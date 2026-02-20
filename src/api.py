"""FastAPI server that reads from the SQLite DB."""
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.db import get_session, init_db
from src.models import Card, PriceSnapshot

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


def _load_watchlist() -> list[str]:
    path = Path(__file__).resolve().parent.parent / "config" / "watchlist.json"
    if not path.exists():
        return []
    with open(path) as f:
        data = json.load(f)
    return data.get("card_ids", [])


@app.get("/")
def root():
    """Health check."""
    return {"status": "ok", "service": "pokemon-tcg-tracker"}


@app.get("/api/watchlist")
def get_watchlist():
    """Return watchlist card IDs."""
    return {"card_ids": _load_watchlist()}


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
