# Congress Portfolio Tracker

Tracks stock trading activity of members of the US Congress, scraped
directly from official public disclosure filings (not paid aggregators),
and scores each trade for how well-timed and how "clustered" it was.

**Educational/personal project only. Not investment advice. Disclosed
amounts are ranges, not exact figures.**

## 1. What this is

Members of Congress are required by the STOCK Act to disclose stock trades
within 45 days. Those disclosures are public, but they're scattered across
PDF filings on two different government sites and give no sense of which
trades were well-timed, clustered with other members, or worth a second
look. This project:

1. Scrapes House and Senate disclosure filings directly from the source
   (`clerk.house.gov`, `efdsearch.senate.gov`), not a third-party feed.
2. Matches disclosed asset names to real stock tickers.
3. Backfills historical prices and computes a set of 0-100 percentile
   scores per trade — **performance** (how the price moved after the
   trade), **conviction** (repeated buying of the same ticker),
   **overlap** (other members buying the same ticker in the same window),
   and **recency** — blended into a single **composite** score, plus
   **committee-relevance** and **bipartisan-overlap** flags.
4. Serves the results over REST and GraphQL, with a web dashboard and a
   mobile app on top.

Three clients ship against the same backend and the same computed scores:
a Next.js web dashboard, an Expo/React Native mobile app, and the raw
REST/GraphQL APIs.

## 2. Architecture

```
                    ┌─────────────────────────┐
                    │   Government sources     │
                    │  clerk.house.gov (PTR)   │
                    │  efdsearch.senate.gov    │
                    │  api.congress.gov        │
                    │  NASDAQ Trader symbols   │
                    │  yfinance (price data)   │
                    └────────────┬─────────────┘
                                 │  scrapers (app/scrapers/)
                                 ▼
                    ┌─────────────────────────┐
                    │   Normalization           │
                    │   asset name -> ticker    │
                    │   (app/normalization/)    │
                    └────────────┬─────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │   PostgreSQL              │
                    │   (SQLAlchemy models,     │
                    │    app/db/models.py)      │
                    └────────────┬─────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │   Scoring engine          │
                    │   (app/scoring/), run in  │
                    │   batch via app/cli.py    │
                    └────────────┬─────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │   FastAPI app             │
                    │   REST  (app/api/)        │
                    │   GraphQL (app/graphql/)  │
                    │   shared service layer    │
                    │   (app/services/)         │
                    └──────┬─────────────┬──────┘
                           │             │
                  REST     │             │  GraphQL
                           ▼             ▼
                  ┌────────────┐  ┌──────────────┐
                  │  Next.js    │  │  Expo / RN    │
                  │  dashboard  │  │  mobile app   │
                  │ (frontend/) │  │  (mobile/)    │
                  └────────────┘  └──────────────┘
```

Key design points:

- **Ingestion and scoring are batch jobs, not live computation.** Scores
  are computed by `python -m app.cli score` and stored in the `scores` /
  `portfolio_returns` tables — the API and both clients just read them.
  Re-run the pipeline after every new scrape to refresh the numbers.
- **REST is the source of truth for response shapes; GraphQL is additive.**
  The GraphQL layer (`app/graphql/`) reuses the exact same score/metric
  lookups as REST (`app/services/`) rather than recomputing anything, and
  batches its `politician -> trades` and `trade -> ticker` lookups with
  DataLoader to avoid N+1 queries. Adding GraphQL made zero changes to the
  existing REST response shapes (enforced by `tests/test_rest_unchanged.py`).
- **A shared fetch layer enforces scraping etiquette** (`app/cache/http_cache.py`):
  every fetched page/PDF is cached by a stable key, rate-limited, and sent
  with an identifying User-Agent.
- **The mobile app is a thin client**, not a port of the dashboard — it
  covers two screens (trades feed, politician detail) chosen because
  they make sense as a phone app, consuming the same GraphQL API.

## 3. Data sources

| Source | What it provides | Notes |
| --- | --- | --- |
| [api.congress.gov](https://api.congress.gov/) | Member roster + bio data | Free API key required |
| [clerk.house.gov](https://clerk.house.gov/) | House committee rosters + Periodic Transaction Reports (PTRs) | Committee data isn't in the congress.gov API, so this is scraped directly |
| [senate.gov](https://www.senate.gov/) | Senate committee rosters | Scraped directly, same reason as above |
| [efdsearch.senate.gov](https://efdsearch.senate.gov/) | Senate eFD Periodic Transaction Reports | Requires accepting a click-wrap agreement and a **visible (non-headless) browser** — its bot protection (Akamai) blocks every headless client, confirmed against httpx, PowerShell, and headless Chromium alike |
| [NASDAQ Trader symbol directory](https://www.nasdaqtrader.com/trader.aspx?id=symboldirdefs) | Ticker + company name reference table | Free, no key, used for fuzzy-matching disclosed asset names to tickers |
| [yfinance](https://pypi.org/project/yfinance/) | Historical daily close prices, sector/industry metadata | Documented single point of failure — kept behind one function (`fetch_ticker_metadata`, `price_backfill.py`) so it can be swapped later |

All scraping goes through a shared caching/rate-limiting layer
(`app/cache/http_cache.py`) rather than hitting these sites directly from
each scraper.

## 4. Tech stack

**Backend**
- Python, FastAPI, Uvicorn
- SQLAlchemy 2.0 + PostgreSQL
- [Strawberry GraphQL](https://strawberry.rocks/) (FastAPI integration, DataLoader-based batching)
- Pydantic / pydantic-settings for config
- httpx, BeautifulSoup4 + lxml, Playwright (Senate scraping), pdfplumber + pytesseract (PDF/OCR parsing of PTR filings)
- rapidfuzz (ticker/company name fuzzy matching)
- yfinance (price history + sector metadata)
- pytest (in-memory SQLite for tests — see `tests/conftest.py`)

**Web dashboard** (`frontend/`)
- Next.js, React, TypeScript
- Tailwind CSS
- Recharts (sector breakdown chart)

**Mobile app** (`mobile/`)
- Expo (managed workflow), React Native, TypeScript, Expo Router
- Apollo Client, with GraphQL Code Generator producing typed hooks from the live schema
- react-native-svg (performance chart)

## 5. Repo structure

```
app/
├── api/            REST endpoints (FastAPI routers): /trades, /members/{id}, /tickers/{ticker}
├── graphql/         GraphQL schema, resolvers, and DataLoaders, mounted at /graphql
├── services/        Shared score/metric lookups used by both REST and GraphQL
├── db/              SQLAlchemy models + session management
├── scrapers/        House/Senate/committee/roster scrapers
├── normalization/   Asset name -> ticker matching
├── scoring/         Price backfill + performance/conviction/overlap/recency/composite scoring, portfolio P&L
├── selection/       Member selection strategies (all / manual / volume / frequency / performance)
├── cache/           Shared rate-limited, caching fetch layer
└── cli.py           Pipeline entry points (roster, trades, normalize, score, all)

config/
├── settings.py               Central config (env-overridable)
├── tracked_members.py        Manual member list (used when selection_method = "manual")
└── committee_sector_map.py   Committee -> sector/industry keyword mapping

frontend/            Next.js dashboard (trade table, member profile pages, ticker pages)
mobile/              Expo/React Native app (trades feed, politician detail)
tests/               Pytest suite (REST, GraphQL, DataLoader N+1 regression)
data/                Local cache + SQLite artifacts (gitignored)
```

## Getting started

### Backend setup

```
python -m venv .venv
.venv/Scripts/activate   # or source .venv/bin/activate on Linux/Mac
pip install -r requirements.txt
playwright install chromium   # needed for Senate eFD scraping (--include-senate)
cp .env.example .env  # fill in CONGRESS_API_KEY (free: https://api.congress.gov/sign-up/)
                       # and DATABASE_URL (Postgres)
```

### Running the pipeline

```
python -m app.cli init-db        # create tables
python -m app.cli roster         # roster + committees
python -m app.cli trades         # House PTRs for every tracked member
python -m app.cli trades --include-senate   # also Senate (pops up a visible Chrome window)
python -m app.cli normalize      # re-run ticker matching + backfill ticker_metadata
python -m app.cli score          # price backfill + every sub-score + composite
python -m app.cli all            # roster -> trades -> normalize -> score
```

Default `selection_method` is `all` — every active member, both chambers
(`config/settings.py`). `--include-senate` means ~100 sequential Senate
searches, each through the visible browser window the Akamai constraint
requires (see "Known limitations" below) — a full run takes a while and
needs the desktop session to stay active throughout. House is cheap by
comparison: the bulk filing index already covers every member in one
download, so tracking everyone instead of a curated list doesn't add extra
requests there, just more PDFs to parse. Switch back to
`selection_method = "manual"` and edit `config/tracked_members.py` if
you'd rather scope down to a curated subset.

Edit `config/settings.py` for every other config value (rate limits,
confidence threshold, scoring weights, etc.) — also overridable via
`.env`. Changing the composite weights is logged with a timestamp to
`data/weight_changes.log` so old vs. new rankings stay comparable.

### Running tests

```
pip install -r requirements.txt   # brings in pytest
python -m pytest
```

Tests run against an in-memory SQLite database (see `tests/conftest.py`),
not the real Postgres instance in `.env`.

### Running the dashboard

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
live in the UI.

### GraphQL API

Alongside the REST endpoints above, the same FastAPI app serves a GraphQL
aggregation layer at `/graphql`. It reuses the exact same score/metric
lookups as the REST routes (`app/services/`) and batches its
`politician -> trades` and `trade -> ticker` lookups with DataLoader to
avoid N+1 queries. See `app/graphql/` for the schema, resolvers, and
loaders.

#### Mobile dev: reaching `/graphql` from a physical phone

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

### Mobile app

```
cd mobile
npm install
cp .env.example .env   # see mobile/README.md for the LAN-IP note above
npm start
```

Then scan the QR code with Expo Go (see `mobile/README.md` for the full
walkthrough, including running on a physical device). Two screens:

- **Trades feed** — recent disclosures with pull-to-refresh, infinite
  scroll, and server-side search/ticker/chamber filtering (never filtered
  client-side — the GraphQL query variables do the work).
- **Politician detail** — profile, performance rollup, portfolio P&L,
  holdings by sector, a per-trade performance chart, and their full trade
  list, all fetched in one nested GraphQL query.

## Dashboard columns

| Column | Meaning |
| --- | --- |
| **Member** | Who filed the trade, with party-state and chamber. Links to that member's profile page. |
| **Ticker / Asset** | The matched ticker (links to that ticker's page) plus the raw asset name as disclosed. "unmatched" means ticker normalization couldn't confidently resolve a ticker (below the confidence threshold, or it's a non-stock asset) — `asset_name_raw` is still shown as-is. |
| **Type** | Buy, Sell, or Exchange, as disclosed. |
| **Txn Date** | The date the actual trade happened. |
| **Disclosed** | The date the member filed the disclosure (the PTR/eFD filing date). |
| **Lag** | Days between Txn Date and Disclosed — how late the disclosure was. The STOCK Act requires filing within 45 days. |
| **Amount** | The disclosed range (these are always ranges, never exact amounts). |
| **Performance** | 0-100 percentile rank of the trade's price move. For a buy, this is the % gain from the transaction date to today (or to a later matching sell, if one was disclosed). For a sell, it's inverted — a sell followed by a price *drop* scores well. Only computed for stock buy/sell trades with a resolved ticker; options/bonds/funds/exchanges show `--`. |
| **Overlap** | 0-100 percentile rank of how many other tracked members bought the same ticker within a 60-day window — the "cluster, not coincidence" signal. Only computed for buys. |
| **Conviction** | 0-100 percentile rank of how many times that member bought that same ticker in the trailing 12 months — repeated small buys score higher than one large one. Only computed for buys. |
| **Composite** | The weighted blend of the above four (Performance/Overlap/Conviction/Recency, weighted 0.35/0.30/0.20/0.15 by default — see `config/settings.py`). For sells, which don't have an Overlap or Conviction value, those two terms default to a neutral 50 rather than 0 (`app/scoring/composite.py`) so a sell isn't unfairly penalized. Recency itself isn't shown as its own column, but it pulls the composite up for more recent trades and decays with a 90-day half-life. |
| **Flags** | **Committee** = the member sits on a committee whose jurisdiction plausibly overlaps the ticker's sector/industry (a small hand-maintained mapping in `config/committee_sector_map.py`) — a badge to prompt your own scrutiny, not a numeric score. **Bipartisan** = within that ticker's 60-day overlap window, at least one Democrat and one Republican both bought — a stronger, less partisan-driven clustering signal. |

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
holding, most likely) doesn't count toward either number.

## Known limitations

- **Senate scraping needs a visible browser and an active desktop
  session.** `efdsearch.senate.gov`'s bot protection blocks every headless
  client, so it won't work unattended on a headless server/CI box without
  a virtual display.
- **Disclosed amounts are ranges, not exact figures**, so P&L, position
  size, and performance scores are all estimates derived from the
  midpoint of the disclosed range.
- **Ticker matching is stocks-only.** Options, bonds, funds, and crypto
  are stored but not fuzzy-matched to a ticker — trades below the
  confidence threshold, or non-stock assets, show as unmatched.
- **Cross-filing amendments aren't linked automatically.** The House
  filing index doesn't say which DocID an amendment supersedes, so both
  the original and the amended filing stay on file rather than being
  merged.
- **Scanned (image-only) filings need OCR**, which is slower and less
  reliable than parsing text-based PDFs directly; they're logged for
  manual review rather than silently skipped.
- This is a **personal, educational project** — read
  `efdsearch.senate.gov`'s terms yourself before relying on this for
  anything beyond that.

## License

MIT — see [LICENSE](LICENSE).
