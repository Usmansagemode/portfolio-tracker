// Usage: node check_calcs.js <account dir> [scenario]
// Runs the dashboard's calcs from <account>/data/index.html on <account>/data/*.json and prints the results.
// Stops if a log entry doesn't sum to 100%.
// checks.json (optional): {"scenarios": {"<name>": {"append": {"<dataset>": [rows]}, "replace": {"<dataset>": rows}}}}
// A scenario adds simulated rows (e.g. next month's report and a second snapshot) to test the win/lose logic.
const fs = require('fs'), path = require('path');
const acc = process.argv[2], scenario = process.argv[3];
if (!acc) throw Error('usage: node check_calcs.js <account dir> [scenario]');
const dir = path.join(acc, 'data');
const h = fs.readFileSync(path.join(dir, 'index.html'), 'utf8');
const scripts = [...h.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((m) => m[1]);
scripts.forEach((s, i) => new Function(s.replace(/\bdash\.|window\.|d3\./g, 'x.')) && null); // syntax check both
const calcs = {}; global.dash = { calc: (id, o) => (calcs[id] = o), colors: [] }; global.window = {}; global.d3 = {};
new Function(scripts[0].replace(/^window\.PT[\s\S]*?\}\)\(\);/m, ''))();
const J = (f) => JSON.parse(fs.readFileSync(f, 'utf8'));
const D = {}; for (const f of ['allocations', 'target', 'fund_stats', 'macro', 'funds', 'log_notes', 'snapshots', 'fund_years']) D[f] = J(path.join(dir, f + '.json'));
const checksFile = path.join(acc, 'checks.json');
const checks = fs.existsSync(checksFile) ? J(checksFile) : {};
if (scenario) {
  const s = (checks.scenarios || {})[scenario];
  if (!s) throw Error(`no scenario "${scenario}" in ${checksFile}`);
  for (const [k, rows] of Object.entries(s.append || {})) D[k].push(...rows);
  Object.assign(D, s.replace || {});
}
const sums = {}; for (const r of D.allocations) sums[r.entry] = (sums[r.entry] ?? 0) + r.pct;
for (const [e, t] of Object.entries(sums)) if (Math.abs(t - 100) > 0.01) throw Error(`entry ${e} sums to ${t}`);
const run = (id) => D[id] ?? (D[id] = calcs[id].fn(...calcs[id].inputs.map(run)));
for (const id of ['score', 'next', 'bench', 'actual', 'years', 'since']) console.log(id, JSON.stringify(run(id), null, 0));
