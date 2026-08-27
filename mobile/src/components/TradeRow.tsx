import { StyleSheet, Text, View } from "react-native";

import { TransactionType } from "@/generated/graphql";
import type { TradesFeedQuery } from "@/generated/graphql";
import { formatAmountRange, formatDisclosureDate } from "@/lib/format";

type FeedTrade = TradesFeedQuery["trades"]["results"][number];

// Buy/sell/exchange must be distinguishable without relying on colour alone,
// so each badge also carries a distinct glyph and text label.
const TRANSACTION_BADGE: Record<TransactionType, { label: string; glyph: string; background: string; foreground: string }> = {
  [TransactionType.Buy]: { label: "BUY", glyph: "▲", background: "#E6F4EA", foreground: "#1E7E34" },
  [TransactionType.Sell]: { label: "SELL", glyph: "▼", background: "#FCE8E6", foreground: "#B3261E" },
  [TransactionType.Exchange]: { label: "EXCHANGE", glyph: "◆", background: "#EEEEEE", foreground: "#5F6368" },
};

export function TradeRow({ trade }: { trade: FeedTrade }) {
  const badge = TRANSACTION_BADGE[trade.transactionType];

  return (
    <View style={styles.row}>
      <View style={styles.mainColumn}>
        <Text style={styles.politician} numberOfLines={1}>
          {trade.politician.fullName}
        </Text>
        <Text style={styles.ticker} numberOfLines={1}>
          {trade.ticker ?? trade.assetNameRaw}
        </Text>
        <Text style={styles.amount}>{formatAmountRange(trade.amountMin, trade.amountMax)}</Text>
      </View>
      <View style={styles.sideColumn}>
        <View style={[styles.badge, { backgroundColor: badge.background }]}>
          <Text style={[styles.badgeText, { color: badge.foreground }]}>
            {badge.glyph} {badge.label}
          </Text>
        </View>
        <Text style={styles.date}>{formatDisclosureDate(trade.disclosureDate)}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    minHeight: 44,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: "#D8D8D8",
  },
  mainColumn: {
    flex: 1,
    marginRight: 12,
    gap: 2,
  },
  politician: {
    fontSize: 15,
    fontWeight: "600",
  },
  ticker: {
    fontSize: 13,
    color: "#5F6368",
  },
  amount: {
    fontSize: 13,
    color: "#5F6368",
  },
  sideColumn: {
    alignItems: "flex-end",
    gap: 6,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  badgeText: {
    fontSize: 12,
    fontWeight: "700",
  },
  date: {
    fontSize: 12,
    color: "#5F6368",
  },
});
