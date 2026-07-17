export interface MemberSummary {
  member_id: string;
  full_name: string;
  chamber: "house" | "senate";
  party: "D" | "R" | "I";
  state: string;
  district: string | null;
  photo_url: string | null;
}

export interface TradeOut {
  trade_id: number;
  member: MemberSummary;
  filing_id: string;
  asset_name_raw: string;
  ticker: string | null;
  ticker_match_confidence: number | null;
  asset_type: string;
  sector: string | null;
  industry: string | null;
  owner: string;
  transaction_type: string;
  transaction_date: string;
  disclosure_date: string;
  filing_lag_days: number;
  amount_min: number;
  amount_max: number;
  amount_mid: number;
  source_url: string;
  committee_relevant: boolean;
  performance: number | null;
  overlap: number | null;
  conviction: number | null;
  composite: number | null;
  bipartisan_overlap: boolean;
}

export interface TradePage {
  total: number;
  page: number;
  page_size: number;
  results: TradeOut[];
}

export interface PortfolioReturnFields {
  realized_pnl: number | null;
  realized_cost_basis: number | null;
  realized_pnl_pct: number | null;
  unrealized_pnl: number | null;
  unrealized_cost_basis: number | null;
  unrealized_pnl_pct: number | null;
}

export interface MemberListEntry extends MemberSummary, PortfolioReturnFields {
  trade_count: number;
}

export interface MemberDetail extends MemberSummary, PortfolioReturnFields {
  committees: string[];
  performance_rollup: number | null;
  trade_count: number;
  sector_breakdown: Record<string, number>;
}

export interface TickerTradeEntry {
  member: MemberSummary;
  transaction_type: string;
  transaction_date: string;
  amount_min: number;
  amount_max: number;
  bipartisan_overlap: boolean;
}

export interface TickerDetail {
  ticker: string;
  company_name: string | null;
  sector: string | null;
  industry: string | null;
  trades: TickerTradeEntry[];
  distinct_members: number;
  has_bipartisan_overlap: boolean;
}

export interface TradeFilters {
  page: number;
  page_size: number;
  sort_by: string;
  sort_dir: "asc" | "desc";
  sector?: string;
  party?: string;
  bipartisan_only?: boolean;
  chamber?: string;
  transaction_type?: string;
  asset_type?: string;
  transaction_date_from?: string;
  transaction_date_to?: string;
  filing_lag_bucket?: string;
  committee_relevant?: boolean;
  member_id?: string;
  ticker?: string;
  search?: string;
}
