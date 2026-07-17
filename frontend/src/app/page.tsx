import { fetchTrades } from "@/lib/api";
import FilterBar from "@/components/FilterBar";
import TradeTable from "@/components/TradeTable";
import Pagination from "@/components/Pagination";

type SearchParams = { [key: string]: string | string[] | undefined };

function asString(v: string | string[] | undefined): string | undefined {
  return Array.isArray(v) ? v[0] : v;
}

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const sp = await searchParams;

  const page = Number(asString(sp.page) ?? "1");
  const pageSize = 50;
  const sortBy = asString(sp.sort_by) ?? "transaction_date";
  const sortDir = (asString(sp.sort_dir) ?? "desc") as "asc" | "desc";

  const data = await fetchTrades({
    page,
    page_size: pageSize,
    sort_by: sortBy,
    sort_dir: sortDir,
    sector: asString(sp.sector),
    party: asString(sp.party),
    bipartisan_only: asString(sp.bipartisan_only) === "true",
    chamber: asString(sp.chamber),
    transaction_type: asString(sp.transaction_type),
    asset_type: asString(sp.asset_type),
    filing_lag_bucket: asString(sp.filing_lag_bucket),
    committee_relevant: asString(sp.committee_relevant) === "true" ? true : undefined,
    search: asString(sp.search),
  });

  const searchParamsString = new URLSearchParams(
    Object.entries(sp).flatMap(([k, v]) => (v === undefined ? [] : [[k, asString(v) as string]]))
  ).toString();

  return (
    <div className="mx-auto max-w-7xl space-y-4 p-4">
      <h1 className="text-2xl font-bold text-gray-900">Congressional Trades</h1>
      <FilterBar />
      <TradeTable
        trades={data.results}
        currentSortBy={sortBy}
        currentSortDir={sortDir}
        searchParamsString={searchParamsString}
      />
      <Pagination page={data.page} pageSize={data.page_size} total={data.total} searchParamsString={searchParamsString} />
    </div>
  );
}
