# Pokemon TCG Market Tracker

Local app for analyzing Pokemon TCG singles and sealed product trends to make evidence-based buy/sell decisions. Runs entirely on your machine with free data sources.

## Setup

```bash
cd pokemon-tcg-tracker
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Required for best results:** Get a free API key from [dev.pokemontcg.io](https://dev.pokemontcg.io/) (20k/day vs 1k without). Create `.env` in the project root:

```
POKEMON_TCG_API_KEY=your_key_here
```

Run with `--debug` to verify the key is loaded. The API can be slow (30–60s per request); the fetcher retries on timeout.

## Watchlist

Edit `config/watchlist.json`:

- **card_ids**: Exact IDs from [pokemontcg.io](https://pokemontcg.io/) (e.g. `swsh4-25` = Vivid Voltage Charizard)
- **card_names**: Fallback search by name (e.g. `Flareon V`, `Jolteon VMAX`). Uses search API when IDs 404.

## Run

**One-time fetch:**

```bash
python scripts/run_fetch.py
```

**Seed sample data (when fetch fails):**

```bash
python scripts/seed_data.py
```
Adds 7 sample cards (Charizard + Eeveelutions) with 30 days of fake price history for frontend development.

**API server (for frontend):**

```bash
python scripts/run_api.py
```

Serves at http://localhost:8000. Docs at http://localhost:8000/docs.

**Endpoints:**
- `GET /api/watchlist` – card IDs in your watchlist
- `GET /api/cards` – all cards with latest prices
- `GET /api/cards/{card_id}` – single card + latest price
- `GET /api/prices/{card_id}` – price history (optional: `?variant=`, `?source=`, `?days=`)

**Scheduled (every 30 min) via cron:**

```bash
crontab -e
# Add:
*/30 * * * * cd /path/to/pokemon-tcg-tracker && .venv/bin/python scripts/run_fetch.py
```

Or run manually when your machine is on.

## Data

- **Source:** pokemontcg.io (TCGPlayer + CardMarket prices)
- **Storage:** SQLite at `data/tcg_tracker.db`
- **Tables:** `cards` (catalog), `price_snapshots` (history by variant/source)

## Roadmap

- [ ] PSA population scraper
- [ ] PriceCharting scraper (graded + sealed)
- [ ] TCGPlayer sealed scraper
- [ ] Trend analytics (7d/30d/90d, rising/declining)
- [ ] CLI or simple UI for decisions

## License

Personal use. Not financial advice.
