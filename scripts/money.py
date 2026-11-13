"""Money view of the portfolio, from the local-only files in <account>/private/ (gitignored, chmod 600).

Run from the account folder. Prints to the terminal only. Never copy its amounts into data/, log.md,
a commit or the dashboard; those hold percentages only.

  python3 -I money.py status                    holdings, % of total, gain, tax if sold (latest date)
  python3 -I money.py snapshot                  % return between the last two dates -> row for data/snapshots.json
  python3 -I money.py move CODE=5 CODE2=1.7 [--from CODE3]   amount for each move (pts of total), tax if taken from a holding

private/holdings.csv   needs date,fund,value,to_date_gain; other columns (units, unit_price, ...) are kept but unused
private/cashflows.csv  date,fund,amount,note   (money in > 0, money out < 0; a cash dividend counts as money out)
--tax 0.20             tax rate on gains; default is portfolio.json "tax_rate_on_gains"
"""
import csv, json, os, sys
from collections import defaultdict

DISCLAIMER = ("Tax figures are an estimate only, not tax advice. Confirm with a tax professional or the tax authority. "
              "The skill and its author accept no liability.")


def read(name):
    with open(os.path.join("private", name), newline="") as f:
        return list(csv.DictReader(f))


def by_date(rows):
    out = defaultdict(dict)
    for r in rows:
        out[r["date"]][r["fund"]] = {k: float(r[k]) for k in ("value", "to_date_gain")}
    return dict(sorted(out.items()))


def period_return(v_start, v_end, new_money):
    """Money added at the start of the period: r = V_end / (V_start + new) - 1."""
    return v_end / (v_start + new_money) - 1


def amt(x):
    return f"{x:,.0f}"


def status(snaps, tax):
    date, funds = list(snaps.items())[-1]
    total = sum(f["value"] for f in funds.values())
    print(f"Holdings on {date}  (tax at {tax:.0%} of gain, estimate)")
    print(f"{'Code':8}{'Value':>14}{'Share':>8}{'Gain':>12}{'Gain %':>8}{'Tax if sold':>13}")
    for fund, f in funds.items():
        cost = f["value"] - f["to_date_gain"]
        print(f"{fund:8}{amt(f['value']):>14}{f['value'] / total:>8.1%}{amt(f['to_date_gain']):>12}"
              f"{(f['to_date_gain'] / cost if cost else 0):>8.1%}{amt(max(f['to_date_gain'], 0) * tax):>13}")
    print(f"{'Total':8}{amt(total):>14}")
    print(DISCLAIMER)


def snapshot(snaps, flows):
    dates = list(snaps)
    if len(dates) < 2:
        sys.exit("Need two dates in private/holdings.csv for a return.")
    d0, d1 = dates[-2], dates[-1]
    v0, v1 = (sum(f["value"] for f in snaps[d].values()) for d in (d0, d1))
    new = sum(float(r["amount"]) for r in flows if d0 < r["date"] <= d1)
    r = period_return(v0, v1, new)
    print(f"{d0} -> {d1}: return {r:+.2%}, new money {new / v0:+.1%} of the start value")
    print(json.dumps({"date": d1, "return_since_last_pct": round(r * 100, 3), "new_money_pct": round(new / v0 * 100, 2)}))


def move(snaps, args, tax, sym):
    src = args[args.index("--from") + 1] if "--from" in args else None
    date, funds = list(snaps.items())[-1]
    total = sum(f["value"] for f in funds.values())
    for a in (a for a in args if "=" in a):
        fund, pts = a.split("=")
        amount = total * float(pts) / 100
        line = f"{fund}: {float(pts):g} pts of the total = {sym} {amt(amount)}"
        if src:
            s = funds[src]
            line += f" from {src}, tax about {sym} {amt(amount * max(s['to_date_gain'], 0) / s['value'] * tax)}"
        print(line)
    print(f"(total on {date}: {sym} {amt(total)})")
    if src:
        print(DISCLAIMER)


if __name__ == "__main__":
    # self-check: 100 + 50 added, ending at 165 -> +10%
    assert abs(period_return(100, 165, 50) - 0.10) < 1e-12
    args = sys.argv[1:]
    if not args or args[0] not in ("status", "snapshot", "move"):
        sys.exit(__doc__)
    if not os.path.isfile("portfolio.json"):
        sys.exit("Run from the account folder (the one holding portfolio.json and private/).")
    cfg = json.load(open("portfolio.json", encoding="utf-8"))
    tax = float(args[args.index("--tax") + 1]) if "--tax" in args else cfg.get("tax_rate_on_gains", 0)
    if not tax:
        print("No tax rate set (portfolio.json tax_rate_on_gains), so tax shows as 0.")
    snaps = by_date(read("holdings.csv"))
    if args[0] == "status":
        status(snaps, tax)
    elif args[0] == "snapshot":
        snapshot(snaps, read("cashflows.csv"))
    else:
        move(snaps, args[1:], tax, cfg["currency"]["symbol"])
