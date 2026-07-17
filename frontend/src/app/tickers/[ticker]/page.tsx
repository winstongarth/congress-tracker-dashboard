import Link from "next/link";
import { fetchTicker } from "@/lib/api";

export default async function TickerPage({ params }: { params: Promise<{ ticker: string }> }) {
  const { ticker } = await params;
  const data = await fetchTicker(ticker);

  return (
    <div className="mx-auto max-w-5xl space-y-4 p-4">
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <h1 className="text-2xl font-bold text-gray-900">
          {data.ticker} {data.company_name && <span className="text-gray-500">— {data.company_name}</span>}
        </h1>
        <p className="text-sm text-gray-500">
          {data.sector ?? "Unknown sector"} {data.industry ? `/ ${data.industry}` : ""}
        </p>
        <p className="mt-2 text-sm text-gray-600">
          {data.distinct_members} distinct tracked member{data.distinct_members === 1 ? "" : "s"}{" "}
          {data.distinct_members === 1 ? "has" : "have"} traded this ticker.
        </p>
        {data.has_bipartisan_overlap && (
          <span className="mt-2 inline-block rounded bg-purple-100 px-2 py-1 text-xs font-medium text-purple-800">
            Bipartisan overlap detected
          </span>
        )}
      </div>

      <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
            <tr>
              <th className="px-3 py-2">Member</th>
              <th className="px-3 py-2">Type</th>
              <th className="px-3 py-2">Date</th>
              <th className="px-3 py-2">Amount</th>
              <th className="px-3 py-2">Bipartisan</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {data.trades.map((t, i) => (
              <tr key={i} className="hover:bg-gray-50">
                <td className="px-3 py-2">
                  <Link href={`/members/${t.member.member_id}`} className="text-blue-600 hover:underline">
                    {t.member.full_name}
                  </Link>
                  <span className="ml-1 text-xs text-gray-400">
                    ({t.member.party}-{t.member.state})
                  </span>
                </td>
                <td className="px-3 py-2 capitalize">{t.transaction_type}</td>
                <td className="px-3 py-2">{t.transaction_date}</td>
                <td className="px-3 py-2">
                  ${t.amount_min.toLocaleString()} - ${t.amount_max.toLocaleString()}
                </td>
                <td className="px-3 py-2">{t.bipartisan_overlap ? "Yes" : ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
