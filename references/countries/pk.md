# Country: Pakistan (PKR)

Rules that come from where the account is held, whichever source supplies the figures.

## Conventions

- Currency PKR, symbol Rs. Large amounts are often written in lakh style (10,00,000); the pre-commit guard catches both styles.
- Fiscal year July to June (`fy_start: 7`), named by the year it ends in (FY27 = July 2026 to June 2027).
- Time zone PKT, UTC+5, no daylight saving.
- Mutual fund returns: money-market and income funds are reported as % a year (simple), equity and asset-allocation funds as plain %. True of UBL's FMR; the template treats it as the industry (MUFAP) convention, unverified against a MUFAP rule.

## Inflation and rates

- Inflation: CPI year on year from the Pakistan Bureau of Statistics (pbs.gov.pk); fund reports quote it in their market review.
- Policy rate: State Bank of Pakistan (sbp.org.pk), set at Monetary Policy Committee meetings.
- No FRED series is wired in for Pakistan; `macro.json` rows are written from the fund report (see the source file).

## Trading

- Mutual funds deal Monday to Friday, excluding Pakistan public holidays. Each fund company sets its own cut-off times (see the source file).
- Pakistan Stock Exchange trading hours and settlement cycle: not checked. Look them up on psx.com.pk before relying on them.

## Tax (estimate only)

- A redemption or a switch between funds is a sale and can incur capital gains tax (CGT) on the gain. Dividends can be taxed at source. Rates change with each year's Finance Act and differ for people on and off FBR's Active Taxpayers List; no rate is given here (unverified).
- **Voluntary Pension System (VPS):** contributions can earn a Section 63 tax credit, which only helps someone who pays income tax.
- Any figure here is an estimate only, not tax advice. Confirm with a tax professional, FBR (fbr.gov.pk) or the fund company. The skill and its author accept no liability.
