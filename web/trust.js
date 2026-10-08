/* Static provenance helpers; no graph edge implies observed execution. */
(function(root){
'use strict';
const warnings = new Set(['non_source_target','unresolved_local_reference','unsupported_dynamic_construct']);
function contextual(map, ids){
  const t=map.trust;
  if(!t || t.version!==2)return {scope:'repository',findings:[],reason:'Repository-level uncertainty: legacy map has no versioned extraction findings. Runtime completeness unknown.'};
  const paths=new Set();
  for(const id of ids || []){
    const n=map.nodes.find(n=>n.id===id);
    if(n && n.kind==='file')paths.add(id);
    if(n && n.kind==='layer')for(const p of (map.layers[id] || {}).files || [])paths.add(p);
  }
  const relevant=t.findings.filter(f=>warnings.has(f.category) && (paths.has(f.path)||paths.has(f.target)));
  const unscanned=t.scope.unscanned_paths.filter(p=>paths.has(p));
  return {scope:relevant.length || unscanned.length?'context':'repository',findings:relevant,unscanned,
    reason:relevant.length || unscanned.length ? 'Contextual extraction limitation: '+relevant.length+' observed findings; '+unscanned.length+' selected/context files outside extraction scan. Static links are not runtime proof.' :
    'Repository-level uncertainty: no traceable blind spot observed for this selection. Findings are not exhaustive; runtime completeness and coverage unknown.'};
}
const api={contextual};
if(typeof module==='object' && module.exports)module.exports=api; else root.DagGpsTrust=api;
})(typeof globalThis!=='undefined'?globalThis:this);
