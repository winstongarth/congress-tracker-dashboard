import { ApolloProvider } from "@apollo/client";
import { Stack } from "expo-router";

import { apolloClient } from "@/lib/apolloClient";

export default function RootLayout() {
  return (
    <ApolloProvider client={apolloClient}>
      <Stack />
    </ApolloProvider>
  );
}
