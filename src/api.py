"""FastAPI server that reads from the SQLite DB."""
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.db import get_session, init_db
from src.models import Card, PriceSnapshot
from src.fetcher import run_fetch

app = FastAPI(
    title="Pokemon TCG Tracker API",
    description="Evidence-based buy/sell data for Pokemon TCG singles and sealed.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


WATCHLIST_PATH = Path(__file__).resolve().parent.parent / "config" / "watchlist.json"
WATCHLIST_MAX = 200


def _load_watchlist_full() -> dict:
    if not WATCHLIST_PATH.exists():
        return {"card_ids": [], "card_names": []}
    with open(WATCHLIST_PATH) as f:
        return json.load(f)


def _save_watchlist(data: dict) -> None:
    WATCHLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(WATCHLIST_PATH, "w") as f:
        json.dump(data, f, indent=2)


@app.get("/")
def root():
    """Health check."""
    return {"status": "ok", "service": "pokemon-tcg-tracker"}


@app.post("/api/refresh")
def refresh_prices():
    """Fetch latest prices from TCGdex and save to DB. Call periodically (e.g. daily) to update data."""
    try:
        n = run_fetch(debug=False)
        return {"status": "ok", "cards_updated": n}
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/watchlist")
def get_watchlist():
    """Return watchlist card IDs and card names."""
    data = _load_watchlist_full()
    return {"card_ids": data.get("card_ids", []), "card_names": data.get("card_names", [])}


class AddToWatchlist(BaseModel):
    card_id: Optional[str] = None
    card_name: Optional[str] = None


@app.post("/api/watchlist")
def add_to_watchlist(body: AddToWatchlist):
    """Add a card to the watchlist by ID or name. Limit 200 total items."""
    if body.card_id and body.card_name:
        raise HTTPException(status_code=400, detail="Provide card_id OR card_name, not both")
    if not body.card_id and not body.card_name:
        raise HTTPException(status_code=400, detail="Provide card_id or card_name")
    data = _load_watchlist_full()
    ids = data.get("card_ids", [])
    names = data.get("card_names", [])
    if body.card_id:
        if body.card_id in ids:
            return {"status": "ok", "message": "Already in watchlist", "card_id": body.card_id}
        if len(ids) + len(names) >= WATCHLIST_MAX:
            raise HTTPException(status_code=400, detail=f"Watchlist full ({WATCHLIST_MAX} max)")
        ids.append(body.card_id)
        data["card_ids"] = ids
    else:
        if body.card_name in names:
            return {"status": "ok", "message": "Already in watchlist", "card_name": body.card_name}
        if len(ids) + len(names) >= WATCHLIST_MAX:
            raise HTTPException(status_code=400, detail=f"Watchlist full ({WATCHLIST_MAX} max)")
        names.append(body.card_name)
        data["card_names"] = names
    _save_watchlist(data)
    return {"status": "ok", "card_id": body.card_id, "card_name": body.card_name}


@app.delete("/api/watchlist")
def remove_from_watchlist(card_id: Optional[str] = None, card_name: Optional[str] = None):
    """Remove a card from the watchlist by ID or name."""
    if card_id and card_name:
        raise HTTPException(status_code=400, detail="Provide card_id OR card_name, not both")
    if not card_id and not card_name:
        raise HTTPException(status_code=400, detail="Provide card_id or card_name")
    data = _load_watchlist_full()
    ids = data.get("card_ids", [])
    names = data.get("card_names", [])
    if card_id:
        if card_id not in ids:
            raise HTTPException(status_code=404, detail="Card ID not in watchlist")
        data["card_ids"] = [x for x in ids if x != card_id]
    else:
        if card_name in names:
            data["card_names"] = [x for x in names if x != card_name]
        else:
            # Fallback: card may have been added by ID; look up by name in DB
            init_db()
            session = get_session()
            try:
                card = session.query(Card).filter(Card.name == card_name).first()
                if card and card.id in ids:
                    data["card_ids"] = [x for x in ids if x != card.id]
                else:
                    raise HTTPException(status_code=404, detail="Card name not in watchlist")
            finally:
                session.close()
    _save_watchlist(data)
    return {"status": "ok"}


@app.get("/api/cards")
def get_cards():
    """List all cards in the catalog with latest prices."""
    init_db()
    session = get_session()
    try:
        cards = session.query(Card).all()
        result = []
        for c in cards:
            latest = (
                session.query(PriceSnapshot)
                .filter(PriceSnapshot.card_id == c.id)
                .order_by(PriceSnapshot.snapshot_date.desc())
                .first()
            )
            prices = None
            if latest:
                prices = {
                    "variant": latest.variant,
                    "source": latest.source,
                    "date": latest.snapshot_date.isoformat() if latest.snapshot_date else None,
                    "market": latest.market,
                    "low": latest.low,
                    "mid": latest.mid,
                    "high": latest.high,
                }
            result.append(
                {
                    "id": c.id,
                    "name": c.name,
                    "set_id": c.set_id,
                    "set_name": c.set_name,
                    "number": c.number,
                    "rarity": c.rarity,
                    "supertype": c.supertype,
                    "image_url": c.image_url,
                    "latest_price": prices,
                }
            )
        return {"cards": result}
    finally:
        session.close()


@app.get("/api/cards/{card_id}")
def get_card(card_id: str):
    """Get a single card with latest price."""
    init_db()
    session = get_session()
    try:
        card = session.query(Card).filter(Card.id == card_id).first()
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")

        latest = (
            session.query(PriceSnapshot)
            .filter(PriceSnapshot.card_id == card_id)
            .order_by(PriceSnapshot.snapshot_date.desc())
            .first()
        )
        prices = None
        if latest:
            prices = {
                "variant": latest.variant,
                "source": latest.source,
                "date": latest.snapshot_date.isoformat() if latest.snapshot_date else None,
                "market": latest.market,
                "low": latest.low,
                "mid": latest.mid,
                "high": latest.high,
            }

        return {
            "id": card.id,
            "name": card.name,
            "set_id": card.set_id,
            "set_name": card.set_name,
            "number": card.number,
            "rarity": card.rarity,
            "supertype": card.supertype,
            "image_url": card.image_url,
            "latest_price": prices,
        }
    finally:
        session.close()


@app.get("/api/prices/{card_id}")
def get_prices(
    card_id: str,
    variant: Optional[str] = None,
    source: Optional[str] = None,
    days: Optional[int] = None,
):
    """Get price history for a card. Optional filters: variant, source, days (max history)."""
    init_db()
    session = get_session()
    try:
        q = session.query(PriceSnapshot).filter(PriceSnapshot.card_id == card_id)
        if variant:
            q = q.filter(PriceSnapshot.variant == variant)
        if source:
            q = q.filter(PriceSnapshot.source == source)
        if days:
            cutoff = date.today() - timedelta(days=days)
            q = q.filter(PriceSnapshot.snapshot_date >= cutoff)
        snapshots = q.order_by(PriceSnapshot.snapshot_date.asc()).all()

        result = [
            {
                "date": s.snapshot_date.isoformat() if s.snapshot_date else None,
                "variant": s.variant,
                "source": s.source,
                "market": s.market,
                "low": s.low,
                "mid": s.mid,
                "high": s.high,
                "avg_7": s.avg_7,
                "avg_30": s.avg_30,
            }
            for s in snapshots
        ]
        return {"card_id": card_id, "prices": result}
    finally:
        session.close()
