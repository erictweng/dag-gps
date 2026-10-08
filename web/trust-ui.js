// Trusted closure UI. Findings/paths are text, never executable data.
var trustPanel=document.getElementById('trust-panel'),trustPaths=[];
var trustLabels={resolved_source:'Resolved source link',non_source_target:'Non-source target',unresolved_local_reference:'Unresolved local reference',unsupported_dynamic_construct:'Unsupported dynamic construct',external_dependency:'External dependency'};
function trustBadge(ids){
  var c=DagGpsTrust.contextual(MAP,ids);
  return '<div class="trust-warning" data-trust-scope="'+c.scope+'"><b>'+esc(c.reason)+'</b>'+c.findings.map(function(f){return '<p>'+esc(f.path)+' → '+esc(f.target)+'<br>'+esc(f.reason)+'</p>';}).join('')+(c.unscanned || []).map(function(p){return '<p>'+esc(p)+' — outside extraction scan</p>';}).join('')+'<button type="button" class="btn ghost" data-trust-context="'+esc(JSON.stringify(ids || []))+'">Inspect extraction findings</button></div>';
}
function renderTrust(){
  var t=MAP.trust;
  if(!t){document.getElementById('trust-summary').textContent='Map trust · legacy provenance unavailable';return;}
  document.getElementById('trust-summary').textContent='Map trust · '+t.scope.extracted_files+' / '+t.scope.inventory_files+' files scanned · runtime completeness unknown';
  var filter=document.getElementById('trust-filter').value,path=document.getElementById('trust-path').value.trim();
  var rows=t.findings.filter(function(f){return (!filter || f.category===filter) && (!path || f.path.includes(path)||f.target.includes(path)) && (!trustPaths.length || trustPaths.includes(f.path)||trustPaths.includes(f.target));});
  document.getElementById('trust-meta').textContent=MAP.meta.repo+' @ '+t.snapshot_commit+' · '+t.extractor+' · JS inputs: '+t.scope.js_inputs.join(', ')+'. Python: '+t.scope.python+'. SQL: '+t.scope.sql+'. Inventory denominator: '+t.scope.inventory_files+' included source files; scanned '+t.scope.extracted_files+', unscanned '+t.scope.unscanned_paths.length+'. '+(trustPaths.length?'Context paths: '+trustPaths.join(', ')+'. ':'Repository findings. ')+'Tours '+(MAP.meta.tours || {}).status+': '+(MAP.meta.tours || {}).reason;
  document.getElementById('trust-counts').textContent=Object.keys(trustLabels).map(function(k){return trustLabels[k]+': '+t.counts[k];}).join(' · ');
  document.getElementById('trust-findings').innerHTML='<p>'+rows.length+' matching findings. '+(!rows.length?'No observed matches, not proof of completeness.':'')+'</p>'+rows.map(function(f){return '<article class="trust-finding"><b>'+esc(trustLabels[f.category])+'</b><p>'+esc(f.path)+' → '+esc(f.target)+'</p><p>'+esc(f.reason)+'</p><small>Evidence: '+esc(f.evidence)+'</small>'+(NODE.has(f.path)?'<button type="button" class="btn ghost" data-trust-locate="'+esc(f.path)+'">Locate source file</button>':'<p>Path not mapped; navigation unavailable.</p>')+'</article>';}).join('');
  document.getElementById('trust-limits').innerHTML='<p>Evidence tiers: resolved lexical import ≠ curated source-supported runtime walkthrough ≠ inferred/unverified literal boundary or manual layer link. No observed execution inferred from imports.</p>'+t.limitations.map(function(l){return '<p>'+esc(l)+'</p>';}).join('')+'<p>File cycles retained: '+t.file_cycles.length+'. Layer cycles require grouping review; no true edges are erased.</p><details><summary>Unscanned inventory paths ('+t.scope.unscanned_paths.length+')</summary>'+t.scope.unscanned_paths.map(function(p){return '<p>'+esc(p)+'</p>';}).join('')+'</details>';
}
document.getElementById('trust-filter').onchange=renderTrust;
document.getElementById('trust-path').oninput=renderTrust;
document.getElementById('trust-reset').onclick=function(){trustPaths=[];document.getElementById('trust-path').value='';renderTrust();};
document.addEventListener('click',function(ev){
  var b=ev.target.closest('[data-trust-context]');
  if(b){var ids=JSON.parse(b.dataset.trustContext);trustPaths=ids.flatMap(function(id){var n=NODE.get(id);return n&&n.kind==='layer'?(MAP.layers[id].files || []):[id];});document.getElementById('trust-filter').value='';document.getElementById('trust-path').value='';trustPanel.open=true;renderTrust();trustPanel.scrollIntoView({block:'nearest'});}
  b=ev.target.closest('[data-trust-locate]');if(b && NODE.has(b.dataset.trustLocate))setFocus(b.dataset.trustLocate);
});
renderTrust();
({badge:trustBadge,render:renderTrust});
