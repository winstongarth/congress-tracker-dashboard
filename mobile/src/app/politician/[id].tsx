import { ActivityIndicator, FlatList, StyleSheet, Text, View } from "react-native";
import { Stack, useLocalSearchParams } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { ErrorState } from "@/components/ErrorState";
import { PositionRow } from "@/components/PositionRow";
import { SectorBreakdownList } from "@/components/SectorBreakdownList";
import { TradePerformanceChart } from "@/components/TradePerformanceChart";
import { Chamber, usePoliticianDetailQuery } from "@/generated/graphql";
import { formatCurrency } from "@/lib/format";

const TRADES_LIMIT = 50;

export default function PoliticianDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const insets = useSafeAreaInsets();

  // See src/graphql/politician.graphql for why this is one query instead of
  // the two REST calls the equivalent web page would need.
  const { data, loading, error, refetch } = usePoliticianDetailQuery({
    variables: { id, tradesLimit: TRADES_LIMIT, tradesOffset: 0 },
  });

  if (error && !data) {
    return (
      <View style={styles.container}>
        <Stack.Screen options={{ title: "Politician" }} />
        <ErrorState title="Could not load politician" message={error.message} onRetry={() => refetch()} />
      </View>
    );
  }

  if (loading && !data) {
    return (
      <View style={[styles.container, styles.centered]}>
        <Stack.Screen options={{ title: "Politician" }} />
        <ActivityIndicator />
      </View>
    );
  }

  const politician = data?.politician;

  if (!politician) {
    return (
      <View style={[styles.container, styles.centered]}>
        <Stack.Screen options={{ title: "Politician" }} />
        <Text style={styles.sectionTitle}>Politician not found</Text>
      </View>
    );
  }

  const portfolioReturn = politician.portfolioReturn;
  const hasTradePerformance = politician.trades.results.some((trade) => trade.performance != null);

  return (
    <View style={styles.container}>
      <Stack.Screen options={{ title: politician.fullName }} />
      <FlatList
        data={politician.trades.results}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => <PositionRow trade={item} />}
        contentContainerStyle={{ paddingBottom: insets.bottom }}
        ListEmptyComponent={<Text style={styles.emptySection}>No trades on file.</Text>}
        ListHeaderComponent={
          <View>
            <View style={styles.header}>
              <Text style={styles.name}>{politician.fullName}</Text>
              <Text style={styles.subtitle}>
                {politician.party}-{politician.state}
                {politician.district ? `-${politician.district}` : ""} {"·"}{" "}
                {politician.chamber === Chamber.House ? "House" : "Senate"}
              </Text>
            </View>

            <View style={styles.statsRow}>
              <View style={styles.stat}>
                <Text style={styles.statLabel}>Performance</Text>
                <Text style={styles.statValue}>
                  {politician.performance != null ? Math.round(politician.performance) : "-"}
                </Text>
              </View>
              <View style={styles.stat}>
                <Text style={styles.statLabel}>Realized P&L</Text>
                <Text style={styles.statValue}>
                  {portfolioReturn?.realizedPnl != null ? formatCurrency(portfolioReturn.realizedPnl) : "-"}
                </Text>
              </View>
              <View style={styles.stat}>
                <Text style={styles.statLabel}>Unrealized P&L</Text>
                <Text style={styles.statValue}>
                  {portfolioReturn?.unrealizedPnl != null ? formatCurrency(portfolioReturn.unrealizedPnl) : "-"}
                </Text>
              </View>
            </View>

            <Text style={styles.sectionTitle}>Performance by trade</Text>
            {hasTradePerformance ? (
              <TradePerformanceChart trades={politician.trades.results} />
            ) : (
              <Text style={styles.emptySection}>No performance data yet -- run the scoring pipeline.</Text>
            )}

            <Text style={styles.sectionTitle}>Holdings by sector</Text>
            {politician.sectorBreakdown.length > 0 ? (
              <SectorBreakdownList entries={politician.sectorBreakdown} />
            ) : (
              <Text style={styles.emptySection}>No disclosed trades yet.</Text>
            )}

            <Text style={styles.sectionTitle}>Trades ({politician.trades.totalCount})</Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#FFFFFF",
  },
  centered: {
    alignItems: "center",
    justifyContent: "center",
  },
  header: {
    padding: 16,
    gap: 4,
  },
  name: {
    fontSize: 22,
    fontWeight: "700",
  },
  subtitle: {
    fontSize: 14,
    color: "#5F6368",
  },
  statsRow: {
    flexDirection: "row",
    paddingHorizontal: 16,
    paddingBottom: 16,
    gap: 12,
  },
  stat: {
    flex: 1,
    backgroundColor: "#F5F5F5",
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 8,
    alignItems: "center",
    gap: 2,
  },
  statLabel: {
    fontSize: 11,
    color: "#5F6368",
    textAlign: "center",
  },
  statValue: {
    fontSize: 15,
    fontWeight: "700",
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: "700",
    paddingHorizontal: 16,
    paddingTop: 20,
    paddingBottom: 8,
  },
  emptySection: {
    fontSize: 13,
    color: "#5F6368",
    paddingHorizontal: 16,
    paddingBottom: 8,
  },
});
