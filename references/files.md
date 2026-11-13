# Account files

## portfolio.json

| Key | Example (UBL / US) | Used by |
|---|---|---|
| `name` | "Al-Ameen Portfolio Tracker" | page title, artifact title |
| `source` | "ubl-fmr" / "prices" | how the numbers arrive: `references/sources/<source>.md`, its script, page wording (`templates/text.json`) |
| `country` | "pk" / "us" | where the account is held: `references/countries/<country>.md` (currency, inflation, trading, tax) |
| `currency` | `{"code": "PKR", "symbol": "Rs", "name": "rupees"}` / `{"code": "USD", "symbol": "$", "name": "dollars"}` | `money.py`, pre-commit guard, page wording |
| `plan` | "moderate, 5+ years" | page header |
| `cash` | "AICF" / "SGOV" | the "vs leaving it all in cash" comparison; must be a code in `funds.json` with monthly figures |
| `index` | `{"name": "KSE-100"}` / `{"name": "S&P 500 (SPY)", "symbol": "SPY"}` | market strip; for `prices.py` also the benchmark of every non-cash holding |
| `fred` | `{"cpi": "CPIAUCSL", "policy_rate": "FEDFUNDS"}` | `prices.py macro` only; the series ids are in the country file |
| `fy_start` | 7 (July) / 1 (January) | year tables, "since the start of each year", year-to-date |
| `app` | "UBL app" / "broker app" | page note: growth won't match the gain % in your {app} |
| `tax_rate_on_gains` | 0.20 / 0.15 | `money.py` flat tax estimate (not tax advice) |
| `text` | `{"help_score_read": "<p>…</p>"}` | optional overrides of any key in `templates/text.json` for this account's plan |

Values that also land inside JS strings (`cash`, `index.name`, and the source's `fund`, `Fund`, `report` words) must not contain `'` or `\`; `build_page.py` checks.

## data/ (each JSON file is one dashboard dataset)

| File | Rows | Notes |
|---|---|---|
| `allocations.json` | `{entry, date, fund, pct}` | One set of rows per log entry; each entry sums to 100. |
| `log_notes.json` | `{entry, date, rationale, verdict, planned, next}` | `next` is the one concrete next step; the dashboard shows the latest. `planned: true` marks a deliberate step back (e.g. consolidating before a split), shown as Planned, not Lose. |
| `target.json` | `{fund, pct, action, set_on}` | The agreed target; change it only when the user agrees a new plan, and log why. |
| `snapshots.json` | `{date, return_since_last_pct, new_money_pct}` | From `money.py snapshot`. First row: `return_since_last_pct: null` (index 100). |
| `funds.json` | `{fund, name, category, risk, …}` | Holdings, low → high risk. `prices.py` also needs `equity_share_pct` (100 stock or stock ETF, 0 cash or bonds) and adds `vol_pct`. |
| `fund_stats.json` | `{month, fund, nav_change_pct, month_return_pct, month_bench_pct, month_is_annualized, fytd_pct, fytd_bench_pct, ret_1y_pct, ter_pct, equity_share_pct}` | One row per holding per month. `nav_change_pct` is the plain monthly total return (drives the estimate). When `month_is_annualized` is true, `month_return_pct` and `fytd_pct` are % a year (simple); the cash holding must be reported this way. `*_bench_pct` null = no benchmark. |
| `fund_years.json` | `{fund, fy, return_pct, bench_pct}` | Full fiscal years, named by the calendar year they end in. The current year comes from `fund_stats`. |
| `macro.json` | `{month, cpi_yoy_pct, policy_rate_pct, index_close}` | Never leave `cpi_yoy_pct` null: the growth maths would read it as 0% inflation. |
| `index.html` | | Built by `build_page.py`. |
| `published.json` | `{artifact, published_at, datasets: {id: {file, blob, sha256}}, page: {file, doc_version, sha256}}` | Not a dataset. Written at publish. |

## Account root

- `checks.json`: (optional) `{"scenarios": {"<name>": {"note", "append": {dataset: [rows]}, "replace": {dataset: rows}}}}`. A scenario simulates rows (next month's figures, a second snapshot) to test the win/lose logic: `node $S/check_calcs.js . <name>`.
- `private/holdings.csv`: needs `date,fund,value,to_date_gain`; any other columns the app shows (units, unit price) can stay.
- `private/cashflows.csv`: `date,fund,amount,note`; money in > 0, money out < 0, a cash dividend is money out.
- `private/keys.env`: optional `NAME=value` lines for a keyed price provider (e.g. `ALPHAVANTAGE_API_KEY`), written by the user. An environment variable of the same name wins.
