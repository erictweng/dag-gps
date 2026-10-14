#!/usr/bin/env node
'use strict';
// Measurement only: frozen construction labels never consult a query result.
const fs = require('node:fs'), path = require('node:path'), os = require('node:os');
const crypto = require('node:crypto'), {performance} = require('node:perf_hooks');
const {execFileSync} = require('node:child_process');
const ROOT = path.resolve(__dirname, '..'), OUT = path.join(ROOT, 'artifacts/variation-benchmark');
const sha = x => crypto.createHash('sha256').update(x).digest('hex');
const read = p => JSON.parse(fs.readFileSync(p));
const write = (p, x) => fs.writeFileSync(p, JSON.stringify(x, null, 2) + '\n');
const success = r => ['correct', 'choose-correct'].includes(r.outcome);

function forms(t, config) {
  const text = t.kind === 'symbol' ? t.id : t.path || t.label;
  const values = [[t.kind === 'symbol' ? 'symbol-id' : 'full-path', text]];
  if (t.kind === 'symbol') values.push(['symbol-name', t.name], ['qualified-name', t.qualname]);
  else {
    const base = path.posix.basename(text), stem = base.replace(/\.[^.]+$/, '');
    values.push([t.kind === 'layer' ? 'folder-name' : 'basename', base], ['stem', stem]);
    for (const group of config.synonyms) if (group.includes(stem))
      for (const word of group) if (word !== stem) values.push(['synonym:' + word, word]);
  }
  return values;
}
function generate(config, repo, snapshot) {
  const rows = [], spec = config.repos[repo];
  const add = row => rows.push({id: repo + '-' + rows.length, negative: false, ...row});
  const mutations = [['case', 'lower', x => x.toLowerCase()], ['case', 'Title', x => x.replace(/\b[a-z]/g, c => c.toUpperCase())],
    ['case', 'UPPER', x => x.toUpperCase()], ['punctuation', '?', x => x], ['punctuation', '.', x => x],
    ...config.fillers.map(v => ['filler', v, x => v === 'the' ? 'the ' + x : x + ' ' + v]),
    ...config.kinds.map(v => ['kind', v, x => v + ' ' + x]), ['typo', 'one-insertion', x => x + 'z']];
  for (const t of spec.targets) {
    const ops = t.kind === 'symbol' ? ['LOCATE', 'CALLERS', 'CALLEES', 'TRACE'] : ['LOCATE', 'UPSTREAM', 'DOWNSTREAM'];
    const ff = forms(t, config);
    for (const operation of ops) for (const phrase of config.phrases[operation]) {
      const base = {targets: [t.id], operation, phrase, kind: t.kind};
      for (const [form, value] of ff) add({...base, axis: 'target-form', value: form, form,
        question: phrase.replace('{x}', value)});
      for (const [axis, value, apply] of mutations) {
        const form = ff[0][0], x = apply(ff[0][1]);
        const hintKind = ['file', 'module', 'script'].includes(value) ? 'file' :
          ['folder', 'directory', 'dir', 'package'].includes(value) ? 'layer' : 'symbol';
        add({...base, axis, value, form, kindAgreement: axis === 'kind' ? (hintKind === t.kind ? 'matching' : 'mismatching') : null,
          question: phrase.replace('{x}', x) + (axis === 'punctuation' ? value : '')});
      }
    }
  }
  for (const pair of spec.pairs) for (const phrase of config.phrases[pair.operation]) {
    const base = {targets: [pair.from, pair.to], operation: pair.operation, phrase, kind: 'pair', form: 'full-path'};
    add({...base, axis: 'target-form', value: 'full-path', question: phrase.replace('{x}', pair.a).replace('{y}', pair.b)});
    for (const [axis, value, apply] of mutations) add({...base, axis, value,
      question: phrase.replace('{x}', apply(pair.a)).replace('{y}', apply(pair.b)) + (axis === 'punctuation' ? value : '')});
  }
  const known = [...snapshot.map.nodes, ...(snapshot.map.symbol_graph?.nodes || [])];
  const knownText = new Set(known.flatMap(n => [n.id, n.path, n.label, n.name, n.qualname]).filter(Boolean).map(x => x.toLowerCase()));
  for (let i = 0; i < 240; i++) {
    const category = ['absent-concept', 'nonsense', 'near-miss'][i % 3];
    const token = sha(config.seed + repo + i).slice(0, 12);
    const name = category === 'near-miss' ? path.posix.basename(spec.targets[i % spec.targets.length].path || spec.targets[i % spec.targets.length].label) + '_absent_' + token :
      (category === 'absent-concept' ? 'teleportation antimatter ' : 'qzxv ') + token;
    if (knownText.has(name.toLowerCase())) throw Error('Negative exists');
    add({negative: true, targets: [], operation: 'LOCATE', phrase: 'where is {x}', kind: 'negative', form: category,
      axis: 'negative', value: category, question: 'where is ' + name});
  }
  const labels = new Map();
  for (const r of rows.filter(r => !r.negative)) {
    if (!labels.has(r.question)) labels.set(r.question, new Set());
    labels.get(r.question).add(JSON.stringify([r.operation, r.targets]));
  }
  for (const r of rows) r.constructionStratum = r.negative ? 'negative' :
    r.kindAgreement === 'mismatching' ? 'mismatching-kind' :
      labels.get(r.question).size > 1 ? 'ambiguous' : 'unambiguous';
  return rows;
}
function classify(row, packet, choiceOperation) {
  if (row.negative) return packet.status === 'matched' ? 'overconfident' : packet.status === 'no-match' ? 'no-match' : 'unresolved';
  const ids = packet.seedNodeId ? [packet.seedNodeId] : (packet.selectedNodeIds || []).slice(0, 1);
  const right = row.targets.length === 1 ? ids[0] === row.targets[0] :
    (packet.witnesses || []).some(w => w.nodeIds[0] === row.targets[0] && w.nodeIds.at(-1) === row.targets[1]);
  if (packet.status === 'matched') return right && packet.operation === row.operation ? 'correct' : 'wrong';
  if (packet.status === 'needs-choice' && (packet.operation === row.operation ||
      (packet.operation === 'NOT_SURE' && choiceOperation === row.operation)) &&
      row.targets.every(id => (packet.alternatives || []).some(a => a.nodeId === id))) return 'choose-correct';
  return packet.status === 'no-match' ? 'no-match' : 'unresolved';
}
function timing(values) {
  const a = [...values].sort((x, y) => x - y), n = a.length;
  if (!n) return {n: 0};
  const mean = a.reduce((s, x) => s + x, 0) / n;
  return {n, p50: a[Math.ceil(n * .5) - 1], p95: a[Math.ceil(n * .95) - 1], p99: a[Math.ceil(n * .99) - 1], max: a[n - 1], mean,
    stddev: Math.sqrt(a.reduce((s, x) => s + (x - mean) ** 2, 0) / n)};
}
function counts(rows) {
  const out = {total: rows.length};
  for (const k of ['correct', 'choose-correct', 'wrong', 'no-match', 'unresolved', 'overconfident']) out[k] = rows.filter(r => r.outcome === k).length;
  out.correctPct = 100 * out.correct / (rows.length || 1);
  out.successPct = 100 * rows.filter(success).length / (rows.length || 1);
  out.distinctSuccessful = new Set(rows.filter(success).map(r => r.question)).size;
  return out;
}
function grouped(rows, key, summarize) {
  const groups = new Map();
  for (const r of rows) { const k = key(r); if (!groups.has(k)) groups.set(k, []); groups.get(k).push(r); }
  return Object.fromEntries([...groups].sort(([a], [b]) => a.localeCompare(b)).map(([k, rs]) => [k, summarize(rs)]));
}
function runVersion(config, repo, version, codeRoot, rows) {
  const snapshotPath = path.join(ROOT, 'artifacts/question-parser', repo, 'snapshot.json');
  const {createQueryService} = require(path.join(codeRoot, 'web/query-service.js'));
  const Scorer = require(path.join(codeRoot, 'web/scorer.js'));
  let service, snapshot; const cold = [];
  for (let i = 0; i < 3; i++) {
    const t = performance.now(); snapshot = read(snapshotPath); const loaded = performance.now();
    service = createQueryService(snapshot); cold.push({loadMs: loaded - t, indexMs: performance.now() - loaded});
  }
  const scorer = Scorer.createScorer(snapshot.map);
  const request = r => ({requestId: r.id, query: r.question});
  const order = [...rows].sort((a, b) => sha(config.seed + a.id).localeCompare(sha(config.seed + b.id)));
  for (const r of order.slice(0, 200)) service.query(request(r));
  const results = new Map(), repeatTimes = [];
  for (let repeat = 0; repeat < 3; repeat++) {
    const times = [];
    for (const r of order) {
      const start = performance.now(), p = service.query(request(r)), ms = performance.now() - start;
      times.push(ms);
      if (!repeat) {
        const choiceOp = p.status === 'needs-choice' && p.operation === 'NOT_SURE' ? scorer.score(r.question).requestedOperation : p.operation;
        const tier = p.status === 'no-match' ? 'no-match' : /Concept search/.test(p.reason) ? 'BM25 fallback' :
          /matched via synonym/.test(p.reason + JSON.stringify(p.alternatives)) ? 'synonym' : 'literal';
        results.set(r.id, {...r, outcome: classify(r, p, choiceOp), status: p.status, actualOperation: p.operation, tier,
          selected: p.seedNodeId ? [p.seedNodeId] : p.selectedNodeIds.slice(0, 2), alternatives: p.alternatives.map(a => a.nodeId), ms: [ms]});
      } else results.get(r.id).ms.push(ms);
    }
    repeatTimes.push(timing(times));
  }
  const raw = rows.map(r => results.get(r.id)), positive = raw.filter(r => !r.negative), negative = raw.filter(r => r.negative);
  fs.writeFileSync(path.join(OUT, repo + '-' + version + '.jsonl'), raw.map(r => JSON.stringify(r)).join('\n') + '\n');
  // Deterministic distributed HTTP sample; never pick based on successful outcomes.
  const sample = order.slice(0, 240).map(r => ({...r, directMs: results.get(r.id).ms}));
  write(path.join(OUT, repo + '-' + version + '-http-input.json'), sample);
  const report = {positive: counts(positive), negative: counts(negative), distinctQuestions: new Set(raw.map(r => r.question)).size,
    cold, repeatTimes, latency: timing(raw.flatMap(r => r.ms)),
    tier: grouped(raw, r => r.tier, rs => timing(rs.flatMap(r => r.ms))),
    operationLatency: grouped(positive, r => r.operation, rs => timing(rs.flatMap(r => r.ms))),
    correctOperationLatency: grouped(positive.filter(r => r.outcome === 'correct'), r => r.operation, rs => timing(rs.flatMap(r => r.ms))),
    constructionStratum: grouped(positive, r => r.constructionStratum, counts),
    axis: grouped(positive, r => r.axis + ':' + r.value, counts), operation: grouped(positive, r => r.operation, counts),
    kindAgreement: grouped(positive.filter(r => r.kindAgreement), r => r.kindAgreement, counts),
    matrix: grouped(positive.filter(r => r.axis === 'target-form'), r => r.phrase + ' × ' + r.form, counts),
    failures: Object.entries(grouped(positive.filter(r => !success(r)), r => r.operation + '/' + r.axis + ':' + r.value + '/' + r.outcome,
      rs => ({count: rs.length, examples: rs.slice(0, 2).map(r => ({question: r.question, target: r.targets, actual: r.selected, status: r.status, operation: r.actualOperation}))})))
      .sort((a, b) => b[1].count - a[1].count).slice(0, 15),
    slowest: [...raw].sort((a, b) => Math.max(...b.ms) - Math.max(...a.ms)).slice(0, 10).map(r => ({question: r.question, operation: r.operation, ms: r.ms}))};
  write(path.join(OUT, repo + '-' + version + '-summary.json'), report);
  console.log(repo, version, report.positive, report.latency);
  return report;
}
function main() {
  fs.mkdirSync(OUT, {recursive: true});
  const config = read(path.join(ROOT, 'eval/variation_templates.json'));
  const baseline = path.join(OUT, 'main-code'); fs.mkdirSync(baseline, {recursive: true});
  const archive = execFileSync('git', ['archive', '7db31cd'], {cwd: ROOT, maxBuffer: 64 * 1024 * 1024});
  execFileSync('tar', ['-xf', '-', '-C', baseline], {input: archive});
  const report = {seed: config.seed, templatesSha256: sha(fs.readFileSync(path.join(ROOT, 'eval/variation_templates.json'))),
    main: execFileSync('git', ['rev-parse', '7db31cd'], {cwd: ROOT}).toString().trim(),
    parser: execFileSync('git', ['rev-parse', 'HEAD'], {cwd: ROOT}).toString().trim(),
    machine: {platform: os.platform(), release: os.release(), arch: os.arch(), cpu: os.cpus()[0].model, cores: os.cpus().length, memory: os.totalmem(), node: process.version},
    loadBefore: os.loadavg(), warmup: 200, repeats: 3, coldRepeats: 3, repos: {}};
  for (const repo of ['honcho', 'salesroom']) {
    const bytes = fs.readFileSync(path.join(ROOT, 'artifacts/question-parser', repo, 'snapshot.json'));
    if (sha(bytes) !== config.repos[repo].snapshotSha256) throw Error('Frozen snapshot changed');
    const snapshot = JSON.parse(bytes), rows = generate(config, repo, snapshot);
    write(path.join(OUT, repo + '-grid.json'), rows);
    report.repos[repo] = {gridSha256: sha(JSON.stringify(rows)), targets: grouped(config.repos[repo].targets, r => r.kind, rs => rs.length)};
    for (const [version, codeRoot] of [['main', baseline], ['parser', ROOT]]) {
      report.repos[repo][version] = runVersion(config, repo, version, codeRoot, rows);
      execFileSync('python3', [path.join(ROOT, 'scripts/bench_variations_http.py'), codeRoot, repo, version], {cwd: ROOT, stdio: 'inherit', timeout: 600000});
      report.repos[repo][version].http = read(path.join(OUT, repo + '-' + version + '-http.json'));
    }
  }
  report.loadAfter = os.loadavg();
  write(path.join(ROOT, 'eval/variation_results.json'), report);
}
module.exports = {generate, forms, classify, timing, counts};
if (require.main === module) main();
