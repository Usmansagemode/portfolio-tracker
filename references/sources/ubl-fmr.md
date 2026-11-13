# Source: ubl-fmr (UBL Fund Managers' monthly report)

Script: `ubl_fmr.py`. For UBL's Al-Ameen Islamic funds. Country notes: `references/countries/pk.md`. Risk: UBL's own risk profile from the FMR, set by hand in `data/funds.json`.

## Data

- **FMR** (all Islamic funds, one HTML page): `https://online.ublfunds.com/FMR/Funds/Islamic?Year=YYYY&Mon=Mmm`. WebFetch fails on this host's TLS chain; use `curl -sSL -A "Mozilla/5.0" <url> -o <scratchpad>/fmr.html`. Index of all FMRs: `https://www.ublfunds.com.pk/download/performance-reports/`.
- **Expense ratio:** use "Total Expense Ratio (FYTD)", which is annualised. The "1|3" figure is year-to-date absolute for equity funds and understates their cost.
- **Returns:** money-market and income funds report % a year; equity, asset-allocation and pension funds report plain %. Never mix the two in one comparison without labelling.
- **AIRSF (VPS pension)** is tracked as its Equity Sub-Fund (ESF). UBL rates the pension fund "allocation dependent"; tracked as ESF it counts as High risk.
- Funds pay dividends around 30 June, the end of the fiscal year.
- `ubl_fmr.py` knows UBL's fund names (its `FUNDS` table); a new fund needs a line there.

## Monthly refresh (early each month)

1. `curl` the FMR into the scratchpad, then `python3 -I $S/ubl_fmr.py <saved html> YYYY-MM`. It exits with a message if UBL changed the layout: fix the regex, not the numbers.
2. Append the rows to `data/fund_stats.json`. Add the month's CPI (year on year), month-end SBP policy rate and KSE-100 close (`index_close`) to `data/macro.json`, from the FMR's CIO note and market review.
3. From the July FMR on (a fiscal year has just closed), rebuild `data/fund_years.json` with `python3 -I $S/ubl_fmr.py --years <saved html>`. The FMR table reaches back about 10 years, so keep older rows already in the file. The script checks itself against the FMR's 5-year table and stops if they disagree.
4. Run `check_calcs.js`. Flag any standing fund fact in the account's notes that the new FMR breaks.

## UBL dealing

- Cut-off is 3:00 PM PKT (4:00 PM Fri); AICF same-day redemption is 9:30 AM PKT.
- A request before the cut-off is priced at that day's NAV, published that evening; after it, the next dealing day.
- A conversion is a redemption plus a purchase. Units usually show in 1–2 dealing days; the app's transaction status is the confirmation. Do the next step only after the source fund shows the expected balance.
- Equity funds go in by monthly transfers (UBL's Systematic Transfer Plan, STP), never as a lump sum.
- UBL's app shows an on-screen capital gains tax estimate for a redemption or switch (an estimate only, not tax advice; see the country file).
