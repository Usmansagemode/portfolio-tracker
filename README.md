# portfolio-tracker

A Claude Code skill that tracks one investment account in one currency: a log of each allocation, a target mix, monthly figures, rules-based next steps and a claude.ai dashboard. Amounts stay in a local, gitignored `private/` folder; everything else is percentages.

Install: clone this repo to `~/.claude/skills/portfolio-tracker`, then in a new empty folder ask Claude to "set up a portfolio tracker". `SKILL.md` is the entry point; `examples/us-sample/` is a filled-in sample account with invented numbers.

Requires Python 3 and Node. Prices come from free, unofficial sources (Yahoo, FRED) that can change without notice. Nothing here is financial or tax advice.
