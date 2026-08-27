import { Pressable, StyleSheet, Text, View } from "react-native";

export function FeedErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Could not load trades</Text>
      <Text style={styles.subtitle}>{message}</Text>
      <Pressable style={styles.button} onPress={onRetry} accessibilityRole="button">
        <Text style={styles.buttonText}>Retry</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 32,
    gap: 8,
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
  button: {
    marginTop: 12,
    minHeight: 44,
    minWidth: 120,
    paddingHorizontal: 20,
    borderRadius: 8,
    backgroundColor: "#1A73E8",
    alignItems: "center",
    justifyContent: "center",
  },
  buttonText: {
    color: "#FFFFFF",
    fontWeight: "700",
  },
});
