#!/usr/bin/env node
'use strict';
/* Trusted JSON-lines query worker. Usage: node scripts/query_worker.cjs SNAPSHOT.json
 * stdin:  one JSON request per line {requestId, query, snapshotId?, continuation?, chosenNodeId?}
 * stdout: one JSON line per request {ok:true, packet} | {ok:false, requestId, error}
 * Runs only the installed DAG GPS modules; never code from an imported repository.
 * Refuses to answer if the snapshot was bound to different query-code bytes. */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const readline = require('readline');
const {createQueryService} = require('../web/query-service.js');

const MAX_SNAPSHOT_BYTES = 128 * 1024 * 1024;
const MAX_LINE_BYTES = 64 * 1024;
const ROOT = path.resolve(__dirname, '..');
const QUERY_CODE = ['web/scorer.js', 'web/router.js', 'web/query-service.js'];

function fail(message) { process.stderr.write(message + '\n'); process.exit(2); }

const file = process.argv[2];
if (!file) fail('usage: query_worker.cjs SNAPSHOT.json');
const stat = fs.statSync(file);
if (!stat.isFile() || stat.size > MAX_SNAPSHOT_BYTES) fail('snapshot must be a bounded regular file');
const snapshot = JSON.parse(fs.readFileSync(file, 'utf8'));
const sha = data => crypto.createHash('sha256').update(data).digest('hex');
for (const name of QUERY_CODE) {
  const actual = sha(fs.readFileSync(path.join(ROOT, name)));
  const bound = snapshot.queryCode && snapshot.queryCode[name];
  if (bound !== actual) fail('query code ' + name + ' differs from the bytes bound into this snapshot');
}
if (snapshot.scorerSha256 !== snapshot.queryCode['web/scorer.js']) fail('scorer digest mismatch');
const service = createQueryService(snapshot);

const rl = readline.createInterface({input: process.stdin, crlfDelay: Infinity});
rl.on('line', line => {
  let requestId = null;
  try {
    if (Buffer.byteLength(line) > MAX_LINE_BYTES) throw new Error('request line too large');
    if (!line.trim()) return;
    const request = JSON.parse(line);
    requestId = typeof request.requestId === 'string' ? request.requestId : null;
    const packet = service.query(request);
    process.stdout.write(JSON.stringify({ok: true, packet}) + '\n');
  } catch (error) {
    process.stdout.write(JSON.stringify({ok: false, requestId, error: String(error.message || error)}) + '\n');
  }
});
