# Recommending holdings (only when asked)

The default is rules-based next steps. Recommend specific holdings or a target mix only when the user asks what to hold, add or swap, or during setup when there is no target or no holdings yet (`SKILL.md`, set up step 3).

## Before recommending

Know the goal, horizon and constraints (e.g. Shariah-compliant only, low cost, the account's currency, no single stock above a cap). Ask once, in one message, for any that are missing; offer the plan in `portfolio.json` as the default. If they stay unknown, use the defaults in `SKILL.md` set up step 2 and say so.

## Evidence for each pick

Every number is one fetched or checked in this session, with its source and date. A number that can't be checked is left out or marked unverified, never estimated.
- **Exists and fits the account:** `prices.py resolve` (currency, type, months of history). With under 36 months of history, say so.
- **Risk:** volatility from `prices.py risk` (or the fund report's own rating) and its band.
- **Cost:** expense ratio from the issuer's page or fund report (`ter_pct`).
- **Diversification:** number of holdings and the weight of the top 10 or the largest sector, from the issuer's page or fund report.
- **History:** year-by-year returns from `prices.py years` or the fund report, against the benchmark.
- **Fit with the portfolio:** overlap with what is already held (e.g. two S&P 500 Shariah ETFs hold mostly the same companies), effect on equity exposure, and the share in any one company, sector or country after the change.
- **Constraint check:** e.g. the fund's Shariah certification or index methodology, from the issuer's page.

## Reply

A table, `Pick | Role | Evidence (figure, source) | Fit`, then the suggested target change and how to get there by the usual rules (monthly steps, new money before taxable switches). A swap is a sale, so it carries the tax disclaimer (`SKILL.md` rule 7). End with one line:

*Not a licensed financial adviser and not personalised financial advice; the decision is yours.*

A target the user accepts is logged as a new plan (`log.md`, `data/target.json`).
