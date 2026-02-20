#!/usr/bin/env python3
"""Resolve card names to pokemontcg.io IDs via search API."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import requests
from dotenv import load_dotenv
import os

load_dotenv(ROOT / ".env")
API_KEY = os.getenv("POKEMON_TCG_API_KEY", "")
BASE = "https://api.pokemontcg.io/v2/cards"

SEARCHES = [
    'name:"Flareon V"',
    'name:"Jolteon V"',
    'name:"Vaporeon V"',
    'name:"Flareon VMAX"',
    'name:"Jolteon VMAX"',
    'name:"Vaporeon VMAX"',
]

def main():
    headers = {"X-Api-Key": API_KEY} if API_KEY else {}
    ids = []
    for q in SEARCHES:
        r = requests.get(BASE, params={"q": q, "pageSize": 5}, headers=headers, timeout=30)
        if r.status_code != 200:
            print(f"Search {q}: {r.status_code}", file=sys.stderr)
            continue
        data = r.json()
        cards = data.get("data", [])
        if cards:
            # Prefer Evolving Skies or Promo set
            for c in cards:
                sid = c.get("set", {}).get("id", "")
                if "swsh" in sid or "evolving" in sid.lower():
                    ids.append(c["id"])
                    print(f"{c['name']} -> {c['id']} ({c.get('set',{}).get('name','')})")
                    break
            else:
                ids.append(cards[0]["id"])
                print(f"{cards[0]['name']} -> {cards[0]['id']} ({cards[0].get('set',{}).get('name','')})")
        else:
            print(f"No results for {q}", file=sys.stderr)
    if ids:
        print("\n# Add to watchlist.json:")
        print(json.dumps({"card_ids": ids}, indent=2))

if __name__ == "__main__":
    main()
