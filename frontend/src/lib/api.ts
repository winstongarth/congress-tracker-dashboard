import { MemberDetail, MemberListEntry, TickerDetail, TradeFilters, TradePage } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function buildQuery(filters: Record<string, unknown>): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== null && value !== "") {
      params.set(key, String(value));
    }
  }
  return params.toString();
}

export async function fetchTrades(filters: Partial<TradeFilters>): Promise<TradePage> {
  const res = await fetch(`${API_URL}/trades?${buildQuery(filters)}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch trades: ${res.status}`);
  return res.json();
}

export interface MemberListFilters {
  chamber?: string;
  party?: string;
  sort_by?: string;
  sort_dir?: "asc" | "desc";
  [key: string]: string | undefined;
}

export async function fetchMembers(filters: MemberListFilters = {}): Promise<MemberListEntry[]> {
  const res = await fetch(`${API_URL}/members?${buildQuery(filters)}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch members: ${res.status}`);
  return res.json();
}

export async function fetchMember(memberId: string): Promise<MemberDetail> {
  const res = await fetch(`${API_URL}/members/${memberId}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch member: ${res.status}`);
  return res.json();
}

export async function fetchTicker(ticker: string): Promise<TickerDetail> {
  const res = await fetch(`${API_URL}/tickers/${ticker}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch ticker: ${res.status}`);
  return res.json();
}
