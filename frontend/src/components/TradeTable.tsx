import Link from "next/link";
import { TradeOut } from "@/lib/types";

const SORT_COLUMNS: { key: string; label: string }[] = [
  { key: "transaction_date", label: "Txn Date" },
  { key: "disclosure_date", label: "Disclosed" },
  { key: "filing_lag_days", label: "Lag" },
  { key: "amount", label: "Amount" },
  { key: "performance", label: "Performance" },
  { key: "overlap", label: "Overlap" },
  { key: "conviction", label: "Conviction" },
  { key: "composite", label: "Composite" },
];

function fmtAmount(min: number, max: number): string {
  const fmt = (n: number) => `$${n.toLocaleString()}`;
  return min === max ? fmt(min) : `${fmt(min)} - ${fmt(max)}`;
}

function fmtScore(v: number | null): string {
  return v === null ? "--" : v.toFixed(1);
}

export default function TradeTable({
  trades,
  currentSortBy,
  currentSortDir,
  searchParamsString,
}: {
  trades: TradeOut[];
  currentSortBy: string;
  currentSortDir: string;
  searchParamsString: string;
}) {
  const sortHref = (column: string) => {
    const params = new URLSearchParams(searchParamsString);
    const nextDir = currentSortBy === column && currentSortDir === "desc" ? "asc" : "desc";
    params.set("sort_by", column);
    params.set("sort_dir", nextDir);
    return `?${params.toString()}`;
  };

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
          <tr>
            <th className="px-3 py-2">Member</th>
            <th className="px-3 py-2">Ticker / Asset</th>
            <th className="px-3 py-2">Type</th>
            {SORT_COLUMNS.map((col) => (
              <th key={col.key} className="px-3 py-2">
                <Link href={sortHref(col.key)} className="hover:underline">
                  {col.label} {currentSortBy === col.key ? (currentSortDir === "desc" ? "↓" : "↑") : ""}
                </Link>
              </th>
            ))}
            <th className="px-3 py-2">Flags</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {trades.map((t) => (
            <tr key={t.trade_id} className="hover:bg-gray-50">
              <td className="px-3 py-2">
                <Link href={`/members/${t.member.member_id}`} className="text-blue-600 hover:underline">
                  {t.member.full_name}
                </Link>
                <div className="text-xs text-gray-400">
                  {t.member.party}-{t.member.state} ({t.member.chamber})
                </div>
              </td>
              <td className="px-3 py-2">
                {t.ticker ? (
                  <Link href={`/tickers/${t.ticker}`} className="font-medium text-blue-600 hover:underline">
                    {t.ticker}
                  </Link>
                ) : (
                  <span className="text-gray-400">unmatched</span>
                )}
                <div className="text-xs text-gray-400">{t.asset_name_raw}</div>
              </td>
              <td className="px-3 py-2 capitalize">{t.transaction_type}</td>
              <td className="px-3 py-2">{t.transaction_date}</td>
              <td className="px-3 py-2">{t.disclosure_date}</td>
              <td className="px-3 py-2">{t.filing_lag_days}d</td>
              <td className="px-3 py-2">{fmtAmount(t.amount_min, t.amount_max)}</td>
              <td className="px-3 py-2">{fmtScore(t.performance)}</td>
              <td className="px-3 py-2">{fmtScore(t.overlap)}</td>
              <td className="px-3 py-2">{fmtScore(t.conviction)}</td>
              <td className="px-3 py-2 font-semibold">{fmtScore(t.composite)}</td>
              <td className="px-3 py-2">
                <div className="flex flex-col gap-1">
                  {t.committee_relevant && (
                    <span className="rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-800">Committee</span>
                  )}
                  {t.bipartisan_overlap && (
                    <span className="rounded bg-purple-100 px-1.5 py-0.5 text-xs text-purple-800">Bipartisan</span>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {trades.length === 0 && (
        <p className="p-6 text-center text-gray-400">No trades match the current filters.</p>
      )}
    </div>
  );
}
