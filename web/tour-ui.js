// Trusted UI source evaluated inside the canvas closure. Tour text is always escaped.
var tourController = DagGpsTours.createController(TOUR_DATA);
var tourPanel = document.getElementById('tour-panel');
var tourSelect = document.getElementById('tour-select');
tourController.tours.forEach(function(t){
  var option=document.createElement('option'); option.value=t.id; option.textContent=t.title; tourSelect.appendChild(option);
});
if(!tourController.tours.length){
  tourSelect.disabled=true;
  tourSelect.options[0].textContent='No curated tours available';
  tourSelect.title=(MAP.meta.tours || {}).reason || 'No reviewed tours supplied for this snapshot.';
}
['http','message','spawn','data','import'].forEach(function(type){
  EDGE_TYPES['tour-'+type]={color:'#56d4c7',dash:type==='import'?'3 3':'14 4 2 4',title:'tour '+type+' · source direction'};
});
function tourGraph(){
  var state=tourController.state(),tour=state.active;
  var current=new Set(state.step.nodeIds);
  var links=tour.links.filter(function(l){return l.status==='source-supported'&&(current.has(l.from)||current.has(l.to));});
  var ids=Array.from(new Set(state.step.nodeIds.concat(links.flatMap(function(l){return [l.from,l.to];}))));
  var graph=routeGraph({ids:ids,edges:links.map(function(l){
    return {from:l.from,to:l.to,type:'tour-'+l.type};
  })});
  graph.edges.forEach(function(e){var link=tour.links.find(function(l){return l.from===e.from&&l.to===e.to&&'tour-'+l.type===e.type;});
    e.tip=link.label+' · '+link.status+' · '+link.from+' → '+link.to;
  });
  return graph;
}
function showTourGraph(){
  var state=tourController.state(); if(!state.active)return;
  answer=null;answerRoute=null;overrides={};document.getElementById('answer').textContent='';
  S.view='route';S.expanded=null;S.focused=state.step.nodeIds[0];
  G=tourGraph();S.nodes=G.nodes;S.edges=G.edges;
  btnBack.classList.remove('hidden');
  crumb.textContent='Current step + direct source context · not an import path or observed execution trace';
  draw();fitView(null);applyHighlight();panelFor();
  document.getElementById('viewport').classList.remove('dimming');
  var current=new Set(state.step.nodeIds);
  document.querySelectorAll('#viewport g.node').forEach(function(g){
    g.classList.remove('faded','rel-up','rel-down','sel');
    g.classList.toggle('tour-current',current.has(g.getAttribute('data-id')));
  });
}
function showTourLayers(){
  var state=tourController.state();if(!state.active)return;
  var involved=new Set(state.active.steps.flatMap(function(s){return s.nodeIds.map(function(id){var n=NODE.get(id);return n.kind==='layer'?id:n.layer;});}));
  showLayers(false);
  document.querySelectorAll('#viewport g.node').forEach(function(g){
    g.classList.toggle('tour-involved',involved.has(g.dataset.id));
    g.classList.toggle('faded',!involved.has(g.dataset.id));
  });
  crumb.textContent='Tour overview · involved layers highlighted · original dependency edges, NOT runtime order';
}
function evidenceHtml(e){
  return '<button class="btn ghost tour-citation" type="button" data-tour-evidence="'+esc(JSON.stringify(e))+'">'+
    esc(e.path)+':'+e.start+'–'+e.end+' · '+esc(e.symbol)+'</button>';
}
function renderTour(){
  var s=tourController.state();tourPanel.hidden=!s.active;
  if(!s.active){tourPanel.textContent='';return;}
  var tour=s.active,step=s.step;
  var layers=Array.from(new Set(tour.steps.flatMap(function(x){return x.nodeIds.map(function(id){var n=NODE.get(id);return n.kind==='layer'?id:n.layer;});})));
  tourPanel.innerHTML='<h2>'+esc(tour.title)+'</h2><details id="tour-overview"><summary>Overview · '+layers.length+' layers</summary><p>'+esc(tour.overview)+'</p><div class="chips">'+layers.map(function(id){return '<button class="chip" data-tour-locate="'+esc(id)+'">'+esc(layerLabel(id))+'</button>';}).join('')+
    '</div><button type="button" class="btn ghost" id="tour-layers">View involved layers</button><button type="button" class="btn ghost" id="tour-step-view">Return to step</button><p>Audited '+esc(TOUR_DATA.repo)+' @ '+esc(TOUR_DATA.commit)+'. Source-supported walkthrough; not a measured execution or confidence score.</p></details>'+
    '<p id="tour-progress" role="status">Step '+(s.index+1)+' of '+tour.steps.length+'</p><h3 class="tour-step-title">'+esc(step.title)+'</h3>'+
    '<p>'+esc(step.does)+'</p><dl><dt>Receives</dt><dd>'+esc(step.receives)+'</dd><dt>Passes on</dt><dd>'+esc(step.passes)+'</dd></dl><p class="sub">'+esc(step.explanation)+'</p>'+
    '<div class="tour-controls"><button type="button" class="btn ghost" id="tour-prev" '+(s.index===0?'disabled':'')+'>Previous</button><button type="button" class="btn" id="tour-next" '+(s.index===tour.steps.length-1?'disabled':'')+'>Next</button><button type="button" class="btn ghost" id="tour-reset">Reset</button><button type="button" class="btn ghost" id="tour-exit">Exit tour</button></div>'+
    '<h3>Source evidence · inspect offline</h3>'+step.evidence.map(evidenceHtml).join('')+
    '<details><summary>Directed tour links (separate from imports)</summary><p>Teal dash-dot edges are curated HTTP, spawn/message or data flow. Arrow direction is exactly from → to below; not consumer → dependency unless explicitly typed import. Inferred/unverified links are not drawn.</p>'+tour.links.map(function(l){return '<p>'+esc(l.from)+' → '+esc(l.to)+'<br><b>'+esc(l.type)+' · '+esc(l.status)+'</b> · '+esc(l.label)+'</p>'+l.evidence.map(evidenceHtml).join('');}).join('')+'</details>';
  document.getElementById('tour-layers').onclick=showTourLayers;
  document.getElementById('tour-step-view').onclick=showTourGraph;
  document.getElementById('tour-prev').onclick=function(){tourController.move(-1);tourStep();};
  document.getElementById('tour-next').onclick=function(){tourController.move(1);tourStep();};
  document.getElementById('tour-reset').onclick=function(){tourController.reset();tourStep();};
  document.getElementById('tour-exit').onclick=function(){exitTour();};
}
function tourStep(){showTourGraph();renderTour();}
function startTour(id){closeTourEvidence();tourController.start(id);tourSelect.value=id;tourStep();}
function exitTour(){closeTourEvidence();tourController.exit();tourSelect.value='';renderTour();showLayers(false);}
function resolveTourQuery(query){var found=tourController.resolve(query);if(found){startTour(found.id);return true;}return false;}
tourSelect.onchange=function(){if(tourSelect.value)startTour(tourSelect.value);else exitTour();};
var evidenceDialog=document.getElementById('tour-evidence');
var evidenceReturnFocus=null;
function closeTourEvidence(){if(evidenceDialog.open)evidenceDialog.close();}
tourPanel.addEventListener('click',function(ev){
  var locate=ev.target.closest('[data-tour-locate]');
  if(locate){setFocus(locate.dataset.tourLocate);return;}
  var target=ev.target.closest('[data-tour-evidence]');if(!target)return;
  var e=JSON.parse(target.dataset.tourEvidence);
  evidenceReturnFocus=target;
  document.getElementById('evidence-title').textContent=e.path+':'+e.start+'–'+e.end+' · '+e.symbol;
  document.getElementById('evidence-source').textContent=e.excerpt.split('\n').map(function(line,i){return (e.start+i)+' | '+line;}).join('\n');
  document.getElementById('evidence-meta').textContent=TOUR_DATA.repo+' @ '+TOUR_DATA.commit+'. Only this cited excerpt is bundled; not the entire repository.';
  var permalink=document.getElementById('evidence-permalink');
  permalink.hidden=!/^[\w.-]+\/[\w.-]+$/.test(TOUR_DATA.repo);
  permalink.href='https://github.com/'+TOUR_DATA.repo+'/blob/'+TOUR_DATA.commit+'/'+e.path.split('/').map(encodeURIComponent).join('/')+'#L'+e.start+'-L'+e.end;
  document.getElementById('evidence-locate').onclick=function(){closeTourEvidence();setFocus(e.nodeId);};
  evidenceDialog.showModal();
});
document.getElementById('evidence-close').onclick=closeTourEvidence;
evidenceDialog.addEventListener('close',function(){if(evidenceReturnFocus&&evidenceReturnFocus.isConnected)evidenceReturnFocus.focus();});
document.addEventListener('keydown',function(ev){
  if(!tourController.state().active || evidenceDialog.open || ev.defaultPrevented || ev.altKey || ev.ctrlKey || ev.metaKey || /^(INPUT|TEXTAREA|SELECT)$/.test(ev.target.tagName) || ev.target.isContentEditable)return;
  if(ev.key==='ArrowRight'||ev.key==='ArrowLeft'){ev.preventDefault();tourController.move(ev.key==='ArrowRight'?1:-1);tourStep();}
  if(ev.key==='Escape'){ev.preventDefault();exitTour();}
},true);
renderTour();
function openTourReference(ref){
  startTour(ref.tourId);
  var t=tourController.state().active;
  var index=ref.step?ref.step-1:t.steps.findIndex(function(s){return s.evidence.some(function(e){return e.path===ref.path;});});
  for(var i=0;i<Math.max(0,index);i++)tourController.move(1);
  tourStep();
  var citation=Array.from(tourPanel.querySelectorAll('[data-tour-evidence]')).find(function(el){var e=JSON.parse(el.dataset.tourEvidence);return e.path===ref.path&&e.start===ref.start&&e.end===ref.end;});
  if(citation){var detail=citation.closest('details');if(detail)detail.open=true;citation.click();}
}
({controller:tourController,resolve:resolveTourQuery,exit:exitTour,openReference:openTourReference});
