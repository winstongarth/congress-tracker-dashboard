import { StyleSheet, Text, View } from "react-native";

import { TransactionType } from "@/generated/graphql";

// Buy/sell/exchange must be distinguishable without relying on colour alone,
// so each badge also carries a distinct glyph and text label. Shared by the
// feed row (Phase 3) and the politician detail holdings list (Phase 4).
const TRANSACTION_BADGE: Record<TransactionType, { label: string; glyph: string; background: string; foreground: string }> = {
  [TransactionType.Buy]: { label: "BUY", glyph: "▲", background: "#E6F4EA", foreground: "#1E7E34" },
  [TransactionType.Sell]: { label: "SELL", glyph: "▼", background: "#FCE8E6", foreground: "#B3261E" },
  [TransactionType.Exchange]: { label: "EXCHANGE", glyph: "◆", background: "#EEEEEE", foreground: "#5F6368" },
};

export function TransactionBadge({ type }: { type: TransactionType }) {
  const badge = TRANSACTION_BADGE[type];
  return (
    <View style={[styles.badge, { backgroundColor: badge.background }]}>
      <Text style={[styles.badgeText, { color: badge.foreground }]}>
        {badge.glyph} {badge.label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  badgeText: {
    fontSize: 12,
    fontWeight: "700",
  },
});
