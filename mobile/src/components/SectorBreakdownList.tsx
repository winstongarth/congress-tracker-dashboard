import { StyleSheet, Text, View } from "react-native";

import { formatCurrency } from "@/lib/format";

type SectorEntry = { sector: string; amountMid: number };

// The "holdings" view: disclosed dollar amount grouped by sector, as bars
// relative to the largest sector. Same underlying data as the Next.js
// dashboard's per-member sector breakdown chart (frontend/src/components/SectorChart.tsx).
export function SectorBreakdownList({ entries }: { entries: SectorEntry[] }) {
  if (entries.length === 0) {
    return null;
  }

  const sorted = [...entries].sort((a, b) => b.amountMid - a.amountMid);
  const max = sorted[0].amountMid;

  return (
    <View style={styles.container}>
      {sorted.map((entry) => (
        <View key={entry.sector} style={styles.row}>
          <View style={styles.labelRow}>
            <Text style={styles.sector} numberOfLines={1}>
              {entry.sector}
            </Text>
            <Text style={styles.amount}>{formatCurrency(entry.amountMid)}</Text>
          </View>
          <View style={styles.track}>
            <View style={[styles.bar, { width: `${max > 0 ? (entry.amountMid / max) * 100 : 0}%` }]} />
          </View>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    gap: 12,
  },
  row: {
    gap: 4,
  },
  labelRow: {
    flexDirection: "row",
    justifyContent: "space-between",
  },
  sector: {
    fontSize: 13,
    fontWeight: "600",
    flexShrink: 1,
  },
  amount: {
    fontSize: 13,
    color: "#5F6368",
  },
  track: {
    height: 8,
    borderRadius: 4,
    backgroundColor: "#EEEEEE",
    overflow: "hidden",
  },
  bar: {
    height: 8,
    borderRadius: 4,
    backgroundColor: "#1A73E8",
  },
});
