import { ScrollView, StyleSheet, Text, View } from "react-native";

import { useTradesQuery } from "@/generated/graphql";

// Phase 2 checkpoint: prove the Expo -> Apollo -> GraphQL -> FastAPI pipeline
// works end to end. Just dumps raw JSON -- the real feed UI is Phase 3.
export default function Index() {
  const { data, loading, error } = useTradesQuery({ variables: { limit: 5 } });

  return (
    <View style={styles.container}>
      <Text style={styles.heading}>trades(limit: 5)</Text>
      {loading && <Text>Loading...</Text>}
      {error && <Text style={styles.error}>{error.message}</Text>}
      {data && (
        <ScrollView style={styles.scroll}>
          <Text style={styles.json}>{JSON.stringify(data, null, 2)}</Text>
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingTop: 60,
    paddingHorizontal: 16,
  },
  heading: {
    fontSize: 18,
    fontWeight: "600",
    marginBottom: 12,
  },
  error: {
    color: "crimson",
  },
  scroll: {
    flex: 1,
  },
  json: {
    fontFamily: "monospace",
    fontSize: 12,
  },
});
