"""Fetch card data and prices from TCGdex (primary) or pokemontcg.io (fallback)."""
import time
from datetime import date
from typing import Optional
from pathlib import Path

import requests

from config.settings import (
    POKEMON_TCG_API_KEY,
    POKEMON_TCG_BASE_URL,
    REQUEST_DELAY_SECONDS,
    TCGDEX_BASE_URL,
)
from src.db import get_session, init_db
from src.models import Card, PriceSnapshot


def _normalize_tcgdex_to_internal(tcgdex: dict) -> dict:
    """Convert TCGdex response to our internal format (compatible with save_card_prices)."""
    set_info = tcgdex.get("set", {}) or {}
    pricing = tcgdex.get("pricing", {}) or {}

    # TCGPlayer: TCGdex uses lowPrice, midPrice, etc; we use low, mid, directLow
    tcg = pricing.get("tcgplayer", {}) or {}
    tcg_prices = {}
    for variant, p in tcg.items():
        if variant in ("updated", "unit") or not isinstance(p, dict):
            continue
        tcg_prices[variant] = {
            "low": p.get("lowPrice"),
            "mid": p.get("midPrice"),
            "high": p.get("highPrice"),
            "market": p.get("marketPrice"),
            "directLow": p.get("directLowPrice"),
        }
    # CardMarket: TCGdex uses avg, low, trend, avg1, avg7, avg30
    cm = pricing.get("cardmarket", {}) or {}
    cm_prices = {
        "lowPrice": cm.get("low"),
        "trendPrice": cm.get("trend"),
        "averageSellPrice": cm.get("avg"),
        "avg1": cm.get("avg1"),
        "avg7": cm.get("avg7"),
        "avg30": cm.get("avg30"),
    } if cm else {}

    return {
        "id": tcgdex.get("id", ""),
        "name": tcgdex.get("name", ""),
        "set": {"id": set_info.get("id", ""), "name": set_info.get("name", "")},
        "number": str(tcgdex.get("localId", "")),
        "rarity": tcgdex.get("rarity", ""),
        "supertype": "Pokémon" if tcgdex.get("category") == "Pokemon" else tcgdex.get("category", ""),
        "image": tcgdex.get("image") or "",
        "tcgplayer": {"prices": tcg_prices} if tcg_prices else {},
        "cardmarket": {"prices": cm_prices} if cm_prices else {},
    }


def fetch_card_tcgdex(card_id: str, debug: bool = False) -> Optional[dict]:
    """Fetch card from TCGdex (free, no API key, usually works). Returns normalized dict or None."""
    url = f"{TCGDEX_BASE_URL}/cards/{card_id}"
    try:
        r = requests.get(url, timeout=15)
        if debug:
            print(f"  {card_id} [TCGdex]: status={r.status_code}", end="")
        if r.status_code != 200:
            if debug:
                print()
            return None
        data = r.json()
        if not data.get("pricing"):
            if debug:
                print(" -> no pricing")
            return None
        normalized = _normalize_tcgdex_to_internal(data)
        if debug:
            print(" -> OK")
        return {"data": normalized}
    except requests.exceptions.RequestException as e:
        if debug:
            print(f"  {card_id} [TCGdex]: ERROR - {e}")
        return None


def fetch_card(card_id: str, debug: bool = False, max_retries: int = 2) -> Optional[dict]:
    """Fetch a single card by ID. Returns full API response or None on error. Retries on timeout."""
    url = f"{POKEMON_TCG_BASE_URL}/cards/{card_id}"
    headers = {}
    if POKEMON_TCG_API_KEY:
        headers["X-Api-Key"] = POKEMON_TCG_API_KEY

    for attempt in range(max_retries + 1):
        try:
            r = requests.get(url, headers=headers, timeout=45)
            if debug:
                print(f"  {card_id}: status={r.status_code}", end="")
            if r.status_code != 200:
                if debug:
                    body = r.text[:200] if r.text else ""
                    print(f" -> {body}")
                return None
            data = r.json()
            if debug:
                print(" -> OK")
            return data
        except requests.exceptions.Timeout as e:
            if debug:
                print(f"  {card_id}: TIMEOUT (attempt {attempt + 1}/{max_retries + 1})", end="")
            if attempt < max_retries:
                time.sleep(2 * (attempt + 1))
            else:
                if debug:
                    print(f" - giving up")
                return None
        except requests.exceptions.RequestException as e:
            if debug:
                print(f"  {card_id}: ERROR - {e}")
            return None
    return None


def fetch_card_by_search_tcgdex(name: str, debug: bool = False) -> Optional[dict]:
    """Search TCGdex by card name, fetch first match with pricing. Returns normalized dict or None."""
    url = f"{TCGDEX_BASE_URL}/cards"
    try:
        r = requests.get(url, params={"name": f"eq:{name}"}, timeout=15)
        if r.status_code != 200:
            return None
        results = r.json()
        if not results or not isinstance(results, list):
            return None
        card_id = results[0].get("id")
        if not card_id:
            return None
        return fetch_card_tcgdex(card_id, debug=debug)
    except Exception:
        return None


def fetch_card_by_search(name: str, set_name: Optional[str] = None, debug: bool = False) -> Optional[dict]:
    """Fallback: search by name when direct ID fails. Returns first matching card or None."""
    url = f"{POKEMON_TCG_BASE_URL}/cards"
    headers = {}
    if POKEMON_TCG_API_KEY:
        headers["X-Api-Key"] = POKEMON_TCG_API_KEY
    q = f'name:"{name}"'
    if set_name:
        q += f" set.name:{set_name}"
    try:
        r = requests.get(url, params={"q": q, "pageSize": 3}, headers=headers, timeout=45)
        if debug and r.status_code != 200:
            print(f"  search:{name}: status={r.status_code}")
        if r.status_code != 200:
            return None
        data = r.json()
        cards = data.get("data", [])
        if cards and "tcgplayer" in cards[0] and cards[0].get("tcgplayer", {}).get("prices"):
            return {"data": cards[0]}
        if cards:
            return {"data": cards[0]}
        return None
    except Exception:
        return None


def fetch_watchlist(card_ids: list[str], card_names: Optional[list[str]] = None, debug: bool = False) -> list[dict]:
    """Fetch multiple cards with polite delay. Returns list of card data dicts."""
    results = []
    names = card_names or []
    total = card_ids + [f"search:{n}" for n in names]
    if debug:
        print(f"Fetching {len(total)} cards...")
    for i, cid in enumerate(card_ids):
        # Try TCGdex first (free, works); fall back to pokemontcg.io
        data = fetch_card_tcgdex(cid, debug=debug)
        if not data or "data" not in data:
            data = fetch_card(cid, debug=debug)
        if data and "data" in data:
            results.append(data["data"])
        elif debug and (not data or "data" not in data):
            print(f"  {cid}: skipped (no data)")
        if i < len(card_ids) - 1:
            time.sleep(REQUEST_DELAY_SECONDS)
    for i, name in enumerate(names):
        data = fetch_card_by_search_tcgdex(name, debug=debug)
        if not data or "data" not in data:
            data = fetch_card_by_search(name, debug=debug)
        if data and "data" in data:
            results.append(data["data"])
            if debug:
                print(f"  search:{name} -> {data['data']['id']} OK")
        elif debug:
            print(f"  search:{name}: skipped (no data)")
        if i < len(names) - 1:
            time.sleep(REQUEST_DELAY_SECONDS)
    return results


def _upsert_card(session, card_data: dict) -> Card:
    """Insert or update card in catalog."""
    d = card_data
    card = session.query(Card).get(d["id"]) or Card(id=d["id"])
    card.name = d.get("name", "")
    card.set_id = d.get("set", {}).get("id", "")
    card.set_name = d.get("set", {}).get("name", "")
    card.number = d.get("number", "")
    card.rarity = d.get("rarity", "")
    card.supertype = d.get("supertype", "")
    img = d.get("image") or (d.get("images") or {}).get("large") or (d.get("images") or {}).get("small")
    card.image_url = img or None
    card.updated_at = date.today()
    session.merge(card)
    return card


def _parse_tcgplayer_prices(prices: dict, source: str = "tcgplayer") -> list[dict]:
    """Extract price rows per variant from tcgplayer hash (pokemontcg or TCGdex normalized)."""
    rows = []
    if not prices:
        return rows
    today = date.today()
    for variant, p in prices.items():
        if not isinstance(p, dict):
            continue
        rows.append({
            "variant": variant,
            "source": source,
            "snapshot_date": today,
            "low": p.get("low") or p.get("lowPrice"),
            "mid": p.get("mid") or p.get("midPrice"),
            "high": p.get("high") or p.get("highPrice"),
            "market": p.get("market") or p.get("marketPrice"),
            "direct_low": p.get("direct_low") or p.get("directLow") or p.get("directLowPrice"),
            "avg_1": None,
            "avg_7": None,
            "avg_30": None,
        })
    return rows


def _parse_cardmarket_prices(prices: dict) -> list[dict]:
    """Extract price rows from cardmarket hash (EU, has avg1/7/30). Handles pokemontcg and TCGdex formats."""
    rows = []
    if not prices:
        return rows
    today = date.today()
    rows.append({
        "variant": "normal",
        "source": "cardmarket",
        "snapshot_date": today,
        "low": prices.get("lowPrice") or prices.get("low"),
        "mid": None,
        "high": None,
        "market": prices.get("trendPrice") or prices.get("averageSellPrice") or prices.get("trend") or prices.get("avg"),
        "direct_low": prices.get("lowPriceExPlus"),
        "avg_1": prices.get("avg1"),
        "avg_7": prices.get("avg7"),
        "avg_30": prices.get("avg30"),
    })
    return rows


def save_card_prices(card_id: str, card_data: dict) -> int:
    """Persist card catalog + price snapshots. Returns count of price rows saved."""
    session = get_session()
    try:
        _upsert_card(session, card_data)

        rows_saved = 0
        today = date.today()

        # TCGPlayer prices
        tcg = card_data.get("tcgplayer", {}) or {}
        prices_tcg = tcg.get("prices", {})
        for r in _parse_tcgplayer_prices(prices_tcg, "tcgplayer"):
            session.query(PriceSnapshot).filter(
                PriceSnapshot.card_id == card_id,
                PriceSnapshot.snapshot_date == today,
                PriceSnapshot.variant == r["variant"],
                PriceSnapshot.source == r["source"],
            ).delete()
            snap = PriceSnapshot(
                card_id=card_id,
                snapshot_date=r["snapshot_date"],
                variant=r["variant"],
                source=r["source"],
                low=r["low"],
                mid=r["mid"],
                high=r["high"],
                market=r["market"],
                direct_low=r["direct_low"],
                avg_1=r["avg_1"],
                avg_7=r["avg_7"],
                avg_30=r["avg_30"],
            )
            session.add(snap)
            rows_saved += 1

        # CardMarket prices
        cm = card_data.get("cardmarket", {}) or {}
        prices_cm = cm.get("prices", {})
        for r in _parse_cardmarket_prices(prices_cm):
            session.query(PriceSnapshot).filter(
                PriceSnapshot.card_id == card_id,
                PriceSnapshot.snapshot_date == today,
                PriceSnapshot.variant == r["variant"],
                PriceSnapshot.source == r["source"],
            ).delete()
            snap = PriceSnapshot(
                card_id=card_id,
                snapshot_date=r["snapshot_date"],
                variant=r["variant"],
                source=r["source"],
                low=r["low"],
                mid=r["mid"],
                high=r["high"],
                market=r["market"],
                direct_low=r["direct_low"],
                avg_1=r["avg_1"],
                avg_7=r["avg_7"],
                avg_30=r["avg_30"],
            )
            session.add(snap)
            rows_saved += 1

        session.commit()
        return rows_saved
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def run_fetch(watchlist_path: Optional[Path] = None, debug: bool = False) -> int:
    """
    Load watchlist, fetch all cards, save to DB.
    Returns number of cards processed.
    """
    import json

    base = Path(__file__).resolve().parent.parent
    path = watchlist_path or base / "config" / "watchlist.json"
    if not path.exists():
        example = path.parent / "watchlist.example.json"
        raise FileNotFoundError(
            f"No watchlist at {path}. Copy {example} to watchlist.json and add card IDs."
        )

    with open(path) as f:
        data = json.load(f)
    card_ids = data.get("card_ids", [])[:200]
    card_names = data.get("card_names", [])  # Fallback: search by name when IDs 404

    init_db()
    if debug:
        from config.settings import POKEMON_TCG_API_KEY
        print(f"API key: {'set' if POKEMON_TCG_API_KEY else 'MISSING (add to .env)'}")
        print(f"Watchlist IDs: {card_ids}")
        if card_names:
            print(f"Watchlist names (search fallback): {card_names}")
    cards = fetch_watchlist(card_ids, card_names=card_names, debug=debug)
    saved = 0
    for c in cards:
        save_card_prices(c["id"], c)
        saved += 1
    return saved
