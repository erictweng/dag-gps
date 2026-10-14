#!/usr/bin/env node
'use strict';
// Same corrected, frozen grid; compare this card's base against the current service.
const fs = require('node:fs'), path = require('node:path'), crypto = require('node:crypto');
const {execFileSync} = require('node:child_process'), {performance} = require('node:perf_hooks');
const {generate, classify, counts, timing} = require('./bench_variations.cjs');
const root = path.resolve(__dirname, '..'), out = path.join(root, 'artifacts/parser-collisions');
const read = p => JSON.parse(fs.readFileSync(p)), sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const configBytes = fs.readFileSync(path.join(root, 'eval/variation_templates.json')), config = JSON.parse(configBytes);
const before = path.join(out, 'base'); fs.mkdirSync(before, {recursive: true});
execFileSync('tar', ['-xf', '-', '-C', before], {input: execFileSync('git', ['archive', '08f1b4d', 'web'], {cwd: root})});
const repeats = Number(process.env.COLLISION_REPEATS || 3);
const report = {base: '08f1b4d597d64bbd7557953f54139161d3e6864d', head: execFileSync('git', ['rev-parse', 'HEAD']).toString().trim(),
  serviceSha256: sha(fs.readFileSync(path.join(root, 'web/query-service.js'))), seed: config.seed,
  templatesSha256: sha(configBytes), repeats, warmup: 200, repos: {}};
for (const repo of ['honcho', 'salesroom']) {
  const snapshotPath = path.join(root, 'artifacts/question-parser', repo, 'snapshot.json');
  const bytes = fs.readFileSync(snapshotPath);
  if (sha(bytes) !== config.repos[repo].snapshotSha256) throw Error('Frozen snapshot changed');
  const snapshot = JSON.parse(bytes), rows = generate(config, repo, snapshot);
  const all = [...snapshot.map.nodes, ...(snapshot.map.symbol_graph?.nodes || [])], names = new Map();
  for (const n of all) {
    const name = (n.kind === 'symbol' ? n.name : n.kind === 'file' ? path.posix.basename(n.path).replace(/\.[^.]+$/, '') : n.label?.split('/').at(-1))?.toLowerCase();
    if (!name) continue;
    if (!names.has(name)) names.set(name, []);
    names.get(name).push(n);
  }
  const collisions = new Set([...names.values()].filter(ns => new Set(ns.map(n => n.kind)).size > 1).flatMap(ns => ns.map(n => n.id)));
  const versions = {};
  for (const [version, codeRoot] of [['before', before], ['after', root]]) {
    const service = require(path.join(codeRoot, 'web/query-service.js')).createQueryService(snapshot);
    const scorer = require(path.join(codeRoot, 'web/scorer.js')).createScorer(snapshot.map);
    const order = [...rows].sort((a, b) => sha(config.seed + a.id).localeCompare(sha(config.seed + b.id)));
    for (const r of order.slice(0, 200)) service.query({requestId: r.id, query: r.question});
    const results = new Map();
    for (let repeat = 0; repeat < repeats; repeat++) for (const r of order) {
      const start = performance.now(), p = service.query({requestId: r.id, query: r.question}), ms = performance.now() - start;
      if (!repeat) {
        const op = p.operation === 'NOT_SURE' && p.status === 'needs-choice' ? scorer.score(r.question).requestedOperation : p.operation;
        results.set(r.id, {...r, outcome: classify(r, p, op), status: p.status, actualOperation: p.operation,
          selected: p.seedNodeId ? [p.seedNodeId] : p.selectedNodeIds.slice(0, 2), alternatives: p.alternatives.map(a => a.nodeId), ms: [ms]});
      } else results.get(r.id).ms.push(ms);
    }
    const raw = rows.map(r => results.get(r.id)); versions[version] = raw;
    fs.writeFileSync(path.join(out, repo + '-' + version + '.jsonl'), raw.map(r => JSON.stringify(r)).join('\n') + '\n');
    const dataset = path.join(root, 'eval', repo === 'honcho' ? 'question_parser.json' : 'question_parser_salesroom.json');
    const frozenOut = path.join(out, repo + '-frozen-' + version + '.json');
    execFileSync(process.execPath, [path.join(root, 'scripts/eval_question_parser.cjs'), snapshotPath, frozenOut,
      version === 'after' ? path.join(out, repo + '-frozen-before.json') : '', dataset, path.join(codeRoot, 'web/query-service.js')]);
    console.log(repo, version, counts(raw.filter(r => !r.negative)));
  }
  const a = versions.before, b = versions.after;
  const summary = predicate => {
    const indices = a.map((r, i) => predicate(r) ? i : -1).filter(i => i >= 0);
    return {before: counts(indices.map(i => a[i])), after: counts(indices.map(i => b[i])),
      confidentToChoice: indices.filter(i => a[i].status === 'matched' && b[i].status === 'needs-choice').length,
      correctToChoice: indices.filter(i => a[i].outcome === 'correct' && b[i].status === 'needs-choice').length,
      newWrong: indices.filter(i => b[i].outcome === 'wrong' && a[i].outcome !== 'wrong').length};
  };
  const axes = [...new Set(a.map(r => r.axis + ':' + r.value))];
  report.repos[repo] = {gridSha256: sha(JSON.stringify(rows)), total: summary(r => !r.negative),
    negatives: summary(r => r.negative), collisionTargetOperations: Object.fromEntries([...new Set(a.map(r => r.operation))].map(op =>
      [op, summary(r => !r.negative && r.operation === op && r.targets.some(id => collisions.has(id)))])),
    operation: Object.fromEntries([...new Set(a.map(r => r.operation))].map(op => [op, summary(r => !r.negative && r.operation === op)])),
    axes: Object.fromEntries(axes.map(axis => [axis, summary(r => r.axis + ':' + r.value === axis)])),
    latency: {before: timing(a.flatMap(r => r.ms)), after: timing(b.flatMap(r => r.ms))},
    frozen: Object.fromEntries(['before', 'after'].map(v => [v, read(path.join(out, repo + '-frozen-' + v + '.json')).splits])),
    newWrongExamples: b.filter((r, i) => r.outcome === 'wrong' && a[i].outcome !== 'wrong').slice(0, 30)};
}
fs.writeFileSync(path.join(out, 'summary.json'), JSON.stringify(report, null, 2) + '\n');
// A separately labeled counterexample supplement: do not add or relabel grid rows.
// These two concrete collision names were not selected as every operation's target
// by the original frozen grid. Keep that coverage limitation visible.
const supplementPatterns = ['where is {x}', 'what uses {x}', 'what does {x} use',
  'dependents of {x}', 'dependencies of {x}', 'downstream of {x}', 'upstream of {x}',
  'who invokes {x}', 'callers of {x}', 'what does {x} call', 'callees of {x}', 'trace from {x}',
  'path from {x} to {y}', 'path from {y} to {x}', 'how does {x} reach {y}', 'how does {y} reach {x}'];
const supplemental = {};
for (const repo of ['honcho', 'salesroom']) {
  const snapshot = read(path.join(root, 'artifacts/question-parser', repo, 'snapshot.json'));
  const old = require(path.join(before, 'web/query-service.js')).createQueryService(snapshot);
  const current = require(path.join(root, 'web/query-service.js')).createQueryService(snapshot);
  const name = repo === 'honcho' ? 'backfill' : 'events';
  const other = repo === 'honcho' ? 'src/reconciler/backfill.py' : 'src/lib/events.ts';
  const packets = [];
  supplemental[repo] = supplementPatterns.map(phrase => {
    const query = phrase.replace('{x}', name).replace('{y}', other), request = {requestId: 'supplement', query};
    const a = old.query(request), b = current.query(request); packets.push(b);
    for (const alt of b.alternatives) {
      packets.push(current.query({...request, chosenNodeId: alt.nodeId}));
      packets.push(current.query({...request, query: alt.query, chosenNodeId: alt.nodeId}));
    }
    return {query, before: {status: a.status, operation: a.operation}, after: {status: b.status, operation: b.operation},
      confidentToChoice: a.status === 'matched' && b.status === 'needs-choice'};
  });
  fs.writeFileSync(path.join(out, repo + '-packets.json'), JSON.stringify(packets) + '\n');
}
const compact = structuredClone({...report, supplemental});
for (const r of Object.values(compact.repos)) { delete r.axes; delete r.newWrongExamples; }
fs.writeFileSync(path.join(root, 'eval/parser_collision_results.json'), JSON.stringify(compact, null, 2) + '\n');
for (const [repo, r] of Object.entries(report.repos)) {
  console.log(repo, JSON.stringify({total: r.total, latency: r.latency, frozen: r.frozen}));
  if (r.total.newWrong || r.negatives.after.overconfident > r.negatives.before.overconfident)
    process.exitCode = 1;
}
