# Congress Portfolio Tracker

Tracks stock trading activity of members of Congress, scraped directly from
official public disclosure filings (not paid aggregators).

**Educational/informational only. Not investment advice. Disclosed amounts
are ranges, not exact figures.**

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
