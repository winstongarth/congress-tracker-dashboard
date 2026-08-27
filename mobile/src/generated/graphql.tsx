import { gql } from '@apollo/client';
import * as Apollo from '@apollo/client';
export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
export type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]?: Maybe<T[SubKey]> };
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]: Maybe<T[SubKey]> };
export type MakeEmpty<T extends { [key: string]: unknown }, K extends keyof T> = { [_ in K]?: never };
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
const defaultOptions = {} as const;
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: { input: string; output: string; }
  String: { input: string; output: string; }
  Boolean: { input: boolean; output: boolean; }
  Int: { input: number; output: number; }
  Float: { input: number; output: number; }
  Date: { input: string; output: string; }
};

export enum AssetType {
  Bond = 'BOND',
  Crypto = 'CRYPTO',
  Fund = 'FUND',
  Option = 'OPTION',
  Other = 'OTHER',
  Stock = 'STOCK'
}

export enum Chamber {
  House = 'HOUSE',
  Senate = 'SENATE'
}

export enum Owner {
  DependentChild = 'DEPENDENT_CHILD',
  Joint = 'JOINT',
  Self = 'SELF',
  Spouse = 'SPOUSE'
}

export enum Party {
  D = 'D',
  I = 'I',
  R = 'R'
}

export type Politician = {
  __typename?: 'Politician';
  active: Scalars['Boolean']['output'];
  chamber: Chamber;
  committees: Array<Scalars['String']['output']>;
  district?: Maybe<Scalars['String']['output']>;
  fullName: Scalars['String']['output'];
  id: Scalars['ID']['output'];
  party: Party;
  /** Member-level performance rollup (0-100 percentile), if computed. */
  performance?: Maybe<Scalars['Float']['output']>;
  photoUrl?: Maybe<Scalars['String']['output']>;
  /** Realized/unrealized P&L for this member, if computed. */
  portfolioReturn?: Maybe<PortfolioReturnType>;
  /** Total disclosed amount_mid per sector across this member's trades. */
  sectorBreakdown: Array<SectorBreakdownEntry>;
  state: Scalars['String']['output'];
  /** Number of trades on file for this member. */
  tradeCount: Scalars['Int']['output'];
  /** This member's trades, most recent first. */
  trades: TradeConnection;
};


export type PoliticianTradesArgs = {
  limit?: Scalars['Int']['input'];
  offset?: Scalars['Int']['input'];
};

export type PoliticianConnection = {
  __typename?: 'PoliticianConnection';
  results: Array<Politician>;
  totalCount: Scalars['Int']['output'];
};

export type PortfolioReturnType = {
  __typename?: 'PortfolioReturnType';
  realizedCostBasis?: Maybe<Scalars['Float']['output']>;
  realizedPnl?: Maybe<Scalars['Float']['output']>;
  realizedPnlPct?: Maybe<Scalars['Float']['output']>;
  unrealizedCostBasis?: Maybe<Scalars['Float']['output']>;
  unrealizedPnl?: Maybe<Scalars['Float']['output']>;
  unrealizedPnlPct?: Maybe<Scalars['Float']['output']>;
};

export type Query = {
  __typename?: 'Query';
  /** A single member of Congress by id (bioguide id). */
  politician?: Maybe<Politician>;
  /** Search/browse tracked members of Congress. */
  politicians: PoliticianConnection;
  /** Search/browse tracked trades. */
  trades: TradeConnection;
};


export type QueryPoliticianArgs = {
  id: Scalars['ID']['input'];
};


export type QueryPoliticiansArgs = {
  chamber?: InputMaybe<Chamber>;
  limit?: Scalars['Int']['input'];
  offset?: Scalars['Int']['input'];
  search?: InputMaybe<Scalars['String']['input']>;
};


export type QueryTradesArgs = {
  from?: InputMaybe<Scalars['Date']['input']>;
  limit?: Scalars['Int']['input'];
  offset?: Scalars['Int']['input'];
  politicianId?: InputMaybe<Scalars['ID']['input']>;
  ticker?: InputMaybe<Scalars['String']['input']>;
  to?: InputMaybe<Scalars['Date']['input']>;
};

export type SectorBreakdownEntry = {
  __typename?: 'SectorBreakdownEntry';
  amountMid: Scalars['Float']['output'];
  sector: Scalars['String']['output'];
};

export type Trade = {
  __typename?: 'Trade';
  amountMax: Scalars['Float']['output'];
  amountMid: Scalars['Float']['output'];
  amountMin: Scalars['Float']['output'];
  assetNameRaw: Scalars['String']['output'];
  assetType: AssetType;
  bipartisanOverlap: Scalars['Boolean']['output'];
  committeeRelevant: Scalars['Boolean']['output'];
  /** 0-100 weighted composite score for this trade, if computed. */
  composite?: Maybe<Scalars['Float']['output']>;
  /** 0-100 percentile conviction score for this trade, if computed. */
  conviction?: Maybe<Scalars['Float']['output']>;
  disclosureDate: Scalars['Date']['output'];
  filingId: Scalars['String']['output'];
  filingLagDays: Scalars['Int']['output'];
  id: Scalars['ID']['output'];
  /** Industry for the matched ticker, if any. */
  industry?: Maybe<Scalars['String']['output']>;
  /** 0-100 percentile overlap score for this trade, if computed. */
  overlap?: Maybe<Scalars['Float']['output']>;
  owner: Owner;
  /** 0-100 percentile performance score for this trade, if computed. */
  performance?: Maybe<Scalars['Float']['output']>;
  /** The member who filed this trade. */
  politician: Politician;
  /** GICS-ish sector for the matched ticker, if any. */
  sector?: Maybe<Scalars['String']['output']>;
  sourceUrl: Scalars['String']['output'];
  ticker?: Maybe<Scalars['String']['output']>;
  tickerMatchConfidence?: Maybe<Scalars['Float']['output']>;
  transactionDate: Scalars['Date']['output'];
  transactionType: TransactionType;
};

export type TradeConnection = {
  __typename?: 'TradeConnection';
  results: Array<Trade>;
  totalCount: Scalars['Int']['output'];
};

export enum TransactionType {
  Buy = 'BUY',
  Exchange = 'EXCHANGE',
  Sell = 'SELL'
}

export type TradesFeedQueryVariables = Exact<{
  limit?: InputMaybe<Scalars['Int']['input']>;
  offset?: InputMaybe<Scalars['Int']['input']>;
}>;


export type TradesFeedQuery = { __typename?: 'Query', trades: { __typename?: 'TradeConnection', totalCount: number, results: Array<{ __typename?: 'Trade', id: string, ticker?: string | null, assetNameRaw: string, transactionType: TransactionType, disclosureDate: string, amountMin: number, amountMax: number, politician: { __typename?: 'Politician', id: string, fullName: string } }> } };


export const TradesFeedDocument = gql`
    query TradesFeed($limit: Int, $offset: Int) {
  trades(limit: $limit, offset: $offset) {
    totalCount
    results {
      id
      ticker
      assetNameRaw
      transactionType
      disclosureDate
      amountMin
      amountMax
      politician {
        id
        fullName
      }
    }
  }
}
    `;

/**
 * __useTradesFeedQuery__
 *
 * To run a query within a React component, call `useTradesFeedQuery` and pass it any options that fit your needs.
 * When your component renders, `useTradesFeedQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useTradesFeedQuery({
 *   variables: {
 *      limit: // value for 'limit'
 *      offset: // value for 'offset'
 *   },
 * });
 */
export function useTradesFeedQuery(baseOptions?: Apollo.QueryHookOptions<TradesFeedQuery, TradesFeedQueryVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<TradesFeedQuery, TradesFeedQueryVariables>(TradesFeedDocument, options);
      }
export function useTradesFeedLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<TradesFeedQuery, TradesFeedQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<TradesFeedQuery, TradesFeedQueryVariables>(TradesFeedDocument, options);
        }
// @ts-ignore
export function useTradesFeedSuspenseQuery(baseOptions?: Apollo.SuspenseQueryHookOptions<TradesFeedQuery, TradesFeedQueryVariables>): Apollo.UseSuspenseQueryResult<TradesFeedQuery, TradesFeedQueryVariables>;
export function useTradesFeedSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<TradesFeedQuery, TradesFeedQueryVariables>): Apollo.UseSuspenseQueryResult<TradesFeedQuery | undefined, TradesFeedQueryVariables>;
export function useTradesFeedSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<TradesFeedQuery, TradesFeedQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<TradesFeedQuery, TradesFeedQueryVariables>(TradesFeedDocument, options);
        }
export type TradesFeedQueryHookResult = ReturnType<typeof useTradesFeedQuery>;
export type TradesFeedLazyQueryHookResult = ReturnType<typeof useTradesFeedLazyQuery>;
export type TradesFeedSuspenseQueryHookResult = ReturnType<typeof useTradesFeedSuspenseQuery>;
export type TradesFeedQueryResult = Apollo.QueryResult<TradesFeedQuery, TradesFeedQueryVariables>;