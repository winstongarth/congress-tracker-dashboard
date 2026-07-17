import { fetchMember, fetchTrades } from "@/lib/api";
import { fmtDollar, fmtPct, pnlColor } from "@/lib/format";
import SectorChart from "@/components/SectorChart";
import TradeTable from "@/components/TradeTable";

export default async function MemberPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const member = await fetchMember(id);
  const trades = await fetchTrades({
    page: 1,
    page_size: 100,
    sort_by: "transaction_date",
    sort_dir: "desc",
    member_id: id,
  });

  return (
    <div className="mx-auto max-w-7xl space-y-4 p-4">
      <div className="flex items-center gap-4 rounded-lg border border-gray-200 bg-white p-4">
        {member.photo_url && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={member.photo_url} alt={member.full_name} className="h-20 w-20 rounded-full object-cover" />
        )}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{member.full_name}</h1>
          <p className="text-sm text-gray-500">
            {member.party}-{member.state}
            {member.district ? `-${member.district}` : ""} ({member.chamber})
          </p>
          <p className="text-sm text-gray-500">
            {member.trade_count} tracked trades
            {member.performance_rollup !== null && (
              <> &middot; avg performance score: {member.performance_rollup.toFixed(1)}</>
            )}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h2 className="mb-1 text-sm font-medium text-gray-500">Realized P&amp;L</h2>
          <p className={`text-2xl font-bold ${pnlColor(member.realized_pnl)}`}>{fmtDollar(member.realized_pnl)}</p>
          <p className={`text-sm ${pnlColor(member.realized_pnl_pct)}`}>{fmtPct(member.realized_pnl_pct)} on closed positions</p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h2 className="mb-1 text-sm font-medium text-gray-500">Unrealized P&amp;L</h2>
          <p className={`text-2xl font-bold ${pnlColor(member.unrealized_pnl)}`}>{fmtDollar(member.unrealized_pnl)}</p>
          <p className={`text-sm ${pnlColor(member.unrealized_pnl_pct)}`}>{fmtPct(member.unrealized_pnl_pct)} on positions still held</p>
        </div>
      </div>
      <p className="text-xs text-gray-400">
        Estimated from disclosed amount ranges, not exact share counts -- see the Members list page for
        the full methodology note.
      </p>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h2 className="mb-2 font-semibold text-gray-900">Committee Assignments</h2>
          {member.committees.length > 0 ? (
            <ul className="list-inside list-disc text-sm text-gray-600">
              {member.committees.map((c) => (
                <li key={c}>{c}</li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-400">No committee data available.</p>
          )}
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4">
          <h2 className="mb-2 font-semibold text-gray-900">Sector Breakdown</h2>
          <SectorChart sectorBreakdown={member.sector_breakdown} />
        </div>
      </div>

      <h2 className="text-lg font-semibold text-gray-900">Trade History</h2>
      <TradeTable
        trades={trades.results}
        currentSortBy="transaction_date"
        currentSortDir="desc"
        searchParamsString={`member_id=${id}`}
      />
    </div>
  );
}
