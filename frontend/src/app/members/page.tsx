import Link from "next/link";
import { fetchMembers } from "@/lib/api";
import { fmtDollar, fmtPct, pnlColor } from "@/lib/format";

type SearchParams = { [key: string]: string | string[] | undefined };

function asString(v: string | string[] | undefined): string | undefined {
  return Array.isArray(v) ? v[0] : v;
}

const SORT_COLUMNS: { key: string; label: string }[] = [
  { key: "full_name", label: "Member" },
  { key: "trade_count", label: "Trades" },
  { key: "realized_pnl", label: "Realized P&L" },
  { key: "realized_pnl_pct", label: "Realized %" },
  { key: "unrealized_pnl", label: "Unrealized P&L" },
  { key: "unrealized_pnl_pct", label: "Unrealized %" },
];

export default async function MembersPage({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const sp = await searchParams;
  const sortBy = asString(sp.sort_by) ?? "realized_pnl";
  const sortDir = (asString(sp.sort_dir) ?? "desc") as "asc" | "desc";
  const chamber = asString(sp.chamber);
  const party = asString(sp.party);

  const members = await fetchMembers({ chamber, party, sort_by: sortBy, sort_dir: sortDir });

  const sortHref = (column: string) => {
    const params = new URLSearchParams();
    if (chamber) params.set("chamber", chamber);
    if (party) params.set("party", party);
    const nextDir = sortBy === column && sortDir === "desc" ? "asc" : "desc";
    params.set("sort_by", column);
    params.set("sort_dir", nextDir);
    return `?${params.toString()}`;
  };

  const filterHref = (key: string, value: string) => {
    const params = new URLSearchParams();
    if (key !== "chamber" && chamber) params.set("chamber", chamber);
    if (key !== "party" && party) params.set("party", party);
    if (value) params.set(key, value);
    params.set("sort_by", sortBy);
    params.set("sort_dir", sortDir);
    return `?${params.toString()}`;
  };

  return (
    <div className="mx-auto max-w-6xl space-y-4 p-4">
      <h1 className="text-2xl font-bold text-gray-900">Members</h1>
      <p className="text-sm text-gray-500">
        Realized P&amp;L is from closed positions (bought, then later sold). Unrealized P&amp;L is
        mark-to-market on positions still held. Both are estimates: STOCK Act disclosures only give
        dollar ranges, never share counts, so position size is implied from the disclosed range
        midpoint, not exact.
      </p>

      <div className="flex flex-wrap gap-2 text-sm">
        <Link href={filterHref("chamber", "")} className={`rounded border px-2 py-1 ${!chamber ? "bg-gray-900 text-white" : ""}`}>
          All chambers
        </Link>
        <Link href={filterHref("chamber", "house")} className={`rounded border px-2 py-1 ${chamber === "house" ? "bg-gray-900 text-white" : ""}`}>
          House
        </Link>
        <Link href={filterHref("chamber", "senate")} className={`rounded border px-2 py-1 ${chamber === "senate" ? "bg-gray-900 text-white" : ""}`}>
          Senate
        </Link>
        <Link href={filterHref("party", "")} className={`rounded border px-2 py-1 ${!party ? "bg-gray-900 text-white" : ""}`}>
          All parties
        </Link>
        <Link href={filterHref("party", "D")} className={`rounded border px-2 py-1 ${party === "D" ? "bg-gray-900 text-white" : ""}`}>
          D
        </Link>
        <Link href={filterHref("party", "R")} className={`rounded border px-2 py-1 ${party === "R" ? "bg-gray-900 text-white" : ""}`}>
          R
        </Link>
      </div>

      <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
            <tr>
              {SORT_COLUMNS.map((col) => (
                <th key={col.key} className="px-3 py-2">
                  <Link href={sortHref(col.key)} className="hover:underline">
                    {col.label} {sortBy === col.key ? (sortDir === "desc" ? "↓" : "↑") : ""}
                  </Link>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {members.map((m) => (
              <tr key={m.member_id} className="hover:bg-gray-50">
                <td className="px-3 py-2">
                  <Link href={`/members/${m.member_id}`} className="text-blue-600 hover:underline">
                    {m.full_name}
                  </Link>
                  <div className="text-xs text-gray-400">
                    {m.party}-{m.state} ({m.chamber})
                  </div>
                </td>
                <td className="px-3 py-2">{m.trade_count}</td>
                <td className={`px-3 py-2 font-medium ${pnlColor(m.realized_pnl)}`}>{fmtDollar(m.realized_pnl)}</td>
                <td className={`px-3 py-2 ${pnlColor(m.realized_pnl_pct)}`}>{fmtPct(m.realized_pnl_pct)}</td>
                <td className={`px-3 py-2 font-medium ${pnlColor(m.unrealized_pnl)}`}>{fmtDollar(m.unrealized_pnl)}</td>
                <td className={`px-3 py-2 ${pnlColor(m.unrealized_pnl_pct)}`}>{fmtPct(m.unrealized_pnl_pct)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {members.length === 0 && <p className="p-6 text-center text-gray-400">No members found.</p>}
      </div>
    </div>
  );
}
