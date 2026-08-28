import { StyleSheet, Text, View } from "react-native";

import { TransactionBadge } from "@/components/TransactionBadge";
import type { PoliticianDetailQuery } from "@/generated/graphql";
import { formatAmountRange, formatDisclosureDate } from "@/lib/format";

type PoliticianTrade = NonNullable<PoliticianDetailQuery["politician"]>["trades"]["results"][number];

// Same information as the feed's TradeRow, minus the politician name -- this
// list already lives on that politician's own screen -- and not tappable,
// since there's nowhere further to navigate to from here yet.
export function PositionRow({ trade }: { trade: PoliticianTrade }) {
  return (
    <View style={styles.row}>
      <View style={styles.mainColumn}>
        <Text style={styles.ticker} numberOfLines={1}>
          {trade.ticker ?? trade.assetNameRaw}
        </Text>
        <Text style={styles.amount}>{formatAmountRange(trade.amountMin, trade.amountMax)}</Text>
      </View>
      <View style={styles.sideColumn}>
        <TransactionBadge type={trade.transactionType} />
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
  ticker: {
    fontSize: 15,
    fontWeight: "600",
  },
  amount: {
    fontSize: 13,
    color: "#5F6368",
  },
  sideColumn: {
    alignItems: "flex-end",
    gap: 6,
  },
  date: {
    fontSize: 12,
    color: "#5F6368",
  },
});
