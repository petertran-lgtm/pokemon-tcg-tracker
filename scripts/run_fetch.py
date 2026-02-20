#!/usr/bin/env python3
"""Fetch watchlist cards from pokemontcg.io and save prices to DB."""
import sys
from pathlib import Path

# Add project root to path so config and src modules resolve
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.fetcher import run_fetch

if __name__ == "__main__":
    debug = "--debug" in sys.argv or "-d" in sys.argv
    try:
        n = run_fetch(debug=debug)
        print(f"Saved prices for {n} cards.")
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
