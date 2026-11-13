# Adding a data source

A source is how the numbers arrive: a price feed, or one fund company's monthly report. Every source writes the same rows, so the page and `check_calcs.js` never know which one ran.

## Row contract

A source must produce, as JSON on stdout (schemas in `references/files.md`):

| Rows | Fields | Rules |
|---|---|---|
| `fund_stats` | `month, fund, nav_change_pct, month_return_pct, month_bench_pct, month_is_annualized, fytd_pct, fytd_bench_pct, ret_1y_pct, ter_pct, equity_share_pct` | One row per holding per finished month. `nav_change_pct` is the plain monthly total return. The cash holding reports `month_return_pct` and `fytd_pct` as % a year with `month_is_annualized: true`. `null` for a figure the source doesn't have, never a guess. |
| `fund_years` | `fund, fy, return_pct, bench_pct` | Full fiscal years only, named by the year they end in. |
| `macro` | `month, cpi_yoy_pct, policy_rate_pct, index_close` | `cpi_yoy_pct` never null. Can come from the source or by hand. |
| `funds` | `fund, name, category, risk, equity_share_pct` | Risk `Low`/`Medium`/`High`, listed low → high risk. |

## Checklist

1. `scripts/<source>.py` (snake_case of the source name). It stops with a clear message when a reply isn't the expected data (layout change, bot check, error JSON) and never writes a guessed number.
2. A self-check in its `__main__`: an assert on a small fixture (a saved snippet or a made-up series) that runs on every call, like `prices.py` and `ubl_fmr.py`.
3. `references/sources/<source>.md`: URL pattern, quirks, the monthly refresh steps, and what each field means for this source. Facts about one fund company stay here, never in a country file.
4. A block named `<source>` in `templates/text.json` with the same keys as the others (page wording: "fund" or "holding", how risk is rated, what the benchmark is).
5. List it under "Source and country" in `SKILL.md`.
6. Test on an account: `build_page.py` (no unfilled slots), `check_calcs.js` (the `score` rows print), the year tables show every holding (codes may be any string, e.g. `7203.T`), and the existing accounts' `check_calcs.js` output unchanged.

## Adding a keyed provider to `prices.py`

A provider is another feed of the same closing prices; it only changes where `fetch` gets them.
1. A function that returns `[(date, adj_close, close)]` for one symbol (dividend- and split-adjusted), stopping with the provider's own error text when the reply has no series. `fetch` writes these as `<SYM>.csv`, the format the other commands already read.
2. Its key comes only from `api_key(account, "<NAME>_API_KEY")`: the environment, then `private/keys.env`. Never from `portfolio.json`, and never in `data/`, the page, a message or git. Pass URLs through `redact()` in error messages and mask the key in any provider text echoed back.
3. Choose it in `fetch` only when its key is set; otherwise the free path runs.
4. A self-check: parse a fixture reply, and check that an error reply stops without the key in the message (see `av_rows` asserts).
5. Document in `references/sources/prices.md`: the endpoint, free-tier limits with where and when they were checked, and what was tested.
