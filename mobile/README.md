# Congress Portfolio Tracker — mobile

Expo (managed workflow) + TypeScript + Expo Router client for the GraphQL
API in `../app/graphql` (see the root [README](../README.md#graphql-api)).
This is a thin client — REST and the Next.js dashboard (`../frontend`) are
untouched and unaffected by anything here.

Currently just a Phase 2 checkpoint screen: it fetches `trades(limit: 5)`
over GraphQL and dumps the raw response as JSON, to prove the Expo → Apollo
Client → `/graphql` → FastAPI pipeline works end to end before building any
real UI (that's Phase 3+).

## Install

```
cd mobile
npm install
cp .env.example .env
```

## Env setup

`.env` needs one variable — see `.env.example` for the exact options:

```
EXPO_PUBLIC_API_URL=http://localhost:8000
```

- Running in the iOS Simulator or an Android Emulator on the same machine as
  the backend: `http://localhost:8000` works as-is.
- Running in Expo Go on a **physical device**: `localhost` on the phone
  means the phone itself, not your computer. Use your computer's LAN IP
  instead (e.g. `http://192.168.1.50:8000`), and see "Mobile dev" in the
  [root README](../README.md#mobile-dev-reaching-graphql-from-a-physical-phone)
  for the backend-side setup (binding to `0.0.0.0`, enabling `DEBUG=true`
  for CORS). Your phone and computer must be on the same Wi-Fi network.

`.env` is gitignored — never commit it.

## Running on a physical device (Expo Go)

1. Make sure the backend is running and reachable from your phone (see
   above).
2. `npm start`
3. Scan the QR code with the Expo Go app (iOS: Camera app; Android: Expo
   Go's built-in scanner).

`npm run android` / `npm run ios` / `npm run web` also work for
simulators/emulators/browser.

## GraphQL Code Generator

`src/generated/graphql.tsx` (typed hooks like `useTradesQuery`) is generated
from the live backend schema plus the `.graphql` operation files under
`src/graphql/`. It's committed, but regenerate it whenever you add/change a
query or the backend schema changes:

```
npm run codegen
```

This introspects `${EXPO_PUBLIC_API_URL}/graphql`, so **the backend must be
running locally** (`python -m uvicorn app.api.main:app --port 8000` from the
repo root) when you run it.

Note: this pins `@apollo/client@3` and the `@graphql-codegen/typescript*`
plugins to their `4.x` line. The `5.x`/`6.x` plugin releases (as of writing)
emit duplicate top-level enum declarations when chained into a single output
file this way — a real bug, not a config issue — so don't bump those without
re-checking `npx tsc --noEmit` first.

## Other scripts

```
npm run typecheck   # tsc --noEmit -- TypeScript strict mode is on, no `any` in app code
npm run lint        # expo lint
```
