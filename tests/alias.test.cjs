'use strict';
const {test} = require('node:test'), assert = require('node:assert/strict');
const A = require('../web/aliases.js'), S = require('../web/scorer.js');
const map = require('../maps/quest-coder/map.json');
function storage() { const data = new Map(); return {getItem:k=>data.get(k)??null,setItem:(k,v)=>data.set(k,v),data}; }
const json = entries => JSON.stringify({version:1,repo:map.meta.repo,aliases:entries});
const alias = (text='Python judge', nodeId='runner-service')=>({alias:text,nodeId});
test('synthetic correction changes evidence, persists, removes to baseline without mutating map',()=>{
 const original=JSON.stringify(map), memory=storage(), store=A.createStore(map,memory);
 const baseline=S.createScorer(map).score('Python judge');
 store.add('Python judge','runner-service');
 const corrected=S.createScorer(map,store.overlay()).score('Python judge');
 assert.equal(corrected.yes,true); assert.equal(corrected.targets.locate_target.choice,'runner-service');
 assert.equal(corrected.targets.locate_target.top3[0].components.learnedAlias,30);
 assert.deepEqual(A.createStore({...map,meta:{...map.meta,commit:'new-build'}},memory).overlay(),[alias()]);
 store.remove('Python judge','runner-service'); assert.deepEqual(S.createScorer(map,store.overlay()).score('Python judge'),baseline);
 assert.equal(JSON.stringify(map),original);
});
test('harder synthetic phrase abstains until explicit correction',()=>{
 const q='Python judge station'; assert.equal(S.createScorer(map).score(q).yes,false);
 assert.equal(S.createScorer(map,[alias(q)]).score(q).targets.locate_target.choice,'runner-service');
 assert.equal(S.createScorer(map,[alias(q)]).score(q).yes,true);
});
test('matching is exact phrase, unrelated or partial nicknames abstain',()=>{
 const s=S.createScorer(map,[alias('galactic nickname')]);
 assert.equal(s.score('galactic nickname').yes,true);
 for(const q of ['quantum teleporter','galactic','galactic nickname elsewhere']) assert.equal(s.score(q).yes,false);
});
test('conflicts across >3 real nodes require choice with all candidates, no prior inflation',()=>{
 const ids=map.nodes.slice(0,5).map(n=>n.id), list=ids.map(id=>alias('my nickname',id));
 const r=S.createScorer(map,list).score('my nickname'); S.validateResult(r,map);
 assert.equal(r.yes,false); assert.equal(r.targets.locate_target.match.margin,0);
 assert.deepEqual(r.targets.locate_target.suggestions.map(a=>a.id),ids);
});
test('duplicate normalized bindings idempotent; conflict is retained visibly',()=>{
 const store=A.createStore(map,storage()); store.add('Python judge','runner-service');store.add('PYTHON  JUDGE','runner-service');
 assert.equal(store.snapshot().entries.length,1);store.add('python judge','browser-run');
 assert.equal(store.snapshot().entries.length,2); assert.ok(store.snapshot().entries.every(e=>e.conflict));
});
test('real literal filenames and paths outrank nicknames, ambiguous basename stays ambiguous',()=>{
 for(const q of ['app/api/health/route.ts','route.ts','quest_runner.py']) {
  assert.deepEqual(S.createScorer(map,[alias(q)]).score(q),S.createScorer(map).score(q));
 }
});
test('every real file path including dynamic-route brackets is protected from alias hijacking',()=>{
 for(const n of map.nodes.filter(n=>n.kind==='file')) {
  const r=S.createScorer(map,[alias(n.path)]).score('locate '+n.path);
  assert.equal(r.yes,true,n.path);assert.equal(r.targets.locate_target.choice,n.id,n.path);
  assert.equal(r.targets.locate_target.match.mode,'filename',n.path);
 }
});
test('learned file nodes and independent PATH endpoints retain real IDs',()=>{
 const s=S.createScorer(map,[alias('health point','app/api/health/route.ts'),alias('friend point','lib/friends-store.ts')]);
 assert.equal(s.score('health point').targets.locate_target.choice,'app/api/health/route.ts');
 const r=s.score('path from health point to friend point');assert.equal(r.yes,true);
 assert.equal(r.targets.to_target.choice,'lib/friends-store.ts');
 assert.equal(s.score('path from unknown place to friend point').yes,false);
});
test('imports validate atomically before merge/replace preview and no writes until commit',()=>{
 const memory=storage(), store=A.createStore(map,memory);store.add('old name','auth');const before=store.serialize();
 const preview=store.preview(json([alias(),alias()]),'merge');assert.equal(preview.imported,1);assert.equal(preview.entries.length,2);
 assert.equal(store.serialize(),before);store.commit(preview);assert.equal(store.snapshot().entries.length,2);
 const replace=store.preview(json([alias()]),'replace');assert.equal(store.snapshot().entries.length,2);store.commit(replace);
 assert.equal(store.snapshot().entries.length,1);
 for(const bad of [json([alias(),{alias:'',nodeId:'auth'}]),'{',json([alias()]).replace('"version":1','"version":2'),json([alias()]).replace(map.meta.repo,'other/repo'),json([alias()]).replace('"aliases":','"extra":1,"aliases":')]) {
  const saved=store.serialize();assert.throws(()=>store.preview(bad));assert.equal(store.serialize(),saved);
 }
});
test('orphan imported IDs quarantined and remain inspectable on deleted-node rebuild',()=>{
 const memory=storage(), store=A.createStore(map,memory);const p=store.preview(json([alias(),alias('old nickname','deleted-node')]));
 assert.equal(p.orphans,1);store.commit(p);assert.equal(store.overlay().length,1);
 const changed=A.createStore({...map,nodes:map.nodes.filter(n=>n.id!=='runner-service')},memory);
 assert.equal(changed.overlay().length,0);assert.equal(changed.snapshot().entries.filter(e=>e.orphan).length,2);
});
test('export roundtrip preserves markup strictly as data',()=>{
 const store=A.createStore(map,storage());store.add('<img src=x onerror=alert(1)>','auth');
 assert.deepEqual(A.validate(store.serialize(),map.meta.repo),[alias('<img src=x onerror=alert(1)>','auth')]);
});
test('bad strings, schema, oversized files and untrusted objects rejected',()=>{
 for(const text of ['', ' ', 'x'.repeat(161),'a\nname','a\u0000','\ud800']) assert.throws(()=>A.entry(alias(text)));
 assert.throws(()=>A.validate(' '.repeat(A.MAX_BYTES+1),map.meta.repo));
 assert.throws(()=>A.validate(json(Array.from({length:1001},(_,i)=>alias('n'+i))),map.meta.repo));
 assert.throws(()=>A.entry({...alias(),__proto__:null,extra:'x'}));
 assert.throws(()=>S.createScorer(map,[alias('x','unknown-id')]));
});
test('inaccessible storage or quota is unsaved but session navigation remains functional',()=>{
 const denied={getItem:()=>{throw Error('denied');},setItem:()=>{throw Error('quota');}};
 const store=A.createStore(map,denied);assert.match(store.snapshot().status,/unavailable/);
 store.add('my judge','runner-service'); assert.match(store.snapshot().status,/Unsaved/);
 assert.equal(S.createScorer(map,store.overlay()).score('my judge').yes,true);
});
test('clear persists an empty schema; wrong/corrupt saved data cannot crash navigation',()=>{
 const memory=storage(), store=A.createStore(map,memory);store.add('my judge','runner-service');store.clear();
 assert.deepEqual(A.createStore(map,memory).overlay(),[]);
 memory.setItem(store.snapshot().key,'bad');const next=A.createStore(map,memory);
 assert.deepEqual(next.overlay(),[]);assert.ok(next.snapshot().error);
 assert.equal(S.createScorer(map,next.overlay()).score('grader').yes,true);
});
test('same repo regenerated map retains valid ID, quarantines deleted alias, reports loaded count',()=>{
 const memory=storage(), before={meta:{repo:'fixture/repo',commit:'old'},nodes:[{id:'a.cjs',kind:'file',layer:'old'},{id:'gone.py',kind:'file',layer:'old'}]};
 const store=A.createStore(before,memory);store.add('valid station','a.cjs');store.add('retired station','gone.py');
 const after={meta:{repo:'fixture/repo',commit:'new'},nodes:[{id:'a.cjs',kind:'file',layer:'new'},{id:'new.cjs',kind:'file',layer:'old'}]};
 const loaded=A.createStore(after,memory);
 assert.equal(loaded.snapshot().key,store.snapshot().key);
 assert.match(loaded.snapshot().status,/Loaded 2 saved aliases/);
 assert.deepEqual(loaded.overlay(),[{alias:'valid station',nodeId:'a.cjs'}]);
 assert.deepEqual(loaded.snapshot().entries.map(e=>[e.nodeId,e.orphan]),[['a.cjs',false],['gone.py',true]]);
 assert.equal(A.createStore({...after,meta:{repo:'another/repo'}},memory).overlay().length,0);
});
