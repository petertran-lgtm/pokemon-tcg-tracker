"""App configuration. Load from .env for secrets."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "tcg_tracker.db"

# API
POKEMON_TCG_API_KEY = os.getenv("POKEMON_TCG_API_KEY", "")  # Get free key at dev.pokemontcg.io
POKEMON_TCG_BASE_URL = "https://api.pokemontcg.io/v2"
TCGDEX_BASE_URL = "https://api.tcgdex.net/v2/en"

# Rate limits (pokemontcg.io: 20k/day with key, 1k without)
REQUEST_DELAY_SECONDS = 0.5  # Polite delay between API calls

# Watchlist size
WATCHLIST_MAX = 200
