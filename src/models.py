"""SQLAlchemy models for cards and price history."""
from datetime import date
from sqlalchemy import Column, Date, Float, Integer, String, UniqueConstraint

from src.db import Base


class Card(Base):
    """Card catalog (identity, set, rarity). One row per card ID."""
    __tablename__ = "cards"

    id = Column(String(64), primary_key=True)  # e.g. swsh4-25
    name = Column(String(128), nullable=False)
    set_id = Column(String(32), nullable=False)
    set_name = Column(String(128))
    number = Column(String(16))
    rarity = Column(String(64))
    supertype = Column(String(32))  # Pokemon, Trainer, Energy
    updated_at = Column(Date)


class PriceSnapshot(Base):
    """Price history. One row per (card, date, variant, source)."""
    __tablename__ = "price_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    card_id = Column(String(64), nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    variant = Column(String(32), nullable=False)  # normal, holofoil, reverseHolofoil, etc.
    source = Column(String(32), nullable=False)  # tcgplayer, cardmarket
    low = Column(Float)
    mid = Column(Float)
    high = Column(Float)
    market = Column(Float)
    direct_low = Column(Float)
    avg_1 = Column(Float)   # CardMarket 1-day avg
    avg_7 = Column(Float)   # CardMarket 7-day avg
    avg_30 = Column(Float)  # CardMarket 30-day avg

    __table_args__ = (
        UniqueConstraint("card_id", "snapshot_date", "variant", "source", name="uq_snapshot"),
    )
