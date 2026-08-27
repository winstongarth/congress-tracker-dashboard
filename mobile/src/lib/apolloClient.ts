import { ApolloClient, InMemoryCache } from "@apollo/client";

// Expo inlines any env var prefixed EXPO_PUBLIC_ at build time -- see
// .env.example. Falls back to the iOS-simulator/localhost default so a
// missing .env doesn't crash the app outright.
const API_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

export const apolloClient = new ApolloClient({
  uri: `${API_URL}/graphql`,
  cache: new InMemoryCache(),
});
