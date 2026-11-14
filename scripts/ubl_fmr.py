"""Parse one Al-Ameen Islamic FMR page into fund_stats rows (JSON on stdout).

Usage: python3 -I ubl_fmr.py <saved FMR html> <YYYY-MM>          (fund_stats rows)
       python3 -I ubl_fmr.py --years <saved FMR html>         (fund_years rows)
Download first:  curl -sSL -A "Mozilla/5.0" "https://online.ublfunds.com/FMR/Funds/Islamic?Year=2026&Mon=Oct" -o fmr.html
AIRSF is tracked as its Equity Sub-Fund (ESF) only.
"""
import html, json, re, sys

FUNDS = {
    "AICF": "AL-AMEEN ISLAMIC CASH FUND",
    "AICP-I": "AL-AMEEN ISLAMIC CASH PLAN-I",
    "AISF": "AL-AMEEN ISLAMIC SOVEREIGN FUND",
    "AIIF": "AL AMEEN ISLAMIC INCOME FUND",
    "AIAAF": "AL-AMEEN ISLAMIC ASSET ALLOCATION FUND",
    "AIEF": "AL-AMEEN ISLAMIC ENERGY FUND",
    "ASSF": "AL-AMEEN SHARIAH STOCK FUND",
}
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
P = r"(-?[\d.]+)%"


def text_of(path):
    t = open(path, encoding="utf-8", errors="ignore").read()
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))


def need(pat, s, what):
    m = re.search(pat, s)
    if not m:
        sys.exit(f"FMR layout changed: could not find {what}")
    return m


def parse(t, month):
    mon = MONTHS[int(month[5:]) - 1]
    head = f"Fund Managers Report - {mon} {month[:4]}"
    rows = []
    for code, name in FUNDS.items():
        i = t.find(f"{name} {head}")
        if i < 0:
            sys.exit(f"{code}: section not found for {mon}")
        s = t[i : i + 7000]
        m = need(rf"{mon} {month[:4]} (\(p\.a\.\) )?{P} {P}", s, f"{code} month return")
        fy = need(rf"FY-YTD (\(p\.a\.\) )?{P} {P}", s, f"{code} FYTD")
        rv = need(rf"Return Vs Benchmark % 3 Months 6 Months 1 Year .*? \S+ (\(p\.a\.\) )?{P} {P} {P}", s, f"{code} 1Y")
        eq = re.search(rf"Equities {P} {P}", s)
        rows.append(dict(
            month=month, fund=code,
            nav_change_pct=float(need(rf"NAV \(PKR\) [\d.]+ [\d.]+ {P}", s, f"{code} NAV").group(1)),
            month_return_pct=float(m.group(2)), month_bench_pct=float(m.group(3)),
            month_is_annualized=bool(m.group(1)),
            fytd_pct=float(fy.group(2)), fytd_bench_pct=float(fy.group(3)),
            ret_1y_pct=float(rv.group(4)),
            ter_pct=float(need(rf"Total Expense Ratio \(FYTD\) 2\|3 {P}", s, f"{code} TER").group(1)),
            equity_share_pct=float(eq.group(2)) if eq else 0.0,
        ))
    # AIRSF: three sub-funds side by side (DSF, MMSF, ESF); ESF is the third value.
    i = t.find(f"Al-Ameen Islamic Retirement Savings Fund {head}")
    if i < 0:
        sys.exit("AIRSF: section not found")
    s = t[i : i + 9000]
    three = lambda pat, what: float(need(pat + rf" {P} {P} {P}", s, what).group(3))
    rows.append(dict(
        month=month, fund="AIRSF",
        nav_change_pct=float(need(rf"Fund Size — ESF .*?NAV \(PKR\) [\d.]+ [\d.]+ {P}", s, "ESF NAV").group(1)),
        month_return_pct=three(rf"{mon} {month[:4]} \(p\.a\.\)", "ESF month"),
        month_bench_pct=float(need(rf"{mon} {month[:4]} \(p\.a\.\) {P} {P} {P} Benchmark {P} {P} {P}", s, "ESF bench").group(6)),
        month_is_annualized=False,
        fytd_pct=three(r"FY-YTD \(p\.a\.\)", "ESF FYTD"),
        fytd_bench_pct=three(r"Benchmark FY-YTD", "ESF FYTD bench"),
        ret_1y_pct=float(need(rf"ESF ² {P} {P} {P}", s, "ESF 1Y").group(3)),
        ter_pct=three(r"Total Expense Ratio \(FYTD\) 2\|3", "ESF TER"),
        equity_share_pct=float(need(rf"ESF Asset Type .*?Equities {P} {P}", s, "ESF equities").group(2)),
    ))
    return rows


def cum_tables(t, start, end, ncol):
    """{code: {fy: (fund %, bench % or None)}} from one 'X vs Benchmark' table block of the FMR."""
    s = t[t.index(start) : t.index(end, t.index(start))]
    out = {}
    for code in FUNDS.keys() | {"AIRSF"}:
        name = "AIRSF-ESF" if code == "AIRSF" else code
        m = re.search(rf"(?<![\w-]){re.escape(name)} vs Benchmark \(Fund return in top row\) ((?:FY'\d\d ){{{ncol}}})((?:\S+ ){{{2 * ncol}}})", s)
        if not m:
            sys.exit(f"FMR layout changed: no yearly table for {code}")
        fys = [2000 + int(y[3:]) for y in m.group(1).split()]
        v = [None if x == "-" else float(x.rstrip("%")) for x in m.group(2).split()]
        out[code] = {fy: (v[i], v[ncol + i]) for i, fy in enumerate(fys) if v[i] is not None}
    return out


def years(t):
    """Yearly return per fiscal year, from the since-inception absolute table: (1+C_t)/(1+C_t-1) - 1."""
    cum = cum_tables(t, "Since Inception Absolute Returns", "Since Inception Annualized Return", 10)
    g = lambda a, b: None if a is None or b is None else round(((100 + a) / (100 + b) - 1) * 100, 2)
    rows = [dict(fund=code, fy=fy, return_pct=g(c[fy][0], c[fy - 1][0]), bench_pct=g(c[fy][1], c[fy - 1][1]))
            for code, c in sorted(cum.items()) for fy in sorted(c) if fy - 1 in c]  # first (part) year skipped
    # self-check against the FMR's own last-5-years table (rounded to 0.1%)
    five = cum_tables(t, "Yearly returns for the last five fiscal years", "Since Inception Absolute Returns", 5)
    for r in rows:
        rep = five.get(r["fund"], {}).get(r["fy"])
        assert rep is None or abs(rep[0] - r["return_pct"]) < 0.25, (r, rep)
    return rows


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    if sys.argv[1] == "--years":  # python3 -I ubl_fmr.py --years <saved html>  -> fund_years rows
        json.dump(years(text_of(sys.argv[2])), sys.stdout, indent=1)
        sys.exit()
    rows = parse(text_of(sys.argv[1]), sys.argv[2])
    assert len(rows) == len(FUNDS) + 1 and all(-50 < r["nav_change_pct"] < 50 for r in rows)
    json.dump(rows, sys.stdout, indent=1)
