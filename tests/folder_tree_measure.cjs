'use strict';
// Manual measurement gate; independent path-prefix/BFS oracle, unchanged frozen sets.
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process'), {performance} = require('node:perf_hooks');
const root = path.resolve(__dirname, '..'), out = path.join(root, 'artifacts/folder-tree');
const read = p => JSON.parse(fs.readFileSync(p));
const config = read(path.join(__dirname, 'folder_questions.json'));
const p95 = xs => xs.sort((a,b)=>a-b)[Math.ceil(xs.length * .95)-1];
const report = {};
for (const repo of ['honcho','salesroom']) {
  const oldPath = path.join(root, 'artifacts/question-parser', repo, 'snapshot.json');
  const newPath = path.join(out, repo, 'snapshot.json');
  const before = read(oldPath), after = read(newPath);
  const old = require(path.join(out,'base/web/query-service.js')).createQueryService(before);
  const service = require('../web/query-service.js').createQueryService(after);
  const folders = after.map.nodes.filter(n=>n.kind==='layer'), files = after.map.nodes.filter(n=>n.kind==='file');
  const fileIds = new Set(files.map(n=>n.id));
  assert.equal(before.source.commit, after.source.commit);
  assert.deepEqual(before.map.file_edges, after.map.file_edges);
  const bare = path.join(process.env.TMPDIR, 'folder-tree-workspace/git-cache');
  const repoDir = fs.readdirSync(bare).find(n=>n.endsWith(after.source.commit));
  const tracked = new Set(execFileSync('git', ['--git-dir',path.join(bare,repoDir,'repo.git'),'ls-tree','-r','--name-only',after.source.commit],{encoding:'utf8'}).trim().split('\n'));
  for (const n of files) assert.ok(tracked.has(n.path), n.path);
  const rows = [], packets = [];
  for (const folder of config[repo]) {
    const seed = folders.find(n=>n.label===folder); assert.ok(seed, folder);
    const inside = new Set(files.filter(n=>n.path.startsWith(folder+'/')).map(n=>n.id));
    assert.ok(inside.size);
    for (const [form, operation] of [['where is {x}','LOCATE'], ['locate folder {x}','LOCATE'], ['what uses {x}','DOWNSTREAM'], ['what does {x} use','UPSTREAM'], ['dependencies of {x} folder','UPSTREAM']]) {
      const question = form.replace('{x}',folder), p = service.query({requestId:'folder',query:question});
      const expected = new Set();
      if (operation === 'LOCATE') {
        expected.add(seed.id);
        folders.filter(n=>n.label.startsWith(folder+'/')).forEach(n=>expected.add(n.id));
        inside.forEach(n=>expected.add(n));
      } else {
        const reached = new Set(inside), queue = [...inside];
        for(let i=0;i<queue.length;i++) for(const e of after.map.file_edges) {
          if(e.type==='realtime') continue;
          const a = operation==='DOWNSTREAM'? e.to:e.from, b=operation==='DOWNSTREAM'?e.from:e.to;
          if(a===queue[i]&&!reached.has(b)) {reached.add(b);queue.push(b);}
        }
        expected.add(seed.id); reached.forEach(id=>{if(!inside.has(id))expected.add(id);});
      }
      const choice = p.status === 'needs-choice' ? seed.id : undefined;
      if (choice) assert.ok(p.alternatives.some(a=>a.nodeId===choice), question);
      let page = choice ? service.query({requestId:'folder',query:question,chosenNodeId:choice}) : p;
      const actual = new Set(); let pages=0;
      do {
        assert.equal(page.status,'matched',question); assert.equal(page.operation,operation,question);
        assert.ok(page.selectedNodeIds.length<=200); page.selectedNodeIds.forEach(id=>actual.add(id));
        for(const w of page.witnesses) {
          assert.ok(w.nodeIds.every(id=>fileIds.has(id)));
          assert.ok(inside.has(operation==='DOWNSTREAM'?w.nodeIds.at(-1):w.nodeIds[0]));
        }
        packets.push(page); pages++; assert.ok(pages<20);
        page = page.continuation ? service.query({requestId:'folder',query:question,chosenNodeId:choice,continuation:page.continuation}) : null;
      } while(page);
      assert.deepEqual(actual,expected,question);
      rows.push({id:repo+'-folder-'+rows.length, question, operation, axis:'folder', folder,
        expected:[...expected].sort(), pages, status:p.status});
    }
  }
  fs.writeFileSync(path.join(out,repo,'folder-questions.json'),JSON.stringify(rows,null,2));
  fs.writeFileSync(path.join(out,repo,'folder-packets.json'),JSON.stringify(packets));
  const frozen = path.join(root,'eval',repo==='honcho'?'question_parser.json':'question_parser_salesroom.json');
  const baseline = path.join(out,repo,'frozen-before.json'), result = path.join(out,repo,'frozen-after.json');
  execFileSync(process.execPath,[path.join(root,'scripts/eval_question_parser.cjs'),oldPath,baseline,'',frozen,path.join(out,'base/web/query-service.js')]);
  execFileSync(process.execPath,[path.join(root,'scripts/eval_question_parser.cjs'),newPath,result,baseline,frozen,path.join(root,'web/query-service.js')]);
  const times = {before:[],after:[]};
  const questions = [...read(frozen).rows, ...rows];
  for(const [version, s] of [['before',old],['after',service]]) {
    for(let repeat=0;repeat<12;repeat++) for(const r of questions) {
      const t=performance.now(); s.query({requestId:r.id,query:r.question});
      if(repeat>=2) times[version].push(performance.now()-t);
    }
  }
  const http = Array.from({length:240},(_,i)=>questions[i%questions.length]);
  fs.writeFileSync(path.join(out,repo,'http-input.json'),JSON.stringify(http));
  const oldSize=Buffer.byteLength(JSON.stringify(before)), newSize=Buffer.byteLength(JSON.stringify(after));
  report[repo]={folderQuestions:rows.length, sourceFiles:files.length, oldFolders:before.map.nodes.filter(n=>n.kind==='layer').length,
    newFolders:folders.length, oldBytes:oldSize,newBytes:newSize,growthPercent:(newSize/oldSize-1)*100,
    directP95Ms:{before:p95(times.before),after:p95(times.after)}, samples:times.after.length,
    frozen:{before:read(baseline).splits,after:read(result).splits},importMs:read(path.join(out,repo,'browser.json')).importMs};
  assert.ok(report[repo].directP95Ms.after <= report[repo].directP95Ms.before+1, 'direct p95 regression');
}
fs.writeFileSync(path.join(out,'measurements.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify(report,null,2));
