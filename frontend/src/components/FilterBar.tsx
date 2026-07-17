"use client";

import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { useCallback } from "react";

const SECTORS = [
  "Technology",
  "Healthcare",
  "Financial Services",
  "Consumer Cyclical",
  "Consumer Defensive",
  "Energy",
  "Industrials",
  "Communication Services",
  "Real Estate",
  "Basic Materials",
  "Utilities",
];

export default function FilterBar() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const setParam = useCallback(
    (key: string, value: string) => {
      const params = new URLSearchParams(searchParams.toString());
      if (value) {
        params.set(key, value);
      } else {
        params.delete(key);
      }
      params.set("page", "1");
      router.push(`${pathname}?${params.toString()}`);
    },
    [router, pathname, searchParams]
  );

  const toggleParam = useCallback(
    (key: string) => {
      const params = new URLSearchParams(searchParams.toString());
      if (params.get(key) === "true") {
        params.delete(key);
      } else {
        params.set(key, "true");
      }
      params.set("page", "1");
      router.push(`${pathname}?${params.toString()}`);
    },
    [router, pathname, searchParams]
  );

  return (
    <div className="flex flex-wrap items-center gap-2 rounded-lg border border-gray-200 bg-white p-3 text-sm">
      <input
        type="text"
        placeholder="Search member or ticker..."
        defaultValue={searchParams.get("search") ?? ""}
        onChange={(e) => setParam("search", e.target.value)}
        className="rounded border border-gray-300 px-2 py-1"
      />
      <select
        defaultValue={searchParams.get("sector") ?? ""}
        onChange={(e) => setParam("sector", e.target.value)}
        className="rounded border border-gray-300 px-2 py-1"
      >
        <option value="">All sectors</option>
        {SECTORS.map((s) => (
          <option key={s} value={s}>
            {s}
          </option>
        ))}
      </select>
      <select
        defaultValue={searchParams.get("party") ?? ""}
        onChange={(e) => setParam("party", e.target.value)}
        className="rounded border border-gray-300 px-2 py-1"
      >
        <option value="">All parties</option>
        <option value="D">Democrat</option>
        <option value="R">Republican</option>
        <option value="I">Independent</option>
      </select>
      <select
        defaultValue={searchParams.get("chamber") ?? ""}
        onChange={(e) => setParam("chamber", e.target.value)}
        className="rounded border border-gray-300 px-2 py-1"
      >
        <option value="">House + Senate</option>
        <option value="house">House</option>
        <option value="senate">Senate</option>
      </select>
      <select
        defaultValue={searchParams.get("transaction_type") ?? ""}
        onChange={(e) => setParam("transaction_type", e.target.value)}
        className="rounded border border-gray-300 px-2 py-1"
      >
        <option value="">Buy + Sell + Exchange</option>
        <option value="buy">Buy</option>
        <option value="sell">Sell</option>
        <option value="exchange">Exchange</option>
      </select>
      <select
        defaultValue={searchParams.get("asset_type") ?? ""}
        onChange={(e) => setParam("asset_type", e.target.value)}
        className="rounded border border-gray-300 px-2 py-1"
      >
        <option value="">All asset types</option>
        <option value="stock">Stock</option>
        <option value="option">Option</option>
        <option value="bond">Bond</option>
        <option value="fund">Fund</option>
        <option value="crypto">Crypto</option>
        <option value="other">Other</option>
      </select>
      <select
        defaultValue={searchParams.get("filing_lag_bucket") ?? ""}
        onChange={(e) => setParam("filing_lag_bucket", e.target.value)}
        className="rounded border border-gray-300 px-2 py-1"
      >
        <option value="">Any filing lag</option>
        <option value="within_10">Filed within 10 days</option>
        <option value="11_to_30">Filed 11-30 days</option>
        <option value="31_to_45">Filed 31-45 days</option>
        <option value="late">Filed after 45 days (late)</option>
      </select>
      <label className="flex items-center gap-1">
        <input
          type="checkbox"
          checked={searchParams.get("bipartisan_only") === "true"}
          onChange={() => toggleParam("bipartisan_only")}
        />
        Bipartisan overlap only
      </label>
      <label className="flex items-center gap-1">
        <input
          type="checkbox"
          checked={searchParams.get("committee_relevant") === "true"}
          onChange={() => toggleParam("committee_relevant")}
        />
        Committee-relevant only
      </label>
    </div>
  );
}
