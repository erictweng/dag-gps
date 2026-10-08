// Trusted UI in canvas closure; query/map values remain text, never code.
var impact = null, selectedWitness = null;
var impactPanel = document.getElementById('impact-panel');
function clearImpact(){impact=null;selectedWitness=null;impactPanel.hidden=true;impactPanel.textContent='';}
function impactRows(rows,section){
  return rows.length ? rows.map(function(r,i){return '<button type="button" class="btn ghost alternative" data-impact-result="'+section+'" data-impact-index="'+i+'">'+esc(r.path)+'<br><small>'+r.distance+' '+(r.distance===1?'edge':'edges')+' · '+esc(r.testEvidence || r.reason)+'</small></button>';}).join('') : '<p class="sub">None observed in this snapshot.</p>';
}
function renderImpact(){
  if(!impact)return;
  impactPanel.hidden=false;
  impactPanel.innerHTML='<h2>Potential impact</h2><p>'+esc(impact.fileId)+'</p><p class="sub">Potentially affected, not guaranteed to break. Snapshot '+esc(impact.snapshot)+'. Arrows: consumer → dependency.</p><button type="button" class="btn ghost" id="impact-return">Return to impact graph</button><button type="button" class="btn ghost" id="impact-close">Close impact</button>'+
    (trustUI ? trustUI.badge([impact.fileId].concat(impact.directConsumers,impact.transitiveConsumers,impact.boundaryImpacts).flatMap(function(r){return typeof r==='string'?[r]:r.chain;})) : '')+
    '<h3>Direct consumers ('+impact.directConsumers.length+')</h3>'+impactRows(impact.directConsumers,'directConsumers')+
    '<h3>Transitive consumers ('+impact.transitiveConsumers.length+')</h3>'+impactRows(impact.transitiveConsumers,'transitiveConsumers')+
    '<h3>Linked tests ('+impact.linkedTests.length+')</h3><p id="impact-coverage">Coverage unknown. '+(impact.linkedTests.length?'Observed import reachability, not coverage proof.':'No dependency-linked test observed; this does not mean untested.')+'</p>'+impactRows(impact.linkedTests,'linkedTests')+
    '<h3>Tour references ('+impact.tourReferences.length+')</h3>'+(impact.tourReferences.length?impact.tourReferences.map(function(r,i){return '<button type="button" class="btn ghost alternative" data-impact-tour="'+i+'">'+esc(r.tourTitle)+' · '+(r.step?'step '+r.step:'link '+r.link)+' · '+esc(r.stepTitle)+'<br>'+esc(r.path)+':'+r.start+'–'+r.end+' · '+esc(r.symbol)+'</button>';}).join(''):'<p class="sub">'+(impact.toursStatus==='available'?'No exact citations for this file.':'No curated tours available for this snapshot.')+'</p>')+
    '<h3>Potential boundary impacts ('+impact.boundaryImpacts.length+')</h3><p class="sub">Separate transitive paths with at least one HTTP/RPC boundary, optionally also imports. Not import-only/runtime truth; may overlap consumers.</p>'+impactRows(impact.boundaryImpacts,'boundaryImpacts')+
    '<h3>Limits</h3>'+impact.limits.map(function(l){return '<p class="sub">'+esc(l)+'</p>';}).join('')+
    '<section id="impact-chain" aria-live="polite">'+(selectedWitness?'<h3>Why included</h3><p>'+esc(selectedWitness.reason)+'</p>'+selectedWitness.edges.map(function(e){return '<p>'+esc(e.from)+' → '+esc(e.to)+' <b>('+esc(e.type)+')</b></p>';}).join('')+'<button type="button" class="btn" data-impact-inspect="'+esc(selectedWitness.id)+'">Inspect real file in map</button>':'<p class="sub">Choose a result to explain its shortest inclusion chain and inspect the real file.</p>')+'</section>';
}
function impactGraph(){
  if(!impact)return;
  answerRoute=null;answer=null;overrides={};document.getElementById('answer').textContent='';
  var rows=selectedWitness?[selectedWitness]:impact.directConsumers.concat(impact.transitiveConsumers,impact.boundaryImpacts);
  var edges=Array.from(new Map(rows.flatMap(function(r){return r.edges;}).map(function(e){return [JSON.stringify([e.from,e.to,e.type]),e];})).values());
  var ids=Array.from(new Set([impact.fileId].concat(rows.flatMap(function(r){return r.chain;}))));
  S.view='route';S.expanded=null;S.focused=impact.fileId;
  G=routeGraph({ids:ids,edges:edges});S.nodes=G.nodes;S.edges=G.edges;
  btnBack.classList.remove('hidden');crumb.textContent='Potential impact · real files · import consumers + separate HTTP/RPC boundary witnesses';
  draw();fitView(null);panelFor();renderImpact();
}
function impactHighlight(){
  if(!impact || tourController.state().active || S.view!=='route' || !S.nodes.some(function(n){return n.id===impact.fileId;}))return false;
  var vp=document.getElementById('viewport');if(!vp)return false;
  var lit=selectedWitness?new Set(selectedWitness.chain):new Set(S.nodes.map(function(n){return n.id;}));
  vp.classList.add('dimming');
  vp.querySelectorAll('g.node').forEach(function(g){
    var id=g.dataset.id;g.classList.remove('sel','rel-up','rel-down','faded','endpoint-to');
    g.classList.add(id===impact.fileId?'sel':lit.has(id)?'rel-down':'faded');
  });
  vp.querySelectorAll('path.edge').forEach(function(p){var e=G.edges[+p.dataset.e];p.classList.toggle('emph',!selectedWitness || selectedWitness.edges.some(function(x){return x.from===e.from&&x.to===e.to&&x.type===e.type;}));});
  return true;
}
function startImpact(id){
  if(tourController.state().active)exitTour();
  impact=DagGpsImpact.analyzeImpact(MAP,TOUR_DATA,id);selectedWitness=null;impactGraph();
}
function impactTarget(query){
  var m=query.trim().match(/^what could be affected if I change\s+(.+?)\??$/i) || query.trim().match(/^(?:inspect potential impact(?: of| for)?|impact(?: of| on| for))\s+(.+?)\??$/i);
  return m?m[1].trim():null;
}
// Capture only explicit impact intent. Legacy DOWNSTREAM wording remains untouched.
document.getElementById('ask-form').addEventListener('submit',function(ev){
  var target=impactTarget(document.getElementById('ask').value);
  clearImpact();
  if(target===null)return;
  ev.preventDefault();ev.stopImmediatePropagation();
  if(tourController.state().active)exitTour();
  clearAnswerHighlight();answer=null;answerRoute=null;S.focused=null;overrides={};showLayers(false);
  var result=scorer.score('locate '+target);DagGpsScorer.validateResult(result,MAP);
  var h=result.targets.locate_target;
  if(!h){document.getElementById('answer').textContent='Potential impact requires a single file target. No analysis performed.';return;}
  if(result.yes && h.yes && NODE.get(h.choice).kind==='file'){startImpact(h.choice);return;}
  var choices=(h.suggestions || h.top3).filter(function(x){return NODE.get(x.id).kind==='file';});
  document.getElementById('answer').innerHTML='<h2>Potential impact — '+esc(h.match?h.match.label:'No match')+'</h2><p>No analysis performed. Choose a real file explicitly before analysis.</p><p class="sub">'+esc(h.reason)+'</p>'+choices.map(function(x){return '<button type="button" class="btn ghost alternative" data-impact-choice="'+esc(x.id)+'">Choose '+esc(x.path || x.id)+'</button>';}).join('')+(trustUI ? trustUI.badge([]) : '');
},true);
document.getElementById('answer').addEventListener('click',function(ev){var b=ev.target.closest('[data-impact-choice]');if(b && NODE.has(b.dataset.impactChoice)&&NODE.get(b.dataset.impactChoice).kind==='file')startImpact(b.dataset.impactChoice);});
panel.addEventListener('click',function(ev){var b=ev.target.closest('[data-impact]');if(b)startImpact(b.dataset.impact);});
impactPanel.addEventListener('click',function(ev){
  if(!impact)return;
  var b=ev.target.closest('button');if(!b)return;
  if(b.id==='impact-close'){clearImpact();showLayers(false);return;}
  if(b.id==='impact-return'){if(tourController.state().active)exitTour();selectedWitness=null;impactGraph();return;}
  if(b.hasAttribute('data-impact-result')){
    selectedWitness=impact[b.dataset.impactResult][+b.dataset.impactIndex];impactGraph();
    document.getElementById('impact-chain').scrollIntoView({block:'nearest'});return;
  }
  if(b.hasAttribute('data-impact-inspect')){setFocus(b.dataset.impactInspect);return;}
  if(b.hasAttribute('data-impact-tour')){
    tourUI.openReference(impact.tourReferences[+b.dataset.impactTour]);
    // Summary survives; Return to impact graph is always available.
  }
});
document.getElementById('tour-select').addEventListener('change',clearImpact);
({start:startImpact,clear:clearImpact,highlight:impactHighlight,state:function(){return impact;}});
