'use strict';
const test = require('node:test'), assert = require('node:assert/strict'), fs = require('node:fs');
const {generate} = require('../scripts/bench_variations.cjs');
const config = require('../eval/variation_templates.json');

test('supported operation pattern families are present in the generated grid', () => {
  const inventory = {
    DOWNSTREAM: ['what uses {x}', 'downstream of {x}', 'downstream {x}'],
    UPSTREAM: ['what does {x} use', 'upstream of {x}', 'upstream {x}', 'which do {x} import'],
    PATH: ['route from {x} to {y}', 'how {x} reach {y}', 'how does {x} connect to {y}'],
    TRACE: ['trace from {x}']
  };
  for (const repo of ['honcho', 'salesroom']) {
    const snapshot = JSON.parse(fs.readFileSync('artifacts/question-parser/' + repo + '/snapshot.json'));
    const rows = generate(config, repo, snapshot);
    for (const [op, phrases] of Object.entries(inventory)) {
      if (op === 'TRACE' && repo === 'salesroom') continue;
      for (const phrase of phrases) assert.ok(rows.some(r => r.operation === op && r.phrase === phrase), repo + ': ' + phrase);
    }
  }
});

test('PATH includes pinned file edges as well as folder edges on both repos', () => {
  for (const repo of ['honcho', 'salesroom']) {
    const s = JSON.parse(fs.readFileSync('artifacts/question-parser/' + repo + '/snapshot.json'));
    const nodes = new Map(s.map.nodes.map(n => [n.id, n]));
    for (const kind of ['file', 'layer']) {
      const pairs = config.repos[repo].pairs.filter(p => p.operation === 'PATH' && nodes.get(p.from).kind === kind);
      assert.ok(pairs.length > 0, repo + ': missing ' + kind);
      for (const p of pairs) assert.ok((kind === 'file' ? s.map.file_edges : s.map.edges).some(e => e.from === p.from && e.to === p.to));
    }
  }
});
