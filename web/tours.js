/* Curated walkthrough state, independent of import routing and learned aliases. */
(function(root,factory){
  if(typeof module==='object' && module.exports) module.exports=factory();
  else root.DagGpsTours=factory();
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const key=q=>String(q).trim().toLowerCase().replace(/\s+/g,' ').replace(/[?!]+$/,'');
  function createController(data){
    const tours=data ? data.tours : [];
    let active=null,index=0;
    function resolve(query){return tours.find(t=>t.queries.some(q=>key(q)===key(query))) || null;}
    function start(id){const found=tours.find(t=>t.id===id); if(!found) throw Error('Unknown tour'); active=found;index=0;return state();}
    function state(){return {active,index,step:active?active.steps[index]:null};}
    function move(delta){if(active)index=Math.max(0,Math.min(active.steps.length-1,index+delta));return state();}
    function reset(){index=0;return state();}
    function exit(){active=null;index=0;return state();}
    return {tours,resolve,start,state,move,reset,exit};
  }
  return {createController};
});
