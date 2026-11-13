# Adding a country

A country file holds the rules that come from where the account is held, whatever the source: `references/countries/<ISO 3166 alpha-2 code, lower case>.md`, named in `portfolio.json` `country`.

## Sections (same as `pk.md` and `us.md`)

1. **Conventions:** currency code and symbol, how large amounts are written (the pre-commit guard must catch that style), fiscal or tax year (`fy_start`), time zone, and any return-reporting convention local funds follow.
2. **Inflation and rates:** the official CPI and policy-rate publishers, and, if FRED carries them, the series ids for `portfolio.json` `fred` (check each id returns a CSV before writing it down).
3. **Trading:** market hours and settlement cycle, fund dealing days.
4. **Tax (estimate only):** how gains, dividends and switches are taxed, and tax-advantaged schemes. No rates unless checked against the tax authority's own page, with the date checked. End with the disclaimer: estimate only, not tax advice; confirm with a tax professional or the tax authority (named); the skill and its author accept no liability.

## Rules

- Every fact is checked against an official source or marked unverified.
- Nothing about one fund company or one data source; that goes in the source file.
- Write current rules only, without dates of past changes.
