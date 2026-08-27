import { StyleSheet, Text, View } from "react-native";

export function FeedEmptyState() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>No trades found</Text>
      <Text style={styles.subtitle}>Check back after the next scrape.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 32,
    gap: 4,
  },
  title: {
    fontSize: 16,
    fontWeight: "600",
  },
  subtitle: {
    fontSize: 13,
    color: "#5F6368",
    textAlign: "center",
  },
});
