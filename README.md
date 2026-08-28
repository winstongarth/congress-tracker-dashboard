# Congress Portfolio Tracker

Tracks stock trading activity of members of Congress, scraped directly from
official public disclosure filings (not paid aggregators).

**Educational/informational only. Not investment advice. Disclosed amounts
are ranges, not exact figures.**

## Status: Phase 1-3 built (ingestion, scoring, dashboard)

What's here:

- `app/scrapers/roster.py` — member roster + bio data via api.congress.gov,
  committee assignments via clerk.house.gov / senate.gov directly (the
  congress.gov API has no committee-roster endpoint).
- `app/scrapers/house_ptr.py` — House Periodic Transaction Report scraper.
  Validated against real filings.
- `app/scrapers/senate_efd.py` — Senate eFD PTR scraper. Validated against
  real filings. **Requires a visible (non-headless) browser window** —
  efdsearch.senate.gov's bot protection blocks every headless client,
  including headless Chromium. A Chrome window will pop up while this runs;
  it needs an active desktop session (won't work on a headless server/CI
  box without a virtual display).
- `app/normalization/ticker_match.py` — asset name → ticker matching against
  NASDAQ Trader's free symbol directory, with a confidence threshold.
- `app/selection/top30.py` — member selection. Default is `all` (every
  active member, both chambers). `manual` (a curated list in
  `config/tracked_members.py`) is still available if you want to scope back
  down; `volume`/`frequency`/`performance` need a full scrape cycle first.
- `app/scoring/` — Phase 2 (CLAUDE.md §7): price backfill via yfinance, then
  performance/conviction/overlap/recency/composite scores, plus the
  committee-relevance and bipartisan-overlap flags. Validated by hand
  against real Pelosi/Gottheimer/Capito trades.
- `app/api/` — FastAPI backend serving `/trades` (sortable/filterable),
  `/members/{id}`, `/tickers/{ticker}`.
- `frontend/` — Next.js + Tailwind + Recharts dashboard (trade table, member
  profile pages with sector breakdown chart, ticker pages).

## Setup

```
python -m venv .venv
.venv/Scripts/activate   # or source .venv/bin/activate on Linux/Mac
pip install -r requirements.txt
playwright install chromium   # needed for Senate eFD scraping (--include-senate)
cp .env.example .env  # fill in CONGRESS_API_KEY (free: https://api.congress.gov/sign-up/)
                       # and DATABASE_URL (Postgres)
```

## Running the pipeline

```
python -m app.cli init-db        # create tables
python -m app.cli roster         # Step 1: roster + committees
python -m app.cli trades         # Step 3: House PTRs for every tracked member
python -m app.cli trades --include-senate   # also Senate (pops up a visible Chrome window)
python -m app.cli normalize      # Step 4: re-run ticker matching + backfill ticker_metadata
python -m app.cli score          # Phase 2: price backfill + every §7 sub-score + composite
python -m app.cli all            # roster -> trades -> normalize -> score
```

Default `selection_method` is `all` — every active member, both chambers
(`config/settings.py`). **`--include-senate` now means ~100 sequential
Senate searches**, each through the visible browser window the Akamai
constraint requires (see "Known limitations" below) — a full run takes a
while and needs the desktop session to stay active throughout. House is
cheap by comparison: the bulk filing index already covers every member in
one download, so tracking everyone instead of a curated list doesn't add
extra requests there, just more PDFs to parse. Switch back to
`selection_method = "manual"` and edit `config/tracked_members.py` if you'd
rather scope down to a curated subset.

Edit `config/settings.py` for every other `[CONFIG]` value from CLAUDE.md
(rate limits, confidence threshold, scoring weights, etc.) — also
overridable via `.env`. Changing the composite weights is logged with a
timestamp to `data/weight_changes.log` so old vs. new rankings stay
comparable (CLAUDE.md §7.6).

## Running tests

```
pip install -r requirements.txt   # brings in pytest
python -m pytest
```

Tests run against an in-memory SQLite database (see `tests/conftest.py`),
not the real Postgres instance in `.env`.

## Running the dashboard

```
# Terminal 1: API (from the project root, with .venv active)
python -m uvicorn app.api.main:app --port 8000

# Terminal 2: frontend
cd frontend
npm install   # first time only
npm run dev
```

Then open http://localhost:3000. Run `python -m app.cli score` again after
any new scrape to refresh the numbers — scores are computed in batch, not
live in the UI (CLAUDE.md §4).

## GraphQL API

Alongside the REST endpoints above, the same FastAPI app serves a GraphQL
aggregation layer at `/graphql` (built with
[Strawberry](https://strawberry.rocks/)), aimed at the `mobile/` React
Native client. It reuses the exact same score/metric lookups as the REST
routes (`app/services/`) rather than recomputing anything, and batches its
`politician -> trades` and `trade -> ticker` lookups with DataLoader to
avoid N+1 queries. See `app/graphql/` for the schema, resolvers, and loaders.

REST stays the source of truth for the Next.js dashboard — GraphQL is
additive, not a replacement.

### Mobile dev: reaching `/graphql` from a physical phone

Expo Go on a physical device can't reach `localhost:8000` — `localhost`
resolves to the phone itself, not your computer. To test against a real
device on the same Wi-Fi network:

1. Bind uvicorn to all interfaces, not just localhost:

   ```
   python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000
   ```

2. Set `DEBUG=true` in `.env` for this session — it enables GraphiQL at
   `/graphql` and relaxes CORS to allow any `http://<lan-ip>:<port>` origin
   (the Expo dev client's Metro bundler runs on a random port). **Never**
   run with `DEBUG=true` in production.
3. Find your computer's LAN IP (`ipconfig` on Windows, look for the
   `192.168.x.x`/`10.x.x.x` address on your Wi-Fi adapter) and point the
   Expo app at it — e.g. `EXPO_PUBLIC_API_URL=http://192.168.1.50:8000` in
   `mobile/.env` (see `mobile/README.md`). Your phone and computer must be
   on the same network, and any firewall prompt for `python.exe`/`uvicorn`
   needs to be allowed on "Private" networks.

## Mobile

An Expo (TypeScript, Expo Router) client in `mobile/`, consuming the
GraphQL API above — not a port of the Next.js dashboard, just the two
screens that make sense as a phone app:

- **Trades feed** — recent disclosures with pull-to-refresh, infinite
  scroll, and server-side search/ticker/chamber filtering (never filtered
  client-side — the GraphQL query variables do the work).
- **Politician detail** — profile, performance rollup, portfolio P&L,
  holdings by sector, a per-trade performance chart, and their full trade
  list, all fetched in one nested GraphQL query.

### Setup

```
cd mobile
npm install
cp .env.example .env   # see mobile/README.md for the LAN-IP note above
npm start
```

Then scan the QR code with Expo Go (see `mobile/README.md` for the full
walkthrough, including running on a physical device).

### Screenshots

<!-- TODO: add screenshots -->
| Trades feed | Search & filter | Politician detail |
| --- | --- | --- |
| _screenshot placeholder_ | _screenshot placeholder_ | _screenshot placeholder_ |

### Screen recording

<!-- TODO: add a screen recording (e.g. a GIF or an mp4 link) showing the
     feed, pull-to-refresh, infinite scroll, filtering, and navigating into
     a politician's detail screen -->

## Dashboard columns

| Column | Meaning |
| --- | --- |
| **Member** | Who filed the trade, with party-state and chamber. Links to that member's profile page. |
| **Ticker / Asset** | The matched ticker (links to that ticker's page) plus the raw asset name as disclosed. "unmatched" means ticker normalization couldn't confidently resolve a ticker (below the confidence threshold, or it's a non-stock asset) — `asset_name_raw` is still shown as-is. |
| **Type** | Buy, Sell, or Exchange, as disclosed. |
| **Txn Date** | The date the actual trade happened. |
| **Disclosed** | The date the member filed the disclosure (the PTR/eFD filing date). |
| **Lag** | Days between Txn Date and Disclosed — how late the disclosure was. The STOCK Act requires filing within 45 days. |
| **Amount** | The disclosed range (these are always ranges, never exact amounts — CLAUDE.md §9). |
| **Performance** | 0-100 percentile rank of the trade's price move (CLAUDE.md §7.1). For a buy, this is the % gain from the transaction date to today (or to a later matching sell, if one was disclosed). For a sell, it's inverted — a sell followed by a price *drop* scores well. Only computed for stock buy/sell trades with a resolved ticker; options/bonds/funds/exchanges show `--`. |
| **Overlap** | 0-100 percentile rank of how many other tracked members bought the same ticker within a 60-day window (§7.4) — the "cluster, not coincidence" signal. Only computed for buys. |
| **Conviction** | 0-100 percentile rank of how many times that member bought that same ticker in the trailing 12 months (§7.2) — repeated small buys score higher than one large one. Only computed for buys. |
| **Composite** | The weighted blend of the above four (Performance/Overlap/Conviction/Recency, weighted 0.35/0.30/0.20/0.15 by default — see `config/settings.py`). For sells, which don't have an Overlap or Conviction value, those two terms default to a neutral 50 rather than 0 (`app/scoring/composite.py`) so a sell isn't unfairly penalized. Recency itself isn't shown as its own column, but it pulls the composite up for more recent trades and decays with a 90-day half-life. |
| **Flags** | **Committee** = the member sits on a committee whose jurisdiction plausibly overlaps the ticker's sector/industry (§7.5, a small hand-maintained mapping in `config/committee_sector_map.py`) — a badge to prompt your own scrutiny, not a numeric score. **Bipartisan** = within that ticker's 60-day overlap window, at least one Democrat and one Republican both bought (§7.4) — a stronger, less partisan-driven clustering signal. |

All scores are recomputed in batch by `python -m app.cli score`, not live in the browser — re-run it after every new scrape to see updated numbers.

## Members page

A sortable list of every tracked member (`/members`) with portfolio-level
realized and unrealized P&L (`app/scoring/portfolio.py`):

- **Realized P&L** — dollar gain/loss on positions that were bought *and
  later sold* (FIFO-matched, same member/ticker/owner). Shown with **Realized
  %** (P&L ÷ cost basis of those closed positions).
- **Unrealized P&L** — mark-to-market gain/loss on positions still held
  (bought, no later matching sell), using the latest available price.
  Shown with **Unrealized %**.

Since STOCK Act disclosures give dollar ranges, not share counts, position
size is *implied* — `amount_mid ÷ price on the transaction date` — so these
are estimates, not exact figures, same caveat as everywhere else in this
app. A sell with no earlier matching buy in the data (a pre-existing
holding, most likely) doesn't count toward either number — see "Known
limitations" below.



## License

MIT — see [LICENSE](LICENSE).
