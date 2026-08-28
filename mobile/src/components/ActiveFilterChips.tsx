import { Pressable, StyleSheet, Text, View } from "react-native";

export type ActiveFilter = {
  key: string;
  label: string;
  onDismiss: () => void;
};

// Makes the current filter state legible at a glance and lets any one of
// them be cleared independently, without resetting the others.
export function ActiveFilterChips({ filters }: { filters: ActiveFilter[] }) {
  if (filters.length === 0) {
    return null;
  }

  return (
    <View style={styles.container}>
      {filters.map((filter) => (
        <Pressable
          key={filter.key}
          onPress={filter.onDismiss}
          style={styles.chip}
          accessibilityRole="button"
          accessibilityLabel={`Remove filter: ${filter.label}`}
        >
          <Text style={styles.chipText} numberOfLines={1}>
            {filter.label}
          </Text>
          <Text style={styles.chipDismiss}>{"×"}</Text>
        </Pressable>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    paddingHorizontal: 16,
    paddingBottom: 8,
  },
  chip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    minHeight: 32,
    paddingLeft: 12,
    paddingRight: 8,
    borderRadius: 16,
    backgroundColor: "#E8F0FE",
  },
  chipText: {
    fontSize: 13,
    color: "#1967D2",
    maxWidth: 160,
  },
  chipDismiss: {
    fontSize: 15,
    color: "#1967D2",
    fontWeight: "700",
  },
});
