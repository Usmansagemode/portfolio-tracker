# Source: prices (anything with a ticker)

Script: `prices.py`. For stocks, ETFs and listed funds. Risk is measured from price swings.
`portfolio.json` needs `cash` (e.g. a T-bill ETF such as SGOV), `index` with a `symbol` (the benchmark of every non-cash holding, e.g. SPY), and `fred` (the country's CPI and policy-rate series, named in its country file). Each `data/funds.json` row needs `equity_share_pct` (100 for a stock or stock fund, 0 for cash or bonds).

## Checking new tickers (setup, or a holding added later)

`python3 -I $S/prices.py resolve . SYM [SYM ...]` with the holdings, the cash holding and the benchmark. For each it prints type, currency, exchange, listing date and name, then the `data/funds.json` draft rows on stdout. It exits 1 with one list of questions when a ticker:
- is not found (it lists other listings of the same ticker if any),
- is priced in another currency than the account's (it lists other listings; pick one in the account's currency),
- has under 36 months of history (its risk is set by hand),
- is an ETF or fund, whose share in stocks it can't tell (ignore that line for the benchmark).

An ADR (e.g. BABA) resolves as a stock in USD; Yahoo does not mark it as an ADR. Yahoo gives no expense ratio without a session cookie, so `ter_pct` is added by hand from the issuer's page if wanted.

## Data

Default: free, no key, unofficial. Either source can change, rate-limit or block without notice. `prices.py` stops with a message when a reply is not the expected data; it never writes a guessed number.

- **Prices:** Yahoo Finance chart endpoint, daily bars, `https://query1.finance.yahoo.com/v8/finance/chart/<SYM>?period1=<unix>&period2=9999999999&interval=1d&events=div,split`. `adjclose` includes dividends and splits, so returns are total returns. Yahoo answers Python's default User-Agent, and a full Chrome one, with 429; plain `Mozilla/5.0` works. Daily bars are used because its monthly series adds extra rows on dividend dates. `resolve` uses the same endpoint (`range=1d`, its `meta`) and `/v1/finance/search?q=<SYM>`.
- **Inflation and policy rate:** FRED CSV, `https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES>`. FRED refuses a bare "Mozilla/5.0" User-Agent, so it is called with the default one. A missing month stops `macro`: take the figure from the official release and write that macro row by hand.
- **Not used:** Stooq's CSV download sits behind a JavaScript proof-of-work bot check.
- **Fallback when Yahoo fails:** save `<dl dir>/<CODE>.csv` with columns `date,adj_close,close` (daily or month-end, dividend-adjusted, from the broker's export or another source), delete `<CODE>.json`, and rerun `stats`/`years`/`risk`/`macro`: they read the CSV instead.

### Optional key: Alpha Vantage

Set `ALPHAVANTAGE_API_KEY` in the environment or as a line `ALPHAVANTAGE_API_KEY=<key>` in `private/keys.env` (the user writes this file; Claude never reads or prints it). `fetch` then takes prices from `TIME_SERIES_MONTHLY_ADJUSTED` (month-end adjusted close, 25+ years) and saves them in the fallback CSV format; nothing else changes. Without the key, the free Yahoo path runs. FRED needs no key.
- Free tier: 25 requests a day (alphavantage.co/support, checked 2026-11-12); one `fetch` uses one request per holding plus one for the index. Monthly Adjusted is free; Daily Adjusted is premium (alphavantage.co/documentation, checked 2026-11-12). The 1.2 s pause between calls guards against a per-second burst limit that is unverified.
- Alpha Vantage returned data for a made-up key in testing, so a wrong key may not fail at once. A refusal (rate limit, unknown symbol) stops `fetch` with Alpha Vantage's own message, key masked.
- Its `ETF_PROFILE` function returns an ETF's `net_expense_ratio` and holdings; `prices.py` doesn't call it.

## Monthly refresh (after a month ends)

1. `python3 -I $S/prices.py fetch . <scratchpad>/prices`
2. `python3 -I $S/prices.py stats . <scratchpad>/prices YYYY-MM` → append to `data/fund_stats.json`. It refuses a month that has not finished.
3. `python3 -I $S/prices.py macro . <scratchpad>/prices YYYY-MM` → append to `data/macro.json`.
4. At the start of each fiscal year, and when a holding is added: `prices.py years` → replace `data/fund_years.json` (last 10 full years), and `prices.py risk` → replace `data/funds.json` (risk and order), then rebuild the page.
5. `check_calcs.js`.

## How the figures are worked out

- Month-end = last trading day's adjusted close. Monthly, year-to-date, 1-year and full-year returns are ratios of month-end adjusted closes.
- The **cash holding** is reported as % a year (simple: × 365 ÷ days), like a money-market fund, so the dashboard's "vs cash" maths treats it the same way. It has no benchmark.
- **Risk:** annualised volatility = standard deviation of up to the last 60 finished monthly returns (at least 36) × √12. Bands: Low under 5%, Medium 5% to under 15%, High 15% and up. These are the cut-offs of the EU UCITS risk scale (SRRI, CESR/10-673: classes 1–3 under 5%, 4–5 from 5% to under 15%, 6–7 from 15%), taken from secondary sources rather than the ESMA PDF itself. A broad stock ETF lands in High (about 15–18%); a T-bill ETF in Low.
- `ter_pct` (expense ratio) is not fetched; add it to a `funds.json` row by hand if wanted, and `stats` carries it.
