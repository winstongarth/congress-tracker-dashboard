import { ScrollView, StyleSheet, Text, View } from "react-native";
import Svg, { Line, Rect } from "react-native-svg";

const CHART_HEIGHT = 110;
const BAR_WIDTH = 28;
const COLUMN_GAP = 12;

type PerformanceTrade = { id: string; ticker?: string | null; performance?: number | null };

// Per-trade performance (0-100 percentile, CLAUDE.md Sec 7.1) as a bar chart,
// one bar per scoreable trade, against a dashed median-percentile reference
// line. Caller (politician detail screen) is responsible for the "no
// performance data yet" empty state -- this renders nothing if there's
// nothing scoreable to show.
export function TradePerformanceChart({ trades }: { trades: PerformanceTrade[] }) {
  const scored = trades.filter((trade): trade is PerformanceTrade & { performance: number } => trade.performance != null);

  if (scored.length === 0) {
    return null;
  }

  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.container}>
      {scored.map((trade) => {
        const clamped = Math.max(0, Math.min(100, trade.performance));
        const barHeight = Math.max((clamped / 100) * CHART_HEIGHT, 2);

        return (
          <View key={trade.id} style={styles.column}>
            <Text style={styles.score}>{Math.round(clamped)}</Text>
            <Svg width={BAR_WIDTH} height={CHART_HEIGHT}>
              <Line
                x1={0}
                y1={CHART_HEIGHT / 2}
                x2={BAR_WIDTH}
                y2={CHART_HEIGHT / 2}
                stroke="#D8D8D8"
                strokeWidth={1}
                strokeDasharray="2,2"
              />
              <Rect
                x={4}
                y={CHART_HEIGHT - barHeight}
                width={BAR_WIDTH - 8}
                height={barHeight}
                rx={3}
                fill={clamped >= 50 ? "#1E7E34" : "#B3261E"}
              />
            </Svg>
            <Text style={styles.ticker} numberOfLines={1}>
              {trade.ticker ?? "-"}
            </Text>
          </View>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    gap: COLUMN_GAP,
    alignItems: "flex-end",
  },
  column: {
    alignItems: "center",
    width: BAR_WIDTH + 8,
  },
  score: {
    fontSize: 11,
    color: "#5F6368",
    marginBottom: 4,
  },
  ticker: {
    fontSize: 11,
    color: "#5F6368",
    marginTop: 4,
    maxWidth: BAR_WIDTH + 8,
  },
});
