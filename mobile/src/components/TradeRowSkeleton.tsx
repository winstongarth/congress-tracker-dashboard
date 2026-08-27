import { StyleSheet, View } from "react-native";

export function TradeRowSkeleton() {
  return (
    <View style={styles.row}>
      <View style={styles.mainColumn}>
        <View style={[styles.bar, { width: "55%" }]} />
        <View style={[styles.bar, { width: "35%" }]} />
        <View style={[styles.bar, { width: "45%" }]} />
      </View>
      <View style={styles.sideColumn}>
        <View style={[styles.bar, styles.badgeBar]} />
        <View style={[styles.bar, { width: 64 }]} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    minHeight: 44,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: "#E8E8E8",
  },
  mainColumn: {
    flex: 1,
    marginRight: 12,
    gap: 8,
    justifyContent: "center",
  },
  sideColumn: {
    alignItems: "flex-end",
    gap: 8,
    justifyContent: "center",
  },
  bar: {
    height: 10,
    borderRadius: 4,
    backgroundColor: "#E3E3E3",
  },
  badgeBar: {
    width: 60,
    height: 20,
    borderRadius: 6,
  },
});
