---
name: portfolio-tracker
description: Tracks one investment account in one currency with any holdings (mutual funds, stocks, ETFs). Keeps a portfolio log and target mix, fetches monthly figures, gives rules-based next steps (target mix, drift, buying in steps), recommends specific holdings only when asked, estimates tax with a disclaimer, and builds a claude.ai dashboard that is published only on request. Amounts stay in a local gitignored private/ folder; everything else is percentages. Triggers: /portfolio-tracker, set up a portfolio tracker, track my portfolio, new allocation, holdings screenshot, rebalance, new monthly figures, update the tracker, publish the dashboard.
---

# Portfolio tracker

One account, one currency, one folder. Each account folder is independent and gets its own dashboard artifact. Several accounts or currencies in one tracker are out of scope: use a folder per account.

## Account folder

```
portfolio.json       account settings (keys in references/files.md)
CLAUDE.md            the account's own facts: mandate, plan notes, standing facts about its holdings, timing. Read it first, every run.
log.md               Portfolio History Log and the agreed target. Read it next.
checks.json          known calc values and test scenarios for check_calcs.js
data/*.json          the datasets the dashboard reads (schemas in references/files.md)
data/index.html      dashboard page, built by build_page.py. Never edit it by hand.
data/published.json  what the dashboard currently holds (written at publish)
private/             amounts: holdings.csv, cashflows.csv; optional keys.env (API keys). Gitignored, folder 700, files 600.
```

**Source and country:** `portfolio.json` names both. Read `references/sources/<source>.md` before any data refresh (where the numbers come from, its script, how risk is rated) and `references/countries/<country>.md` before any advice or tax figure (currency, inflation series, trading, tax).
- Sources: `prices` (anything with a ticker; free Yahoo + FRED, or Alpha Vantage with a key), `ubl-fmr` (UBL's monthly fund report). Every source writes the same rows. New one: `references/adding-a-source.md`.
- Countries: `pk`, `us`. Others work without a file: say tax and inflation notes are unverified, and offer to write one (`references/adding-a-country.md`). `country` only routes Claude to that file; no script reads it.

## Scripts

`S=~/.claude/skills/portfolio-tracker/scripts`. Run them from the account folder (`.` = the account).

| Script | Does |
|---|---|
| `python3 -I $S/build_page.py .` | Writes `data/index.html` from `templates/index.html` + `templates/text.json` + `portfolio.json` + `data/funds.json`. After any change: `build_page.py`, then `check_calcs.js`. |
| `node $S/check_calcs.js . [scenario]` | Runs the page's calcs on `data/*.json` and prints them. Stops if an entry doesn't sum to 100%. Run after any change to `data/` or the page. |
| `python3 -I $S/money.py status\|snapshot\|move` | Amounts view from `private/`: holdings, gain, tax if sold; % return between the last two snapshots; amount per transfer. Terminal only. |
| `python3 -I $S/ubl_fmr.py` | `ubl-fmr` source: one saved FMR page → `fund_stats` rows (`--years`: `fund_years` rows). |
| `python3 -I $S/prices.py resolve\|fetch\|stats\|years\|risk\|macro` | `prices` source: checks tickers, then closing prices and FRED series → the same rows, risk from volatility, macro row. |
| `$S/pre-commit` | Git hook: refuses `private/` and `*.env` files and amounts in the account's currency. |

Templates: `templates/index.html` (the page, with `{{slots}}`) and `templates/text.json` (wording: `default`, then per source, then `portfolio.json` `"text"` overrides). The page follows the Dashboard type's one-writer rule: static words live in the HTML and scripts only fill `data-draw` elements, which is why names and fund columns are written at build time.

## Dashboard

Its job is to answer "am I doing well, and what next?". Page order: summary line (progress to target, equity %) and the latest `next` step; three tiles (growth since start, vs leaving it all in the cash holding, vs inflation); What to do (now, target, action); Now vs target; then the evidence: growth chart, year by year, total gain since each fiscal-year start, allocation history, log.
- Growth uses actual snapshots once two exist, and the estimate from monthly returns × % before that. No Winning/Losing verdict before 12 months, then only beyond ±1 point, because shares swing about ±3 points a month against cash.
- Every section heading has a ? button (native `popover`, static HTML) saying what it shows, how to read it and why it matters. When a section's meaning or data changes, update its help text in the same edit (in the template or `templates/text.json`) and check any figure it quotes against the data.
- The page follows the reader's claude.ai theme (light or dark); every colour is a host token. Optional: if a design linter is installed, run it on `data/index.html` after a change to the page's look.

## Rules

1. **Amounts only in `private/`, and only as the user chose.** `data/`, `log.md` and commits always hold percentages only. `portfolio.json` `amounts` is the user's choice: `"none"` (percentages only; nothing in `private/`), `"private"` (holdings screenshots and deposits go to `private/holdings.csv` and `private/cashflows.csv`; amounts shown in chat only when asked) or `"dashboard"` (as `"private"`, plus totals on the page from `private/amounts.json`, uploaded at publish: `references/publishing.md`, "Amounts"). Missing means `"none"`. API keys live only in an environment variable or `private/keys.env`, which the user writes; never read, print or copy a key, and never read other `.env` files or credentials.
2. **Local first.** Every update is written to the account folder. The dashboard changes only when the user says "publish" (`references/publishing.md`). End other updates with: "Dashboard not yet updated, say publish."
3. **Allocations sum to 100% (±0.01).** If they don't, ask before logging.
4. **Numbers over words.** Lead with a table: `Code | Now % | Target % | Do | Why (one number)`. "Why" is one figure, e.g. "+0.9%/yr vs cash", "−9.9% FYTD". A line or two of prose at most.
5. **Live data before advice.** Use the latest monthly figures, inflation and policy rate. Cite the source; say when a figure is unverified.
6. **Advice is rules-based by default:** the target mix, drift from it, buying in steps, and the one next concrete step (date, code, points, from which holding). A holding within 0.5 pts of target is on target: hold. Once the target is reached, rebalance only when a holding drifts 5 pts or more from it, using new money first. Risky holdings go in by monthly steps, not as a lump sum. No price forecasts or market timing. Say once per audit, in one line, that this is not licensed financial advice.
   **When the user asks what to hold, add or swap**, recommend specific holdings or a target mix for their goal, horizon and constraints, following `references/recommending.md`: every figure fetched or checked, never invented, and one line saying it is not a licensed adviser's or personalised advice and the user decides.
7. **Tax.** A move between holdings is a sale, so it can be taxed; new money avoids that. Every tax figure or tax rule given (in chat, `money.py` output or dashboard help) carries this, in substance: *"Estimate only, not tax advice. Confirm with a tax professional or the tax authority. The skill and its author accept no liability."* `portfolio.json` `tax_rate_on_gains` is a flat estimate, not a tax calculation.
8. **Risk order.** `data/funds.json` lists holdings low → high risk (Low ● ok, Medium ◆ warn, High ▲ bad; within a level, steadier first). That order sets order and colours everywhere on the dashboard; keep it when adding a holding.

## Set up a new account

1. Ask once, in one message, for everything: account name, currency, country, the holdings (any tickers or funds) with current % or amounts, the target % per holding, the cash holding, the benchmark, plan and horizon, a flat tax rate on gains (an estimate), and how to track: percentages only, or amounts too (kept local, or local plus totals on the dashboard). Say this can be changed later. Pick the source from the holdings. Offer defaults to accept, from the country file if there is one (e.g. a T-bill ETF as cash, a broad-market ETF as benchmark).
2. Create the folder with `git init`, a `.gitignore` holding `private/` and `*.env`, `mkdir -m 700 private`, and the hook: `ln -sf $S/pre-commit .git/hooks/pre-commit`. Write `portfolio.json`, and a short `CLAUDE.md` saying the folder is an account of this skill, with the rules above and any account facts the user gives.
3. For `prices`, run `prices.py resolve` on the holdings, the cash holding and the benchmark (`references/sources/prices.md`); it lists what it can't settle. Ask the user about those.
4. Write `portfolio.json` `amounts` from that answer, then `data/funds.json` (from the resolver's draft rows), `data/allocations.json` (entry 1), `data/target.json`, `data/log_notes.json`, `data/snapshots.json` (first row `return_since_last_pct: null`) and log entry #01 in `log.md`. If the user chose amounts and gave them, write them to `private/holdings.csv` (`chmod 600`), compute each holding's % from it, and store only the %. With `"none"`, use any amounts given only to compute the %, and keep nothing.
5. Load the figures as the source file says, then `build_page.py`, then `check_calcs.js`.
6. Create the dashboard only when the user says "publish": `references/publishing.md`, "First publish".

**New source or country:** `references/adding-a-source.md`, `references/adding-a-country.md`.

**Worked example:** `examples/us-sample/` is a made-up US account (`prices` source) with every file filled in; its numbers are invented, not anyone's holdings.

## When the user reports a new allocation

1. Check that it sums to 100%. A new ticker goes through `prices.py resolve` first.
2. Append a log entry to `log.md` (format below), the rows to `data/allocations.json`, and a note to `data/log_notes.json` with the same entry number and a `next` field.
3. Rewrite each `data/target.json` `action` as that holding's next concrete step, naming the source holding for any transfer. A holding within 0.5 pts of target shows "On target: hold" by itself.
4. Run `build_page.py`, then `check_calcs.js`.
5. Reply with `Code | Before | After | Target | Still to move`, progress toward target, the next step, and a one-line verdict.

## When the user shares a holdings screenshot (snapshot)

Ask for one after each trade settles, and once a month. It must show every holding's current value.

With `amounts: "none"`: compute each holding's % from the screenshot and keep no amount. For the return, ask for the % change the app shows since the last snapshot and whether money was added or withdrawn (as % of the portfolio), then do steps 3 and 4.

1. Append each holding's row to `private/holdings.csv` and any deposit, withdrawal or cash dividend since the last snapshot to `private/cashflows.csv`. Compute each holding's %. If any differs from the last log entry by more than 0.5 pts, or a trade happened, add a log entry (rationale "Snapshot", or the trade).
2. Ask whether money was added or withdrawn and whether a dividend was paid out in cash (it counts as a withdrawal). Run `money.py snapshot`: `r = V_end / (V_start + new_money) − 1`, new money assumed to land at the start of the period.
3. Append its row to `data/snapshots.json`. Reply in %; add amounts only if asked.
4. Run `check_calcs.js` and show the `score` rows (growth, vs cash, vs inflation).

## When the user changes the amounts choice

Set `portfolio.json` `amounts` and say what changes. Percentage history is never touched.
- **To `"private"` or `"dashboard"`:** `mkdir -m 700 private`; amounts start from the next holdings screenshot (`money.py snapshot` needs two dated snapshots for a return; earlier returns stay as logged). For `"dashboard"`, the "Your money" block appears at the next publish.
- **From `"dashboard"` to `"private"` or `"none"`:** at the next publish, delete the `datasets/amounts` document and its blob, and remove `amounts` from `data/published.json`; the block hides itself. Do it now if the user says publish.
- **To `"none"`:** ask whether to delete `private/holdings.csv`, `cashflows.csv` and `amounts.json` or keep them; never delete them without a yes.

## When new monthly figures are out

Follow the source file's refresh steps, append the rows, run `check_calcs.js`, and reply with a short table of what changed (month return, year-to-date vs benchmark) plus any action it triggers. Don't publish.

## Log entry format

```text
[LOG ENTRY #XX] - Date: YYYY-MM-DD
--------------------------------------------------
- Previous Allocation: [List previous percentages]
- New Allocation:      [List new percentages]
- User Rationale:      [Reason provided by user]
- Strategic Verdict:   [Advisor evaluation of the change]
--------------------------------------------------
```
