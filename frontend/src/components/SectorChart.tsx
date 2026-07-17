"use client";

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";

const COLORS = [
  "#3b82f6",
  "#ef4444",
  "#10b981",
  "#f59e0b",
  "#8b5cf6",
  "#ec4899",
  "#14b8a6",
  "#f97316",
  "#6366f1",
  "#84cc16",
  "#06b6d4",
];

export default function SectorChart({ sectorBreakdown }: { sectorBreakdown: Record<string, number> }) {
  const data = Object.entries(sectorBreakdown)
    .map(([sector, amount]) => ({ sector, amount }))
    .sort((a, b) => b.amount - a.amount);

  if (data.length === 0) {
    return <p className="text-sm text-gray-400">No sector data available.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie
          data={data}
          dataKey="amount"
          nameKey="sector"
          outerRadius={100}
          label={(props) => (props as unknown as { sector: string }).sector}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip formatter={(value) => `$${Number(value).toLocaleString()}`} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
