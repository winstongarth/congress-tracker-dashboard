export function fmtDollar(v: number | null): string {
  if (v === null) return "--";
  const sign = v >= 0 ? "+" : "-";
  return `${sign}$${Math.abs(v).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

export function fmtPct(v: number | null): string {
  if (v === null) return "--";
  const sign = v >= 0 ? "+" : "";
  return `${sign}${v.toFixed(1)}%`;
}

export function pnlColor(v: number | null): string {
  if (v === null) return "text-gray-400";
  return v >= 0 ? "text-green-600" : "text-red-600";
}
