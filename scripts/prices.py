"""Prices source for anything with a ticker (stocks, ETFs, listed funds): the standard rows, from closing prices.

  python3 -I prices.py resolve <account> SYM [SYM ...]    check tickers before setup: name, type, currency, history
  python3 -I prices.py fetch <account> <dl dir>           download each holding + the index, and FRED CSVs
  python3 -I prices.py stats <account> <dl dir> YYYY-MM   fund_stats rows for a finished month
  python3 -I prices.py years <account> <dl dir>           fund_years rows (last 10 full years)
  python3 -I prices.py risk  <account> <dl dir>           data/funds.json rows with risk from volatility, ordered low -> high
  python3 -I prices.py macro <account> <dl dir> YYYY-MM   macro row: CPI year on year, policy rate, index close

Sources (free, no key, unofficial: they can change or block without notice):
  Yahoo chart  https://query1.finance.yahoo.com/v8/finance/chart/<SYM>?period1=..&interval=1d  (adjclose = dividends and splits included)
  FRED CSV     https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES>
Optional key: with ALPHAVANTAGE_API_KEY set (environment, or a line in <account>/private/keys.env), fetch takes
prices from Alpha Vantage TIME_SERIES_MONTHLY_ADJUSTED instead of Yahoo. The key is never printed or saved elsewhere.
Fallback if Yahoo fails: save <dl dir>/<CODE>.csv with columns date,adj_close,close (daily or month-end, any source),
delete <CODE>.json, and run the other commands again (they read the .csv instead).

Returns: plain %, except the cash holding (portfolio.json "cash"), which is reported as % a year (simple, x 365/days)
like a money-market fund, so the dashboard's "vs cash" maths treats it the same way. The cash holding has no benchmark.
"""
import csv, datetime as dt, json, math, os, re, statistics, sys, time, urllib.error, urllib.request

UA = {"User-Agent": "Mozilla/5.0"}
YEARS = 10
BANDS = ((5, "Low"), (15, "Medium"), (math.inf, "High"))  # annualised volatility %, SRRI classes 1-3 / 4-5 / 6-7
AV = "ALPHAVANTAGE_API_KEY"
YAHOO = "https://query1.finance.yahoo.com"


def load(account):
    j = lambda *p: json.load(open(os.path.join(account, *p), encoding="utf-8"))
    return j("portfolio.json"), j("data", "funds.json")


def api_key(account, name):
    """A provider key from the environment, else a NAME=value line in <account>/private/keys.env; None if unset."""
    if os.environ.get(name):
        return os.environ[name]
    path = os.path.join(account, "private", "keys.env")
    for line in open(path) if os.path.exists(path) else ():
        k, _, v = line.partition("=")
        if k.strip() == name and v.strip():
            return v.strip().strip("'\"")
    return None


def redact(text):
    return re.sub(r"(apikey|token)=[^&\s]*", r"\1=***", text)


def get(url, headers=None, missing_ok=False):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers or {}), timeout=30) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if missing_ok and e.code == 404:
            return None
        sys.exit(f"prices: download failed ({e}) for {redact(url)}")
    except OSError as e:  # URLError and timeouts are OSErrors too
        sys.exit(f"prices: download failed ({e}) for {redact(url)}")


def av_rows(sym, body, key=""):
    """[(date, adj_close, close)] from an Alpha Vantage TIME_SERIES_MONTHLY_ADJUSTED reply, or stop with its message."""
    try:
        d = json.loads(body)
    except ValueError:
        d = None
    d = d if isinstance(d, dict) else {}
    if not d.get("Monthly Adjusted Time Series"):
        msg = next((str(d[k]) for k in ("Error Message", "Information", "Note") if k in d), repr(body[:120]))
        sys.exit(f"prices: Alpha Vantage gave no monthly series for {sym}: {msg.replace(key, '***') if key else msg}\n"
                 f"Check the symbol and the key, or unset {AV} to use the free Yahoo source.")
    return sorted((day, float(v["5. adjusted close"]), float(v["4. close"]))
                  for day, v in d["Monthly Adjusted Time Series"].items())


def check(sym, meta, others, currency, now):
    """(funds.json draft row, problem) for one ticker. meta: Yahoo chart meta, None if not found; others: search hits."""
    near = [o for o in others if o != sym and o.split(".")[0] == sym.split(".")[0]]  # same ticker, other exchanges
    alt = f" Other listings: {', '.join(near)}." if near else ""
    if meta is None:
        return None, f"{sym}: not found.{alt or ' Check the ticker.'}"
    if meta.get("currency", "").upper() != currency.upper():  # London quotes in pence (GBp); returns are ratios, so the unit doesn't matter
        return None, f"{sym}: priced in {meta.get('currency')}, the account is in {currency}.{alt}"
    kind = meta.get("instrumentType", "?")
    first = meta.get("firstTradeDate")
    months = int((now - first) / 2629746) if first else None  # average month in seconds
    row = dict(fund=sym, name=meta.get("longName") or meta.get("shortName") or sym,
               category={"EQUITY": "Stock", "ETF": "ETF", "MUTUALFUND": "Fund"}.get(kind, kind),
               equity_share_pct=100 if kind == "EQUITY" else None, risk=None)
    return row, None if months and months >= 36 else f"{sym}: {months} months of history (< 36); its risk must be set by hand."


def resolve(cfg, syms):
    rows, problems = [], []
    for sym in syms:
        body = get(f"{YAHOO}/v8/finance/chart/{sym}?range=1d&interval=1d", UA, missing_ok=True)
        meta = json.loads(body)["chart"]["result"][0]["meta"] if body else None
        others = []
        if meta is None or meta.get("currency", "").upper() != cfg["currency"]["code"].upper():
            hits = json.loads(get(f"{YAHOO}/v1/finance/search?q={sym.split('.')[0]}&quotesCount=8&newsCount=0", UA))
            others = [q["symbol"] for q in hits.get("quotes", [])]
        row, problem = check(sym, meta, others, cfg["currency"]["code"], time.time())
        rows += [row] if row else []
        problems += [problem] if problem else []
        since = dt.date.fromtimestamp(meta["firstTradeDate"]).isoformat() if row and meta.get("firstTradeDate") else "?"
        print(f"{sym}: " + (f"{row['category']}, {meta['currency']}, {meta.get('fullExchangeName')}, listed since {since}, {row['name']}"
                            if row else "unresolved"), file=sys.stderr)
    for r in rows:
        if r["equity_share_pct"] is None:
            problems.append(f"{r['fund']}: {r['category']}, ask its share in stocks (100 stock fund, 0 cash or bonds).")
    return rows, problems


def fetch(account, cfg, funds, dl):
    os.makedirs(dl, exist_ok=True)
    start = int(time.mktime(dt.date(dt.date.today().year - YEARS - 2, 1, 1).timetuple()))
    key = api_key(account, AV)
    print(f"prices from {'Alpha Vantage (key set)' if key else 'Yahoo (free, no key)'}")
    for sym in [f["fund"] for f in funds] + [cfg["index"]["symbol"]]:
        if key:  # month-end rows saved in the fallback CSV format, which the other commands already read
            rows = av_rows(sym, get(f"https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY_ADJUSTED&symbol={sym}&apikey={key}"), key)
            with open(os.path.join(dl, f"{sym}.csv"), "w", newline="") as out:
                csv.writer(out).writerows([("date", "adj_close", "close"), *rows])
            if os.path.exists(os.path.join(dl, f"{sym}.json")):
                os.remove(os.path.join(dl, f"{sym}.json"))  # month_ends prefers the JSON, so drop a stale Yahoo file
            time.sleep(1.2)  # shortcut: free tier refuses bursts (about 1 call a second, unverified); fine for a monthly run
            continue
        url = f"{YAHOO}/v8/finance/chart/{sym}?period1={start}&period2=9999999999&interval=1d&events=div,split"
        body = get(url, UA)  # Yahoo refuses Python's default User-Agent
        try:
            ok = json.loads(body)["chart"]["result"][0]["indicators"]["adjclose"][0]["adjclose"]
        except (ValueError, KeyError, TypeError, IndexError):
            sys.exit(f"prices: Yahoo gave no price series for {sym} (blocked, renamed or wrong symbol). "
                     f"Fallback: save {dl}/{sym}.csv as date,adj_close,close from another source. Reply starts: {body[:120]!r}")
        open(os.path.join(dl, f"{sym}.json"), "wb").write(body)
    for sid in cfg.get("fred", {}).values():
        body = get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}")  # FRED refuses a bare "Mozilla/5.0"
        if not body.startswith(b"observation_date,"):
            sys.exit(f"prices: FRED gave no CSV for {sid}. Reply starts: {body[:120]!r}")
        open(os.path.join(dl, f"fred_{sid}.csv"), "wb").write(body)
    print(f"saved {len(funds) + 1} price series and {len(cfg.get('fred', {}))} FRED series to {dl}")


def month_ends(dl, sym):
    """{'YYYY-MM': (adj_close, close)} at the last trading day of each month, plus the last date seen."""
    js, cs = os.path.join(dl, f"{sym}.json"), os.path.join(dl, f"{sym}.csv")
    if os.path.exists(js):
        r = json.load(open(js))["chart"]["result"][0]
        days = zip((dt.datetime.fromtimestamp(t, dt.timezone.utc).date().isoformat() for t in r["timestamp"]),
                   r["indicators"]["adjclose"][0]["adjclose"], r["indicators"]["quote"][0]["close"])
    elif os.path.exists(cs):
        days = ((row["date"], float(row["adj_close"]), float(row["close"])) for row in csv.DictReader(open(cs)))
    else:
        sys.exit(f"prices: no {sym}.json or {sym}.csv in {dl}; run fetch first")
    out, last = {}, ""
    for d, a, c in sorted(x for x in days if x[1] is not None):
        out[d[:7]], last = (a, c), max(last, d)
    return out, last


def shift(month, n):
    y, m = divmod(int(month[:4]) * 12 + int(month[5:]) - 1 + n, 12)
    return f"{y:04d}-{m + 1:02d}"


def days_in(month):
    return (dt.date.fromisoformat(shift(month, 1) + "-01") - dt.date.fromisoformat(month + "-01")).days


def fy_base(month, fy_start):
    """Month-end before the fiscal year that `month` falls in (e.g. Dec of last year for a January start)."""
    back = (int(month[5:]) - fy_start) % 12
    return shift(month, -back - 1)


def ret(series, a, b):
    """Plain % return from month-end a to month-end b, or None if either is missing."""
    if a not in series or b not in series:
        return None
    return (series[b][0] / series[a][0] - 1) * 100


def r2(v):
    return None if v is None else round(v, 2)


def stats(cfg, funds, dl, month):
    idx, last = month_ends(dl, cfg["index"]["symbol"])
    if last[:7] <= month:
        sys.exit(f"prices: {month} is not finished in the data yet (last day seen {last})")
    base = fy_base(month, cfg["fy_start"])
    days_fy = (dt.date.fromisoformat(shift(month, 1) + "-01") - dt.date.fromisoformat(shift(base, 1) + "-01")).days
    rows = []
    for f in funds:
        s, _ = month_ends(dl, f["fund"])
        if "equity_share_pct" not in f:
            sys.exit(f"prices: set equity_share_pct for {f['fund']} in data/funds.json (100 stock or stock ETF, 0 cash or bonds)")
        cash = f["fund"] == cfg["cash"]
        m, fy = ret(s, shift(month, -1), month), ret(s, base, month)
        if m is None:
            sys.exit(f"prices: no close for {f['fund']} at the end of {month} or the month before")
        rows.append(dict(
            month=month, fund=f["fund"], nav_change_pct=r2(m),
            month_return_pct=r2(m * 365 / days_in(month) if cash else m),
            month_bench_pct=None if cash else r2(ret(idx, shift(month, -1), month)),
            month_is_annualized=cash,
            fytd_pct=r2(fy * 365 / days_fy if cash and fy is not None else fy),
            fytd_bench_pct=None if cash else r2(ret(idx, base, month)),
            ret_1y_pct=r2(ret(s, shift(month, -12), month)),
            ter_pct=f.get("ter_pct"), equity_share_pct=f["equity_share_pct"],
        ))
    return rows


def years(cfg, funds, dl):
    idx, last = month_ends(dl, cfg["index"]["symbol"])
    fs = cfg["fy_start"]
    end_of = lambda y: f"{y:04d}-{fs - 1:02d}" if fs > 1 else f"{y:04d}-12"  # a fiscal year is named by the year it ends in
    newest = max(y for y in range(int(last[:4]) - 1, int(last[:4]) + 1) if end_of(y) < last[:7])
    rows = []
    for f in funds:
        s, _ = month_ends(dl, f["fund"])
        for y in range(newest - YEARS + 1, newest + 1):
            v = ret(s, shift(end_of(y), -12), end_of(y))
            if v is not None:  # a holding's first, part year has no close a year earlier, so it is left out
                bench = None if f["fund"] == cfg["cash"] else ret(idx, shift(end_of(y), -12), end_of(y))
                rows.append(dict(fund=f["fund"], fy=y, return_pct=r2(v), bench_pct=r2(bench)))
    return rows


def risk(cfg, funds, dl):
    out = []
    for f in funds:
        s, last = month_ends(dl, f["fund"])
        months = sorted(m for m in s if m < last[:7])[-61:]  # finished months only: up to 60 returns
        rets = [s[b][0] / s[a][0] - 1 for a, b in zip(months, months[1:])]
        row = dict(f)
        if len(rets) < 36:
            print(f"prices: {f['fund']} has {len(rets)} monthly returns (< 36); risk left as {f.get('risk')}, set it by hand", file=sys.stderr)
        else:
            row["vol_pct"] = round(statistics.stdev(rets) * math.sqrt(12) * 100, 1)
            row["risk"] = next(name for cap, name in BANDS if row["vol_pct"] < cap)
        out.append(row)
    order = {"Low": 0, "Medium": 1, "High": 2}
    return sorted(out, key=lambda r: (order.get(r.get("risk"), 3), r.get("vol_pct", 0)))


def macro(cfg, dl, month):
    if "fred" not in cfg:
        sys.exit("prices: no FRED series for this country; write the macro row by hand from the official CPI and policy-rate releases.")
    def fred(key):
        sid = cfg["fred"][key]
        rows = {r["observation_date"][:7]: r[sid] for r in csv.DictReader(open(os.path.join(dl, f"fred_{sid}.csv")))}
        # A gap ("" or ".") stops the run: a null CPI would read as 0% inflation in the dashboard's maths.
        return lambda m: float(rows[m]) if rows.get(m, ".") not in ("", ".") else sys.exit(
            f"prices: FRED {sid} has no value for {m}. Take that figure from the official release (BLS / Fed) and write the macro row by hand.")
    cpi, rate = fred("cpi"), fred("policy_rate")
    idx, _ = month_ends(dl, cfg["index"]["symbol"])
    return dict(month=month, cpi_yoy_pct=r2((cpi(month) / cpi(shift(month, -12)) - 1) * 100),
                policy_rate_pct=rate(month), index_close=r2(idx[month][1]))


if __name__ == "__main__":
    # self-check on a made-up series: +1% a month for 13 months
    assert shift("2026-01", -1) == "2025-12" and shift("2025-12", 13) == "2027-01"
    assert fy_base("2026-10", 1) == "2025-12" and fy_base("2026-10", 7) == "2026-06" and fy_base("2026-06", 7) == "2025-06"
    toy = {shift("2025-01", i): (100 * 1.01 ** i, 0) for i in range(13)}
    assert abs(ret(toy, "2025-01", "2026-01") - (1.01 ** 12 - 1) * 100) < 1e-9 and ret(toy, "2024-12", "2025-01") is None
    assert [next(n for c, n in BANDS if v < c) for v in (0.3, 4.99, 5, 14.9, 15, 60)] == ["Low", "Low", "Medium", "Medium", "High", "High"]
    av = b'{"Monthly Adjusted Time Series": {"2026-10-30": {"4. close": "257.81", "5. adjusted close": "256.04"}, "2026-09-30": {"4. close": "240", "5. adjusted close": "238.5"}}}'
    assert av_rows("X", av) == [("2026-09-30", 238.5, 240.0), ("2026-10-30", 256.04, 257.81)]
    try:
        av_rows("X", b'{"Information": "rate limit for key SECRETKEY reached"}', "SECRETKEY")
        assert False
    except SystemExit as e:
        assert "rate limit" in str(e) and "SECRETKEY" not in str(e)
    assert redact("x?symbol=A&apikey=SECRET&b=1") == "x?symbol=A&apikey=***&b=1"
    t = 1_800_000_000
    ok, why = check("BABA", {"currency": "USD", "instrumentType": "EQUITY", "longName": "Alibaba", "firstTradeDate": t - 5e8}, [], "USD", t)
    assert ok["category"] == "Stock" and ok["equity_share_pct"] == 100 and why is None
    assert check("VWRL", None, ["VWRL.L", "VWRL.AS"], "USD", t) == (None, "VWRL: not found. Other listings: VWRL.L, VWRL.AS.")
    assert "priced in GBP" in check("VWRL.L", {"currency": "GBP"}, ["VWRL.AS"], "USD", t)[1]
    assert check("ISF.L", {"currency": "GBp", "instrumentType": "ETF", "firstTradeDate": t - 5e8}, [], "GBP", t)[1] is None
    assert "< 36" in check("NEW", {"currency": "USD", "instrumentType": "ETF", "firstTradeDate": t - 3e7}, [], "USD", t)[1]
    a = sys.argv[1:]
    if len(a) < 3 or a[0] not in ("resolve", "fetch", "stats", "years", "risk", "macro"):
        sys.exit(__doc__)
    cfg, funds = load(a[1]) if a[0] != "resolve" else (json.load(open(os.path.join(a[1], "portfolio.json"))), None)
    if a[0] == "resolve":
        rows, problems = resolve(cfg, a[2:])
        json.dump(rows, sys.stdout, indent=1)
        print()
        if problems:
            sys.exit("Ask the user, in one message:\n- " + "\n- ".join(problems))
    elif a[0] == "fetch":
        fetch(a[1], cfg, funds, a[2])
    else:
        out = {"stats": lambda: stats(cfg, funds, a[2], a[3]), "years": lambda: years(cfg, funds, a[2]),
               "risk": lambda: risk(cfg, funds, a[2]), "macro": lambda: macro(cfg, a[2], a[3])}[a[0]]()
        json.dump(out, sys.stdout, indent=1)
        print()
