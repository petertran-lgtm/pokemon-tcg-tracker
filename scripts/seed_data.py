#!/usr/bin/env python3
"""Seed the DB with sample cards and prices for frontend development."""
import sys
from pathlib import Path
from datetime import date, timedelta

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.db import init_db, get_session
from src.models import Card, PriceSnapshot

SEED_CARDS = [
    {"id": "swsh4-25", "name": "Charizard", "set_id": "swsh4", "set_name": "Vivid Voltage", "number": "25", "rarity": "Rare", "supertype": "Pokémon"},
    {"id": "swsh7-169", "name": "Flareon V", "set_id": "swsh7", "set_name": "Evolving Skies", "number": "169", "rarity": "Rare Holo V", "supertype": "Pokémon"},
    {"id": "swsh7-170", "name": "Jolteon V", "set_id": "swsh7", "set_name": "Evolving Skies", "number": "170", "rarity": "Rare Holo V", "supertype": "Pokémon"},
    {"id": "swsh7-171", "name": "Vaporeon V", "set_id": "swsh7", "set_name": "Evolving Skies", "number": "171", "rarity": "Rare Holo V", "supertype": "Pokémon"},
    {"id": "swsh7-18", "name": "Flareon VMAX", "set_id": "swsh7", "set_name": "Evolving Skies", "number": "18", "rarity": "Rare Holo VMAX", "supertype": "Pokémon"},
    {"id": "swsh7-30", "name": "Vaporeon VMAX", "set_id": "swsh7", "set_name": "Evolving Skies", "number": "30", "rarity": "Rare Holo VMAX", "supertype": "Pokémon"},
    {"id": "swsh7-51", "name": "Jolteon VMAX", "set_id": "swsh7", "set_name": "Evolving Skies", "number": "51", "rarity": "Rare Holo VMAX", "supertype": "Pokémon"},
]


def run():
    init_db()
    session = get_session()
    try:
        today = date.today()
        for card_data in SEED_CARDS:
            card = Card(
                id=card_data["id"],
                name=card_data["name"],
                set_id=card_data["set_id"],
                set_name=card_data["set_name"],
                number=card_data["number"],
                rarity=card_data["rarity"],
                supertype=card_data["supertype"],
                updated_at=today,
            )
            session.merge(card)

            # Seed ~30 days of fake price history (market trending slightly up)
            base_price = {"swsh4-25": 2.50, "swsh7-169": 8.00, "swsh7-170": 6.50, "swsh7-171": 7.00,
                          "swsh7-18": 22.00, "swsh7-30": 25.00, "swsh7-51": 18.00}.get(
                card_data["id"], 5.00
            )
            for d in range(30):
                snap_date = today - timedelta(days=d)
                market = round(base_price * (1 + 0.002 * (30 - d)), 2)
                session.query(PriceSnapshot).filter(
                    PriceSnapshot.card_id == card_data["id"],
                    PriceSnapshot.snapshot_date == snap_date,
                    PriceSnapshot.variant == ("holofoil" if "VMAX" in card_data["name"] or "V" in card_data["name"] else "normal"),
                    PriceSnapshot.source == "tcgplayer",
                ).delete()
                snap = PriceSnapshot(
                    card_id=card_data["id"],
                    snapshot_date=snap_date,
                    variant="holofoil" if "VMAX" in card_data["name"] or "V" in card_data["name"] else "normal",
                    source="tcgplayer",
                    low=round(market * 0.85, 2),
                    mid=round(market * 1.0, 2),
                    high=round(market * 1.25, 2),
                    market=market,
                    direct_low=round(market * 0.95, 2),
                )
                session.add(snap)

        session.commit()
        print(f"Seeded {len(SEED_CARDS)} cards with 30 days of price history.")
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


if __name__ == "__main__":
    run()
