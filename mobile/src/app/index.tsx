import { useCallback, useMemo, useState } from "react";
import { FlatList, RefreshControl, StyleSheet, View } from "react-native";
import { Stack } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { ActiveFilterChips } from "@/components/ActiveFilterChips";
import type { ActiveFilter } from "@/components/ActiveFilterChips";
import { ChamberFilter } from "@/components/ChamberFilter";
import { ErrorState } from "@/components/ErrorState";
import { FeedEmptyState } from "@/components/FeedEmptyState";
import { TextFilterInput } from "@/components/TextFilterInput";
import { TradeRow } from "@/components/TradeRow";
import { TradeRowSkeleton } from "@/components/TradeRowSkeleton";
import { Chamber, useTradesFeedQuery } from "@/generated/graphql";
import { useDebouncedValue } from "@/lib/useDebouncedValue";

const PAGE_SIZE = 20;
const INITIAL_SKELETON_ROWS = 8;
const DEBOUNCE_MS = 400;

const CHAMBER_LABEL: Record<Chamber, string> = {
  [Chamber.House]: "House",
  [Chamber.Senate]: "Senate",
};

export default function TradesFeedScreen() {
  const insets = useSafeAreaInsets();
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);

  const [searchInput, setSearchInput] = useState("");
  const [tickerInput, setTickerInput] = useState("");
  const [chamber, setChamber] = useState<Chamber | null>(null);

  const search = useDebouncedValue(searchInput.trim(), DEBOUNCE_MS) || undefined;
  const ticker = useDebouncedValue(tickerInput.trim(), DEBOUNCE_MS) || undefined;

  // search/ticker/chamber are query variables, not a client-side filter --
  // the backend (app/graphql/queries.py Query.trades) does the matching, so
  // every page fetched (including infinite-scroll pages below) is already
  // filtered server-side.
  const { data, loading, error, refetch, fetchMore } = useTradesFeedQuery({
    variables: { search, ticker, chamber: chamber ?? undefined, limit: PAGE_SIZE, offset: 0 },
    notifyOnNetworkStatusChange: true,
  });

  const trades = data?.trades.results ?? [];
  const totalCount = data?.trades.totalCount ?? 0;
  const hasMore = trades.length < totalCount;

  const activeFilters = useMemo<ActiveFilter[]>(() => {
    const filters: ActiveFilter[] = [];
    if (searchInput.trim()) {
      filters.push({ key: "search", label: `"${searchInput.trim()}"`, onDismiss: () => setSearchInput("") });
    }
    if (tickerInput.trim()) {
      filters.push({ key: "ticker", label: tickerInput.trim().toUpperCase(), onDismiss: () => setTickerInput("") });
    }
    if (chamber) {
      filters.push({ key: "chamber", label: CHAMBER_LABEL[chamber], onDismiss: () => setChamber(null) });
    }
    return filters;
  }, [searchInput, tickerInput, chamber]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await refetch({ offset: 0 });
    } catch {
      // Surfaced via `error` above (Apollo sets it on a failed refetch too);
      // caught here only so a failed pull-to-refresh doesn't become an
      // unhandled promise rejection.
    } finally {
      setRefreshing(false);
    }
  }, [refetch]);

  const handleEndReached = useCallback(async () => {
    if (loadingMore || loading || !hasMore) return;
    setLoadingMore(true);
    try {
      await fetchMore({
        variables: { offset: trades.length },
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
    } catch {
      // A failed fetchMore just leaves the list where it was -- the user
      // can scroll to retry. Caught only to avoid an unhandled rejection.
    } finally {
      setLoadingMore(false);
    }
  }, [fetchMore, hasMore, loading, loadingMore, trades.length]);

  const handleRetry = useCallback(() => {
    refetch().catch(() => {
      // Surfaced via `error` above; swallow so this fire-and-forget retry
      // doesn't produce an unhandled promise rejection.
    });
  }, [refetch]);

  return (
    <View style={styles.container}>
      <Stack.Screen options={{ title: "Trades" }} />

      <View style={styles.filterBar}>
        <TextFilterInput value={searchInput} onChangeText={setSearchInput} placeholder="Search politician, ticker, asset..." />
        <View style={styles.filterRow}>
          <TextFilterInput value={tickerInput} onChangeText={setTickerInput} placeholder="Ticker" style={styles.tickerInput} />
          <ChamberFilter value={chamber} onChange={setChamber} />
        </View>
      </View>
      <ActiveFilterChips filters={activeFilters} />

      {error && !data ? (
        <ErrorState title="Could not load trades" message={error.message} onRetry={handleRetry} />
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
  filterBar: {
    paddingHorizontal: 16,
    paddingTop: 12,
    gap: 8,
  },
  filterRow: {
    flexDirection: "row",
    gap: 8,
    alignItems: "center",
  },
  tickerInput: {
    width: 110,
  },
  listContent: {
    flexGrow: 1,
  },
});
