import { Pressable, StyleSheet, Text, View } from "react-native";

import { Chamber } from "@/generated/graphql";

const OPTIONS: { label: string; value: Chamber | null }[] = [
  { label: "All", value: null },
  { label: "House", value: Chamber.House },
  { label: "Senate", value: Chamber.Senate },
];

export function ChamberFilter({ value, onChange }: { value: Chamber | null; onChange: (chamber: Chamber | null) => void }) {
  return (
    <View style={styles.container}>
      {OPTIONS.map((option) => {
        const selected = option.value === value;
        return (
          <Pressable
            key={option.label}
            onPress={() => onChange(option.value)}
            style={[styles.option, selected && styles.optionSelected]}
            accessibilityRole="button"
            accessibilityState={{ selected }}
          >
            <Text style={[styles.optionText, selected && styles.optionTextSelected]}>{option.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    flexDirection: "row",
    backgroundColor: "#F1F3F4",
    borderRadius: 10,
    padding: 2,
  },
  option: {
    flex: 1,
    minHeight: 40,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 8,
  },
  optionSelected: {
    backgroundColor: "#FFFFFF",
    shadowColor: "#000",
    shadowOpacity: 0.08,
    shadowRadius: 2,
    shadowOffset: { width: 0, height: 1 },
    elevation: 1,
  },
  optionText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#5F6368",
  },
  optionTextSelected: {
    color: "#1A1A1A",
  },
});
