# Market dataset

## Observations collected

- Provider: FRED, Federal Reserve Bank of St. Louis, relaying index-owner data.
- Original sources: S&P Dow Jones Indices LLC (S&P 500 and Dow), Nasdaq, Inc. (Nasdaq-100).
- Collection date: October 25, 2026. Exact UTC timestamp and hashes are in `collection_manifest.json`.
- Requested range: January 1, 2024 through October 23, 2026.
- Retained common range: January 2, 2024 through October 21, 2026.
- Sample: 704 dates per index, 2,112 rows total.
- Columns: `date` (YYYY-MM-DD), `index` (SP500, NASDAQ100, DOW), `close` (positive numeric index level).
- Frequency: daily market close, typically 4 p.m. America/New_York, subject to early closing days.
- Price convention: index levels, not ETF proxies and not total returns including dividends.

## Dataset links

- S&P 500 (SP500): https://fred.stlouisfed.org/series/SP500
- Nasdaq-100 (NASDAQ100): https://fred.stlouisfed.org/series/NASDAQ100
- Dow Jones Industrial Average (DJIA, labeled DOW in our CSV): https://fred.stlouisfed.org/series/DJIA
- Combined source CSV: https://fred.stlouisfed.org/graph/fredgraph.csv?id=SP500,NASDAQ100,DJIA

## Reproduce

Run `python scripts/download_market_data.py`. It writes the source bytes, a cleaned
`date,index,close` CSV, and a JSON manifest under `data/local/`.
The source download can contain a longer history than requested. The cleaner explicitly
filters dates locally, rejects duplicate dates and invalid prices, and retains only
dates with all three closes. It does not fill missing values or interpolate holidays.
The manifest lists excluded dates. FRED observations can be revised, so a future
retrieval may have different bytes or values. Use the recorded hashes for comparison.

## Use and publication

FRED marks these series copyrighted/pre-approval required. S&P 500 and Dow notes
require prior written permission for reproduction. Nasdaq also retains copyright.
The repository therefore publishes retrieval code, source links, schema, and provenance,
while observed data files and prompts that reproduce prices stay excluded from public Git.
No open-data license is claimed. Check provider permission for uses beyond your analysis.

## Relationship to the parent papers

This is a new index-level collection for the proposed extension. It is not the
individual-stock dataset supplied by LOG, PriceSeer, or StockBench.

## Research status

Real market data have been collected. Real assistant forecasts have not been collected.
The existing synthetic demo is separate from this observed dataset.
