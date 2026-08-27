import { ApolloProvider } from "@apollo/client";
import { Stack } from "expo-router";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { apolloClient } from "@/lib/apolloClient";

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <ApolloProvider client={apolloClient}>
        <Stack />
      </ApolloProvider>
    </SafeAreaProvider>
  );
}
