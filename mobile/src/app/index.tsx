import { useCallback, useState } from "react";
import { FlatList, RefreshControl, StyleSheet, View } from "react-native";
import { Stack } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { ErrorState } from "@/components/ErrorState";
import { FeedEmptyState } from "@/components/FeedEmptyState";
import { TradeRow } from "@/components/TradeRow";
import { TradeRowSkeleton } from "@/components/TradeRowSkeleton";
import { useTradesFeedQuery } from "@/generated/graphql";

const PAGE_SIZE = 20;
const INITIAL_SKELETON_ROWS = 8;

export default function TradesFeedScreen() {
  const insets = useSafeAreaInsets();
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);

  const { data, loading, error, refetch, fetchMore } = useTradesFeedQuery({
    variables: { limit: PAGE_SIZE, offset: 0 },
    notifyOnNetworkStatusChange: true,
  });

  const trades = data?.trades.results ?? [];
  const totalCount = data?.trades.totalCount ?? 0;
  const hasMore = trades.length < totalCount;

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await refetch({ limit: PAGE_SIZE, offset: 0 });
    } finally {
      setRefreshing(false);
    }
  }, [refetch]);

  const handleEndReached = useCallback(async () => {
    if (loadingMore || loading || !hasMore) return;
    setLoadingMore(true);
    try {
      await fetchMore({
        variables: { limit: PAGE_SIZE, offset: trades.length },
        updateQuery: (previous, { fetchMoreResult }) => {
          if (!fetchMoreResult) return previous;
          return {
            trades: {
              ...fetchMoreResult.trades,
              results: [...previous.trades.results, ...fetchMoreResult.trades.results],
            },
          };
        },
      });
    } finally {
      setLoadingMore(false);
    }
  }, [fetchMore, hasMore, loading, loadingMore, trades.length]);

  return (
    <View style={styles.container}>
      <Stack.Screen options={{ title: "Trades" }} />

      {error && !data ? (
        <ErrorState title="Could not load trades" message={error.message} onRetry={() => refetch()} />
      ) : loading && !data ? (
        <View>
          {Array.from({ length: INITIAL_SKELETON_ROWS }).map((_, index) => (
            <TradeRowSkeleton key={index} />
          ))}
        </View>
      ) : (
        <FlatList
          data={trades}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => <TradeRow trade={item} />}
          contentContainerStyle={[styles.listContent, { paddingBottom: insets.bottom }]}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />}
          onEndReachedThreshold={0.4}
          onEndReached={handleEndReached}
          ListEmptyComponent={<FeedEmptyState />}
          ListFooterComponent={loadingMore ? <TradeRowSkeleton /> : null}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#FFFFFF",
  },
  listContent: {
    flexGrow: 1,
  },
});
