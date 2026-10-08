'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const {analyzeImpact,testReason}=require('../web/impact.js');
const meta={repo:'fixture/repo',commit:'1234567'};
const file=id=>({id,path:id,kind:'file'}), edge=(from,to,type='import')=>({from,to,type});
function fixture(){return {meta,nodes:['a','b','c','d','tests/test_a.py','rpc','http','rt','isolated'].map(file).concat({id:'layer',kind:'layer'}),file_edges:[edge('b','a'),edge('c','a'),edge('d','c'),edge('d','b'),edge('a','d'),edge('b','a'),edge('tests/test_a.py','d'),edge('rpc','b','rpc'),edge('http','rpc','http'),edge('rt','a','realtime')]};}
test('direct/transitive are distinct, deduped; cycles exclude origin',()=>{
 const r=analyzeImpact(fixture(),null,'a');assert.deepEqual(r.directConsumers.map(x=>x.id),['b','c']);assert.deepEqual(r.transitiveConsumers.map(x=>x.id),['d','tests/test_a.py']);
 assert.equal(r.coverage,'unknown');assert.equal(r.linkedTests.length,1);assert.deepEqual(r.linkedTests[0].chain,['tests/test_a.py','d','b','a']);
});
test('shortest tie deterministic across edge and node order; input immutable',()=>{
 const m=fixture(),before=JSON.stringify(m),r=analyzeImpact(m,null,'a');assert.deepEqual(r.transitiveConsumers[0].chain,['d','b','a']);
 const reversed={...m,nodes:m.nodes.slice().reverse(),file_edges:m.file_edges.slice().reverse()};assert.deepEqual(analyzeImpact(reversed,null,'a'),r);assert.equal(JSON.stringify(m),before);
});
test('HTTP/RPC separate transitive boundary chains, realtime excluded',()=>{
 const r=analyzeImpact(fixture(),null,'a');assert.deepEqual(r.boundaryImpacts.map(x=>x.id),['rpc','http']);assert.deepEqual(r.boundaryImpacts[1].chain,['http','rpc','b','a']);assert.deepEqual(r.boundaryImpacts[1].edges.map(x=>x.type),['http','rpc','import']);assert.ok(!JSON.stringify(r).includes('"rt"'));
});
test('boundary overlaps disclosed and shortest qualifying path retained',()=>{
 const m=fixture();m.file_edges.push(edge('c','a','http'),edge('a','http','http'));const r=analyzeImpact(m,null,'a');assert.equal(r.boundaryImpacts.find(x=>x.id==='c').distance,1);assert.ok(!r.boundaryImpacts.some(x=>x.id==='a'));
});
test('isolated coverage is unknown; rejects unknown/layer IDs and orphan edges',()=>{
 const m=fixture();const r=analyzeImpact(m,null,'isolated');assert.deepEqual(r.directConsumers,[]);assert.deepEqual(r.linkedTests,[]);assert.equal(r.coverage,'unknown');
 for(const id of ['no','layer',null])assert.throws(()=>analyzeImpact(m,null,id),/known file/);
 m.file_edges.push(edge('absent','a'));assert.throws(()=>analyzeImpact(m,null,'a'),/endpoint/);
});
test('documented test rules, not loose filename guessing',()=>{
 for(const id of ['tests/a.ts','x/__tests__/a.ts','runner/test_a.py','x/a.spec.ts','e2e/a.ts'])assert.ok(testReason(file(id)));
 assert.equal(testReason(file('lib/contest.ts')),null);assert.equal(testReason(file('testimony.py')),null);assert.ok(testReason({...file('arbitrary'),classification:'test'}));
});
const citation={path:'a',start:2,end:4,symbol:'f'};
function tours(){return {version:1,...meta,tours:[{id:'tour',title:'Tour',steps:[{title:'Step',nodeIds:['b'],evidence:[citation,citation,{path:'b',start:1,end:1},{path:'absent',start:1,end:1}]}],links:[{label:'Link',evidence:[citation]}]}]};}
test('exact citations not node membership; raw and compiled supported; duplicates/orphans',()=>{
 const raw=tours(),r=analyzeImpact(fixture(),raw,'a');assert.equal(r.tourReferences.length,2);assert.equal(r.orphanTourReferences.length,1);assert.equal(r.tourReferences.find(x=>x.kind==='step').stepTitle,'Step');
 const compiled=JSON.parse(JSON.stringify(raw));compiled.tours[0].steps[0].evidence.forEach(e=>{e.nodeId=e.path;e.excerpt='source';});assert.equal(analyzeImpact(fixture(),compiled,'a').tourReferences.length,2);
 assert.equal(analyzeImpact(fixture(),raw,'c').tourReferences.length,0);
});
test('wrong snapshot/repo/schema and invalid ranges reject; no tours honest',()=>{
 for(const changed of [{repo:'other'},{commit:'7654321'},{version:2}])assert.throws(()=>analyzeImpact(fixture(),{...tours(),...changed},'a'),/snapshot/);
 const t=tours();t.tours[0].steps[0].evidence=[{...citation,start:0}];assert.throws(()=>analyzeImpact(fixture(),t,'a'),/line range/);assert.equal(analyzeImpact(fixture(),null,'a').toursStatus,'unavailable');
});
test('real pinned audit: runner-client witnesses and citations, no observed tests',()=>{
 const m=require('../maps/quest-coder/map.json'),t=require('../maps/quest-coder/tours.json'),r=analyzeImpact(m,t,'lib/runner-client.ts');
 assert.deepEqual(r.directConsumers.map(x=>x.id),['app/api/health/route.ts','app/api/run/route.ts','lib/party-boss-server.ts']);assert.deepEqual(r.transitiveConsumers.map(x=>x.chain),[['app/api/party/boss/route.ts','lib/party-boss-server.ts','lib/runner-client.ts']]);assert.equal(r.linkedTests.length,0);assert.equal(r.coverage,'unknown');assert.deepEqual(r.tourReferences.filter(x=>x.kind==='step').map(x=>[x.tourId,x.step,x.start,x.end]),[['submit',3,31,46],['submit',3,49,83]]);
});
test('real grading engine includes eleven hidden tests through actual imports',()=>{
 const r=analyzeImpact(require('../maps/quest-coder/map.json'),null,'runner/quest_runner.py');assert.equal(r.directConsumers.length,14);assert.equal(r.transitiveConsumers.length,0);assert.equal(r.linkedTests.length,11);assert.ok(r.linkedTests.every(x=>x.edges.every(e=>e.type==='import')));
});
