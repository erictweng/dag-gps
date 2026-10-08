const {test}=require('node:test'),assert=require('node:assert/strict');
const {createController}=require('../web/tours.js');
const spec=require('../maps/quest-coder/tours.json');
test('all three curated tours have explicit stable query resolution',()=>{
 const c=createController(spec);
 assert.equal(c.resolve('walk me through submitting code').id,'submit');
 assert.equal(c.resolve('  WALK ME THROUGH SIGNING IN? ').id,'sign-in');
 assert.equal(c.resolve('how does run basic work').id,'run-basic');
});
test('ordinary Ask and ambiguous free text stay outside tour resolver',()=>{
 const c=createController(spec);
 for(const q of ['where is magic link?','locate lib/session.ts','dependencies of auth','path from auth to api routes','submit','how does arbitrary code work'])assert.equal(c.resolve(q),null);
});
test('previous next boundaries reset switch and exit',()=>{
 const c=createController(spec);assert.equal(c.state().active,null);
 c.start('submit');assert.equal(c.move(-1).index,0);for(let i=0;i<20;i++)c.move(1);
 assert.equal(c.state().index,7);assert.equal(c.reset().index,0);
 c.move(1);assert.equal(c.start('run-basic').index,0);
 assert.equal(c.exit().active,null);assert.equal(c.move(1).index,0);
 assert.throws(()=>c.start('unknown'));
});
test('zero tours are honest and no learned aliases enter resolver',()=>{
 const c=createController(null);assert.deepEqual(c.tours,[]);assert.equal(c.resolve('walk me through submitting code'),null);assert.throws(()=>c.start('submit'));
 const d=createController(spec,[{alias:'tour custom',nodeId:'auth'}]);assert.equal(d.resolve('tour custom'),null);
});
test('controller preserves caller input and never computes graph routes',()=>{
 const before=JSON.stringify(spec),c=createController(spec);c.start('submit');c.move(1);c.reset();c.exit();assert.equal(JSON.stringify(spec),before);
 assert.equal('shortestPath' in c,false);
});
