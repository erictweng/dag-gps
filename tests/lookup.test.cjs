const test = require('node:test');
const assert = require('node:assert/strict');
const {createScorer, validateResult} = require('../web/scorer.js');
const map = require('../maps/quest-coder/map.json');
const scorer = createScorer(map);
const target = q => scorer.score(q).targets.locate_target;
for (const [q,id,label] of [
  ['locate app/api/health/route.ts','app/api/health/route.ts','Exact match'],
  ['quest_runner.py','runner/quest_runner.py','Exact match'],
  ['quest_runner','runner/quest_runner.py','Likely match'],
  ['file bounded_sub','runner/bounded_subprocess.py','Likely match'],
  ['dependencies of lib/runner-client.ts','lib/runner-client.ts','Exact match'],
]) test(`lookup ${q}`,()=>{
  const r=scorer.score(q),h=r.targets.locate_target;
  assert.equal(r.yes,true);assert.equal(h.choice,id);assert.equal(h.match.label,label);
  assert.equal(map.nodes.find(n=>n.id===id).kind,'file');assert.equal(validateResult(r,map),true);
});
test('duplicate basename retains every real path, never picks by fan-in',()=>{
  for (const q of ['route.ts','file route','__init__.py','page.tsx']) {
    const h=target(q);assert.equal(h.yes,false);assert.equal(h.match.label,'Needs your choice');
    assert.ok(h.suggestions.length>1);assert.equal(h.match.margin,0);
    if(q==='route.ts') assert.deepEqual(h.suggestions.map(a=>a.id).sort(),map.nodes.filter(n=>n.kind==='file'&&n.path.endsWith('/route.ts')).map(n=>n.id).sort());
  }
});
test('missing runner.py is honest, full-path real suggestions only, never layer substitute',()=>{
  assert.ok(!map.nodes.some(n=>n.path==='runner.py'||n.path?.endsWith('/runner.py')));
  const h=target('where is runner.py?');assert.equal(h.yes,false);
  assert.match(h.reason,/No exact file named runner\.py/);assert.equal(h.match.label,'Needs your choice');
  assert.ok(h.suggestions.some(a=>a.id==='runner/quest_runner.py'));
  assert.ok(h.suggestions.every(a=>a.path===a.id&&map.nodes.some(n=>n.id===a.id&&n.kind==='file')));
});
for(const q of ['quest_runer.py','quest_runer','quest_runner.pz'])test(`typo is suggestion only: ${q}`,()=>{
  const h=target(q);assert.equal(h.yes,false);assert.equal(h.match.label,'Needs your choice');
  assert.ok(h.suggestions.some(a=>a.id==='runner/quest_runner.py'));
});
for(const q of ['quantum teleporter','zzzzunknown','file asdfghjkl.py','file ox','file authentication.py'])test(`unknown stays no match: ${q}`,()=>{
  const r=scorer.score(q),h=r.targets.locate_target;assert.equal(r.yes,false);
  assert.equal(h.match.label,'No match');assert.deepEqual(h.suggestions,[]);
});
for (const [q,id] of [['where does grading live?','runner-service'],['where is authentication?','auth'],['grading request','run-gateway'],['pyodide','browser-run']])test(`responsibility metadata ${q}`,()=>{
  const r=scorer.score(q);assert.equal(r.yes,true);assert.equal(r.targets.locate_target.choice,id);
  assert.equal(r.targets.locate_target.match.mode,'architecture');
});
test('filename and intent collisions do not parse filenames as commands',()=>{
  for(const [q,op,id] of [['route.ts','NOT_SURE',null],['file route','NOT_SURE',null],['route handlers','LOCATE','api'],['PATH.ts','NOT_SURE',null],['dependencies of quest_runner.py','UPSTREAM','runner/quest_runner.py']]) {
    const r=scorer.score(q);assert.equal(r.operation.choice,op);if(id)assert.equal(r.targets.locate_target.choice,id);
  }
});
test('PATH endpoints independently honor filename ambiguity and missing names',()=>{
  const good=scorer.score('path from app/api/friends/route.ts to friends-store');
  assert.equal(good.yes,true);assert.equal(good.targets.to_target.choice,'lib/friends-store.ts');
  for(const q of ['path from route.ts to friends-store.ts','path from runner.py to database','path from quest_runer.py to database']) {
    const r=scorer.score(q);assert.equal(r.yes,false);assert.equal(r.operation.choice,'NOT_SURE');assert.equal(r.targets.from_target.yes,false);
  }
});
test('literal hierarchy, file/alias collision, and conservative ambiguity on synthetic map',()=>{
  const fixture={nodes:[
    {id:'layer',kind:'layer',label:'Thing architecture',aliases:['thing.ts'],path:''},
    {id:'thing.ts',kind:'file',label:'thing.ts',path:'thing.ts'},
    {id:'lib/thing.ts',kind:'file',label:'thing.ts',path:'lib/thing.ts'},
    {id:'lib/thingy.ts',kind:'file',label:'thingy.ts',path:'lib/thingy.ts'},
  ],edges:[],file_edges:[{from:'thing.ts',to:'lib/thing.ts',type:'import'}]};
  const s=createScorer(fixture);
  for(const [q,id,label] of [['thingy.ts','lib/thingy.ts','Exact match'],['lib/thing.ts','lib/thing.ts','Exact match'],['lib/thing','lib/thing.ts','Likely match']]){
    const r=s.score(q);assert.equal(r.yes,true);assert.equal(r.targets.locate_target.choice,id);assert.equal(r.targets.locate_target.match.label,label);
  }
  for(const q of ['thing.ts','file thing','file thin','thung.ts'])assert.equal(s.score(q).yes,false);
  assert.equal(s.score('Thing architecture').targets.locate_target.choice,'layer');
});
test('labels/acceptance depend on evidence, not normalized weight or table size',()=>{
  const node={id:'a',kind:'layer',label:'Alpha',aliases:['signal'],path:''};
  const small=createScorer({nodes:[node,{id:'b',kind:'layer',label:'Beta',path:''}]}).score('signal').targets.locate_target;
  const large=createScorer({nodes:[node,...Array.from({length:1000},(_,i)=>({id:'x'+i,kind:'layer',path:''}))]}).score('signal').targets.locate_target;
  assert.ok(small.confidence>large.confidence);assert.equal(small.match.label,'Exact match');assert.equal(large.match.label,small.match.label);
  assert.equal(small.yes,true);assert.equal(large.yes,true);
});
test('natural filename mention remains file-first; morphology is only a likely architecture match',()=>{
  const h=target('where is the implementation of runner.py?');assert.equal(h.yes,false);assert.match(h.reason,/No exact file named runner\.py/);
  for(const q of ['where does grading live?','where is authentication?'])assert.equal(target(q).match.label,'Likely match');
  for(const q of ['runner/quest_runner','proxyy'])assert.equal(target(q).match.mode,'filename');
});
test('literal tokens are not truncated or silently repaired into exact files',()=>{
  for(const name of ['./runner/quest_runner.py','runner/quest_runner.py/child','quest_runner.py.extra']) {
    const h=target('locate '+name);assert.equal(h.yes,false);assert.equal(h.match.query,name);assert.notEqual(h.match.label,'Exact match');
  }
});
test('separate lookup challenge retains misses and gates false confident acceptance',()=>{
  const {loadCases,evaluate}=require('../scripts/eval_lookup.cjs'),rows=loadCases(map),r=evaluate(map,rows,1);
  assert.equal(rows.length,40);assert.equal(r.negativeFalseAccept.total,24);assert.equal(r.targetTop1.total,17);
  assert.equal(r.negativeFalseAccept.correct,0);assert.equal(r.acceptedWrong.correct,0);
  assert.ok(rows.some(row=>row.question==='where is bearer auth?')); // retained responsibility challenge, not dropped to perfect metrics
});
test('additive evidence contract accepts legacy heads but rejects malformed new evidence',()=>{
  const r=scorer.score('quest_runner.py');
  for(const mutate of [x=>x.targets.locate_target.match.label='100% sure',x=>x.targets.locate_target.match.margin=NaN,x=>x.targets.locate_target.suggestions[0].id='invented',x=>x.targets.locate_target.suggestions[0].path='fabricated',x=>x.targets.locate_target.match.label='No match']) {
    const bad=structuredClone(r);mutate(bad);assert.throws(()=>validateResult(bad,map));
  }
  const legacy=structuredClone(r);delete legacy.evidenceVersion;
  for(const h of Object.values(legacy.targets)){delete h.match;delete h.suggestions;}
  assert.equal(validateResult(legacy,map),true);
});
