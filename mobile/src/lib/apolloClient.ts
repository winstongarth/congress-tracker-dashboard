import { ApolloClient, HttpLink, InMemoryCache } from "@apollo/client";

// Expo inlines any env var prefixed EXPO_PUBLIC_ at build time -- see
// .env.example. Falls back to the iOS-simulator/localhost default so a
// missing .env doesn't crash the app outright.
const API_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

const REQUEST_TIMEOUT_MS = 15000;

// Without this, a request against a reachable-but-unresponsive server (a
// dropped connection, a captive Wi-Fi portal, ...) never settles, so
// useQuery's `loading` never flips to false -- an indefinite spinner rather
// than a genuine error state. Aborting after a timeout guarantees every
// request eventually resolves one way or the other.
function fetchWithTimeout(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  return fetch(input, { ...init, signal: controller.signal }).finally(() => clearTimeout(timeout));
}

export const apolloClient = new ApolloClient({
  link: new HttpLink({ uri: `${API_URL}/graphql`, fetch: fetchWithTimeout }),
  cache: new InMemoryCache(),
});
