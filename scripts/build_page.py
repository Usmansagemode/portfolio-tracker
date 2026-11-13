"""Build an account's dashboard page, data/index.html, from the skill's template.

Usage: python3 -I build_page.py <account dir>

Static words (names, column headers, help text) are written here because the page follows the
Dashboard type's one-writer rule: scripts only fill data-draw elements. Rebuild after any change to
portfolio.json, the holdings list (data/funds.json), the target, or a log entry that adds or empties a holding.
Text comes from templates/text.json: "default", then the account's data source, then portfolio.json "text".
"""
import datetime, json, os, re, sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONTHS = "January February March April May June July August September October November December".split()
JS_SLOTS = ("cash", "index_name", "fy_start_day", "report", "fund", "Fund", "money_symbol")  # these also land inside JS '…' strings


def account_slots(cfg, funds, target, allocations):
    fy = cfg["fy_start"]
    assert 1 <= fy <= 12, "fy_start is a month number, 1-12"
    last = max(r["entry"] for r in allocations)
    held = {r["fund"] for r in allocations if r["entry"] == last and r["pct"] > 0}
    planned = {r["fund"] for r in target if r["pct"] > 0}
    # Year tables show what you hold now or plan to hold, in funds.json order (low → high risk).
    cols = [f for f in funds if f["fund"] in held | planned]
    start = min(r["date"] for r in allocations)
    return {
        "title": cfg["name"], "plan": cfg["plan"], "cash": cfg["cash"], "app": cfg["app"],
        "index_name": cfg["index"]["name"], "money_word": cfg["currency"]["name"], "money_symbol": cfg["currency"]["symbol"],
        "fy_start": str(fy),
        "fy_start_day": f"1 {MONTHS[fy - 1]}",
        "fy_name": "fiscal year" if fy > 1 else "year",
        "fy_end_month": MONTHS[fy - 2],
        "fy_span": f"{MONTHS[fy - 1]} to {MONTHS[fy - 2]}",
        "fy_header": f"Fiscal year ({MONTHS[fy - 1][:3]}–{MONTHS[fy - 2][:3]})" if fy > 1 else "Year",
        "start_date": datetime.date.fromisoformat(start).strftime("%-d %b %Y"),
        "fund_headers": "\n          ".join(
            f'<th data-field="{f["fund"]}"><span class="pt-code pt-risk-{f["risk"].lower()}">{f["fund"]}</span></th>' for f in cols),
    }


def fill(template, slots):
    for _ in range(3):  # text may hold slots of its own (e.g. {{fy_start_day}} inside def_since)
        template = re.sub(r"\{\{(\w+)\}\}", lambda m: slots.get(m.group(1), m.group(0)), template)
    left = sorted(set(re.findall(r"\{\{(\w+)\}\}", template)))
    if left:
        sys.exit(f"build_page: no value for {left}; add it to portfolio.json or templates/text.json")
    return template


def build(account):
    j = lambda *p: json.load(open(os.path.join(account, *p), encoding="utf-8"))
    cfg = j("portfolio.json")
    funds, target, allocations = j("data", "funds.json"), j("data", "target.json"), j("data", "allocations.json")
    missing = [f["fund"] for f in funds if f.get("risk") not in ("Low", "Medium", "High")]
    if missing:
        sys.exit(f"build_page: risk not set (Low/Medium/High) for {missing}")
    text = json.load(open(os.path.join(SKILL, "templates", "text.json"), encoding="utf-8"))
    if cfg["source"] not in text:
        sys.exit(f"build_page: no page text for source {cfg['source']!r} in templates/text.json")
    slots = {**text["default"], **text[cfg["source"]], **cfg.get("text", {}), **account_slots(cfg, funds, target, allocations)}
    bad = [k for k in JS_SLOTS if re.search(r"['\\\n]", slots[k])]
    assert not bad, f"these values go into JS strings and must not hold quotes or backslashes: {bad}"
    page = fill(open(os.path.join(SKILL, "templates", "index.html"), encoding="utf-8").read(), slots)
    open(os.path.join(account, "data", "index.html"), "w", encoding="utf-8").write(page)
    return page


if __name__ == "__main__":
    # self-check: fiscal-year words for a July start and a January start
    s7 = account_slots({"fy_start": 7, "name": "", "plan": "", "cash": "C", "app": "", "index": {"name": ""}, "currency": {"name": "", "symbol": "Rs"}},
                       [{"fund": "C", "risk": "Low"}, {"fund": "X", "risk": "High"}], [{"fund": "X", "pct": 0}],
                       [{"entry": 1, "date": "2026-11-09", "fund": "C", "pct": 100}])
    assert (s7["fy_header"], s7["fy_span"], s7["start_date"]) == ("Fiscal year (Jul–Jun)", "July to June", "9 Nov 2026")
    assert s7["fund_headers"].count("<th") == 1  # X is neither held nor planned
    assert s7["fy_end_month"] == "June"
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    build(sys.argv[1])
    print(f"wrote {os.path.join(sys.argv[1], 'data', 'index.html')}")
