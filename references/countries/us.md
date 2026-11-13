# Country: United States (USD)

Rules that come from where the account is held, whichever source supplies the figures.

## Conventions

- Currency USD, symbol $. Calendar tax year (`fy_start: 1`).
- Cash comparison: a T-bill ETF (e.g. SGOV) is a sensible default; benchmark: a broad-market ETF (e.g. SPY for the S&P 500).

## Inflation and rates

- `portfolio.json` `fred`: `{"cpi": "CPIAUCSL", "policy_rate": "FEDFUNDS"}`. CPIAUCSL is the CPI index (year on year = this month ÷ same month last year − 1); FEDFUNDS is the effective federal funds rate, monthly average.
- FRED publishes CPI about two weeks after the month. CPIAUCSL has no October 2025 value: take the 12-month change from the BLS CPI release (bls.gov/cpi) and write that macro row by hand.

## Trading

- Regular market hours are 9:30 AM–4:00 PM Eastern, Mon–Fri, excluding exchange holidays. Most US stock and ETF trades settle T+1 (one business day).
- Risky holdings go in by monthly steps (e.g. a fixed transfer from the cash holding each month), never as a lump sum.

## Tax (general federal rules, unverified for the user's situation)

- Selling at a gain is taxable. Held one year or less: short-term, taxed as ordinary income. Held over a year: long-term, at 0%, 15% or 20% depending on income. A 3.8% net investment income tax can apply above income thresholds. State tax may add more.
- Dividends: qualified dividends at long-term rates, others as ordinary income. Non-US residents usually have tax withheld on US dividends at source (often 30%, lower under a tax treaty).
- Wash sale rule: a loss is disallowed if the same or a substantially identical security is bought within 30 days before or after the sale.
- Tax-advantaged accounts: moves inside an IRA or 401(k) are not taxed at the time.
- Any figure here is an estimate only, not tax advice. Confirm with a tax professional or the IRS (or the user's own tax authority). The skill and its author accept no liability.
