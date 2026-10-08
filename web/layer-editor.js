/* Pure offline authoring operations; all imported text is data, never code. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.LayerEditor=api;})(typeof globalThis!=='undefined'?globalThis:this, function(){
'use strict';
const DRAFT='dag-gps-layer-draft/v1', SPEC='dag-gps-reviewed-layers/v1', MAX=8*1024*1024;
const copy=x=>JSON.parse(JSON.stringify(x));
function assert(ok,message){if(!ok)throw new Error(message);}
function strings(a){return Array.isArray(a)&&a.every(x=>typeof x==='string'&&x.length>0);}
function validate(d){
 assert(d&&d.schema===DRAFT,'Expected layer draft v1');
 assert(typeof d.repo==='string'&&typeof d.commit==='string'&&/^[a-f0-9]{40}$/.test(d.commit),'Invalid repository/commit');
 assert(strings(d.source_files)&&d.source_files.length>0&&new Set(d.source_files).size===d.source_files.length,'Invalid source inventory');
 assert(strings(d.tops),'Invalid extraction scope');
 assert(Array.isArray(d.layers)&&d.layers.length>0,'No layers');
 const ids=new Set(),known=new Set(d.source_files);
 for(const l of d.layers){assert(l&&typeof l.id==='string'&&/^[a-zA-Z0-9_-]{1,100}$/.test(l.id)&&!ids.has(l.id)&&!known.has(l.id),'Invalid/duplicate layer ID');ids.add(l.id);
 assert(typeof l.label==='string'&&l.label.trim()&&l.label.length<=500,'Invalid label');
 for(const k of ['desc','reason'])assert(l[k]===undefined||(typeof l[k]==='string'&&l[k].length<=5000),'Invalid layer '+k);
 assert(Array.isArray(l.files)&&strings(l.files)&&new Set(l.files).size===l.files.length&&l.files.every(p=>known.has(p)),'Invalid file ownership');
 assert(l.globs===undefined,'Draft uses exact files only');}
 assert(Array.isArray(d.file_edges)&&d.file_edges.every(e=>e&&known.has(e.from)&&known.has(e.to)&&['import','http','rpc'].includes(e.type)),'Invalid file edges');
 assert(d.diagnostics&&Array.isArray(d.diagnostics.unresolved)&&Array.isArray(d.diagnostics.file_cycles),'Missing extraction diagnostics');
 assert(Array.isArray(d.reference_warnings)&&d.reference_warnings.every(x=>typeof x==='string'),'Invalid migration warnings');
 return d;
}
function parse(text,base){
 assert(typeof text==='string'&&new TextEncoder().encode(text).length<=MAX,'Import exceeds 8 MiB');
 let d=JSON.parse(text);
 if(d.schema===SPEC){
  assert(base,'Reviewed specs need the original pinned draft for evidence');
  assert(d.repo===base.repo&&d.onboarding&&d.onboarding.repo===base.repo&&d.onboarding.commit===base.commit,'Repository/commit mismatch');
  assert(JSON.stringify(d.onboarding.source_files)===JSON.stringify(base.source_files)&&JSON.stringify(d.onboarding.tops)===JSON.stringify(base.tops),'Inventory/scope mismatch');
  assert(!d.manual_edges||d.manual_edges.length===0,'Manual edges unsupported');
  d={...copy(base),layers:d.layers,reference_warnings:d.onboarding.reference_warnings,reviewed:false};
 }
 validate(d);
 if(base){assert(d.repo===base.repo&&d.commit===base.commit,'Repository/commit mismatch');
  // Imported drafts cannot replace pinned evidence, inventory, scope or diagnostics.
  for(const k of ['source_files','tops','file_edges','diagnostics','trust'])assert(JSON.stringify(d[k])===JSON.stringify(base[k]),'Pinned evidence mismatch: '+k);
  d.reference_warnings=[...new Set([...base.reference_warnings,...d.reference_warnings])];
  const changed=base.layers.filter(l=>!d.layers.some(n=>n.id===l.id&&JSON.stringify([...n.files].sort())===JSON.stringify([...l.files].sort()))).map(l=>l.id);
  if(changed.length)warning(d,'Imported ownership/removed IDs differ from pinned draft: '+changed.join(', ')+'.');
 }
 return {...copy(d),reviewed:false};
}
function findings(d){
 validate(d);const owners=new Map(d.source_files.map(p=>[p,[]]));
 for(const l of d.layers)for(const p of l.files)owners.get(p).push(l.id);
 const unmapped=[],double=[];for(const [path,ids]of owners){if(!ids.length)unmapped.push(path);if(ids.length>1)double.push({path,ids});}
 const empty=d.layers.filter(l=>!l.files.length).map(l=>l.id), edges=new Map();
 for(const e of d.file_edges){const a=owners.get(e.from),b=owners.get(e.to);if(a.length!==1||b.length!==1||a[0]===b[0])continue;
  const key=a[0]+'\0'+b[0];if(!edges.has(key))edges.set(key,{from:a[0],to:b[0],evidence:[]});edges.get(key).evidence.push(e);}
 const adj=new Map(d.layers.map(l=>[l.id,[]]));for(const e of edges.values())adj.get(e.from).push(e.to);
 for(const a of adj.values())a.sort();
 // Iterative DFS matches build_map.find_cycle order; no recursion limit on large drafts.
 const color=new Map(),cycles=[];
 for(const start of [...adj.keys()].sort()){if(color.get(start))continue;const stack=[{id:start,next:0}],path=[start];color.set(start,1);
  while(stack.length){const top=stack[stack.length-1],outs=adj.get(top.id);
   if(top.next===outs.length){color.set(top.id,2);stack.pop();path.pop();continue;}
   const n=outs[top.next++];if(color.get(n)===1){cycles.push([...path.slice(path.indexOf(n)),n]);continue;}
   if(!color.get(n)){color.set(n,1);stack.push({id:n,next:0});path.push(n);}
  }
 }
 const unresolved=d.diagnostics.unresolved;
 return {unmapped,double,empty,cycles,edges:[...edges.values()],unresolved,valid:!unmapped.length&&!double.length&&!empty.length&&!cycles.length&&!unresolved.length};
}
function layer(d,id){const l=d.layers.find(x=>x.id===id);assert(l,'Unknown layer');return l;}
function edit(d,op){const n=copy(d);n.reviewed=false;op(n);validate(n);return n;}
function rename(d,id,label){return edit(d,n=>{layer(n,id).label=label;});}
function move(d,paths,target){return edit(d,n=>{const l=layer(n,target);assert(strings(paths)&&paths.every(p=>n.source_files.includes(p)),'Unknown files');for(const x of n.layers)x.files=x.files.filter(p=>!paths.includes(p));l.files=[...new Set([...l.files,...paths])].sort();});}
function warning(n,message){n.reference_warnings.push(message+' Manual alias/tour review required; no IDs rebound automatically.');}
function merge(d,ids,target){return edit(d,n=>{assert(ids.length>=2&&new Set(ids).size===ids.length&&ids.includes(target),'Choose distinct layers including retained target');const l=layer(n,target);const all=ids.flatMap(id=>layer(n,id).files);l.files=[...new Set(all)].sort();const removed=ids.filter(id=>id!==target);n.layers=n.layers.filter(x=>!removed.includes(x.id));warning(n,'Merged/removed IDs: '+removed.join(', ')+'; retained '+target+'.');});}
function split(d,id,paths,label){return edit(d,n=>{const l=layer(n,id);assert(strings(paths)&&paths.length&&new Set(paths).size===paths.length&&paths.every(p=>l.files.includes(p))&&paths.length<l.files.length,'Split a nonempty proper subset owned by selected layer');let i=1,newId;do{newId=id+'-split-'+i++;}while(n.layers.some(x=>x.id===newId));assert(newId.length<=100,'Split ID too long');l.files=l.files.filter(p=>!paths.includes(p));n.layers.push({id:newId,label,desc:'Human split from '+id,reason:'Human split; review responsibility.',files:[...paths].sort()});warning(n,'Split '+id+' into retained '+id+' and new '+newId+'; existing references still target original ID.');});}
function remove(d,id){return edit(d,n=>{assert(n.layers.length>1,'Cannot delete last layer');const l=layer(n,id);n.layers=n.layers.filter(x=>x.id!==id);warning(n,'Deleted ID '+id+'; '+l.files.length+' files now unmapped.');});}
function exportSpec(d,confirmed){const f=findings(d);assert(f.valid,'Fix coverage, empty layers, unresolved imports and dependency cycles before export');assert(confirmed===true,'Explicit human review required');return {schema:SPEC,repo:d.repo,onboarding:{reviewed:true,repo:d.repo,commit:d.commit,source_files:copy(d.source_files),tops:copy(d.tops),reference_warnings:copy(d.reference_warnings)},layers:d.layers.map(l=>({id:l.id,label:l.label,desc:l.desc||'',files:[...l.files].sort()}))};}
return {DRAFT,SPEC,MAX,validate,parse,findings,rename,move,merge,split,remove,exportSpec,copy};
});
