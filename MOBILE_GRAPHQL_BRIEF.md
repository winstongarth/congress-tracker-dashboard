# Task Brief: GraphQL Layer + React Native Client

**Context for Claude Code:** This is an existing full-stack project — Python/FastAPI backend, Next.js frontend, PostgreSQL — that scrapes US House and Senate financial disclosures, maps disclosed assets to tickers, and computes performance and overlap metrics.

**Goal:** Add (a) a GraphQL aggregation layer over the existing FastAPI backend and (b) a React Native (Expo, TypeScript) mobile client that consumes it. The existing REST API and Next.js frontend must keep working unchanged.

**How to work through this:** Complete one phase at a time. Stop at the end of each phase, summarise what changed, and wait for review before continuing. Do not scaffold later phases early.

---

## Phase 0 — Discovery (no code changes)

Before writing anything, read the repo and report back:

1. Backend layout — where FastAPI app/routers/dependencies live, how the app instance is created, how DB sessions are provided.
2. Data models — SQLAlchemy models (or equivalent) and Pydantic schemas for politicians/members, trades/transactions, tickers, and any performance or overlap metrics. List field names and types exactly as they are.
3. Where performance and overlap metrics are computed — service layer, ORM query, or inline in a route? Note whether they are precomputed/stored or calculated on request.
4. Existing REST endpoints — path, method, params, response shape.
5. Dependency management — requirements.txt, pyproject/poetry, or something else. Python version.
6. Whether a monorepo structure already exists, and where a new `mobile/` directory would sit most naturally.
7. Any existing tests and how they are run.

Then propose (do not implement) the GraphQL schema in SDL, mapped to the real field names found above. Flag anything in the current data model that will make a nested `politician -> trades -> performance` query awkward or N+1-prone.

**Output:** a written summary plus proposed SDL. No file changes.

---

## Phase 1 — GraphQL layer on the FastAPI backend

Use **Strawberry GraphQL** (integrates cleanly with FastAPI and type hints).

Requirements:

- Mount the GraphQL router at `/graphql`, alongside — not replacing — existing REST routes.
- Define types derived from the real models found in Phase 0. Do not invent fields.
- Queries to support:
  - `politicians(search: String, chamber: Chamber, limit: Int, offset: Int): PoliticianConnection`
  - `politician(id: ID!): Politician` — with nested `trades` and a computed `performance` field
  - `trades(ticker: String, politicianId: ID, from: Date, to: Date, limit: Int, offset: Int): TradeConnection`
- Reuse the existing service/query layer for metrics. If metrics are currently computed inline in a route handler, extract them into a service function that both REST and GraphQL call — do not duplicate the logic.
- Solve N+1 explicitly: use DataLoader for `politician -> trades` and `trade -> ticker`. Note in comments where batching happens.
- Pagination: offset/limit with a `totalCount` on connection types. Keep it simple; do not build Relay cursor spec.
- Enable GraphiQL in development only, gated on an env/debug flag.
- CORS: allow the Expo dev client origin in development config.

Also add:
- A `mobile-dev` convenience note in the backend README explaining how to reach `/graphql` from a physical phone on the same LAN (host binding `0.0.0.0`, LAN IP rather than `localhost`).
- Tests for each query, including one asserting DataLoader prevents N+1 (assert query count).

**Constraint:** zero changes to existing REST response shapes. Run the existing test suite and confirm it still passes.

---

## Phase 2 — Expo app scaffold

Create `mobile/` — Expo managed workflow, TypeScript, Expo Router.

- Apollo Client configured against the GraphQL endpoint, with the base URL read from an env var (`EXPO_PUBLIC_API_URL`) and a documented `.env.example`.
- GraphQL Code Generator wired up to produce typed hooks from the backend schema. Add a `codegen` npm script. No hand-written `any` types for query results.
- Add a `mobile/README.md` covering install, env setup, and running on a physical device via Expo Go.
- Verify by rendering a single screen that fetches `trades(limit: 5)` and displays raw JSON. Nothing more in this phase — the point is proving the pipeline end to end.

---

## Phase 3 — Trades feed screen

- `FlatList` of recent disclosures: politician name, ticker, transaction type, amount range, disclosure date.
- Pull-to-refresh via Apollo `refetch`.
- Infinite scroll using `fetchMore` with the offset pagination from Phase 1.
- Explicit loading (skeleton rows, not a bare spinner), empty, and error states. Error state must offer a retry.
- Buy/sell visually distinguishable without relying on colour alone.
- Respect safe-area insets. Touch targets at least 44pt.

---

## Phase 4 — Politician detail screen

- Navigate from a feed row into the detail route.
- Single nested GraphQL query fetching politician + trades + performance in one round trip. Add a brief comment explaining that this is the payoff over the REST equivalent.
- Show holdings/positions and a performance chart (`react-native-svg` or `victory-native`).
- Handle the case where a politician has no computed performance data yet.

---

## Phase 5 — Search and filter

- Debounced search bar on the feed, passing `search` as a GraphQL variable.
- Ticker filter, and a chamber filter if the data supports it.
- Show the active filter state clearly and make it dismissable.
- Do not filter client-side — the query variables must do the work.

---

## Phase 6 — Polish

- App icon and splash screen.
- Verify behaviour on a slow/failed network: no infinite spinners, no unhandled promise rejections.
- Root README: add a Mobile section with setup steps and placeholders for screenshots and a screen recording.
- Confirm `npx tsc --noEmit` is clean and lint passes.

---

## Standing constraints

- TypeScript strict mode on. No `any` in application code.
- Do not modify existing REST endpoints, Next.js code, or the scraping pipeline.
- Commit at the end of each phase with a clear message. Do not commit secrets or `.env`.
- If a phase requires a decision not covered here, ask rather than assume.
