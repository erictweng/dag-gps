/* Static potential impact, not execution or coverage. Consumer -> dependency. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.DagGpsImpact = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const compare = (a, b) => a < b ? -1 : a > b ? 1 : 0;
  const edgeKey = e => JSON.stringify([e.from, e.to, e.type]);
  function testReason(n) {
    if (n.is_test === true || n.classification === 'test') return 'Explicit test classification';
    const p = n.path || n.id;
    if (/(^|\/)(tests?|__tests__|e2e)(\/|$)/.test(p)) return 'Test directory path rule';
    if (/(^|\/)test_[^/]+\.py$/.test(p) || /\.(test|spec)\.(c?[jt]sx?|mjs)$/.test(p)) return 'Test source path rule';
    return null;
  }
  function analyzeImpact(map, tours, fileId) {
    const nodes = new Map(map.nodes.map(n => [n.id, n]));
    if (nodes.size !== map.nodes.length) throw new Error('Duplicate node IDs');
    if (!nodes.has(fileId) || nodes.get(fileId).kind !== 'file') throw new Error('Impact requires a known file ID: ' + fileId);
    const files = new Set([...nodes.values()].filter(n => n.kind === 'file').map(n => n.id));
    const edges = [...new Map((map.file_edges || []).map(e => [edgeKey(e), {from:e.from,to:e.to,type:e.type}])).values()].sort((a,b) => compare(edgeKey(a),edgeKey(b)));
    for (const e of edges) if (!files.has(e.from) || !files.has(e.to)) throw new Error('Unknown/non-file impact edge endpoint');
    const reverse = new Map([...files].map(id => [id, []]));
    edges.forEach(e => { if (['import','http','rpc'].includes(e.type)) reverse.get(e.to).push(e); });
    // State includes whether a boundary was crossed: shortest witness with at
    // least one HTTP/RPC is different from shortest import-only witness.
    function bfs(boundaries) {
      const initial = {id:fileId,boundary:false,chain:[fileId],edges:[]};
      const queue = [initial], seen = new Set([JSON.stringify([fileId,false])]), results = new Map();
      for (let i=0;i<queue.length;i++) {
        const state = queue[i];
        for (const e of reverse.get(state.id)) {
          if (!boundaries && e.type !== 'import') continue;
          // Never include or traverse origin again, including boundary cycles.
          if (e.from === fileId) continue;
          const boundary = state.boundary || e.type !== 'import';
          const key = JSON.stringify([e.from,boundary]);
          if (seen.has(key)) continue;
          seen.add(key);
          const next = {id:e.from,boundary,chain:[e.from,...state.chain],edges:[e,...state.edges]};
          queue.push(next);
          if ((!boundaries || boundary) && !results.has(next.id)) results.set(next.id, {
            id:next.id,path:nodes.get(next.id).path || next.id,distance:next.edges.length,
            chain:next.chain,edges:next.edges,
            reason:boundary ? 'Reverse import/HTTP/RPC reachability with at least one HTTP/RPC boundary; potential only' : 'Observed reverse static import reachability; not runtime or coverage proof'
          });
        }
      }
      return [...results.values()].sort((a,b) => a.distance-b.distance || compare(a.id,b.id));
    }
    const imports = bfs(false), boundaryImpacts = bfs(true);
    const linkedTests = imports.filter(r => testReason(nodes.get(r.id))).map(r => ({...r,testEvidence:testReason(nodes.get(r.id))}));
    const tourReferences = [], orphanTourReferences = [];
    let toursStatus = 'unavailable';
    if (tours) {
      const commit = map.meta.snapshot_commit || map.meta.commit;
      const matches = typeof commit === 'string' && typeof tours.commit === 'string' && Math.min(commit.length,tours.commit.length)>=7 && (commit.startsWith(tours.commit) || tours.commit.startsWith(commit));
      if (tours.version !== 1 || tours.repo !== map.meta.repo || !matches || !Array.isArray(tours.tours)) throw new Error('Tours must be validated version-1 raw or compiled data for the exact map snapshot');
      toursStatus = 'available';
      for (const t of tours.tours) {
        function citations(es, context) {
          for (const e of es || []) {
            if (!files.has(e.path) || (e.nodeId && e.nodeId !== e.path)) { orphanTourReferences.push({tourId:t.id,path:e.path,reason:'Citation has no matching real file ID'}); continue; }
            if (e.path !== fileId) continue;
            if (!Number.isInteger(e.start) || !Number.isInteger(e.end) || e.start < 1 || e.end < e.start) throw new Error('Invalid tour citation line range');
            tourReferences.push({...context,tourId:t.id,tourTitle:t.title,path:e.path,start:e.start,end:e.end,symbol:e.symbol || '',evidence:{...e},reason:'Exact source citation; not proof the narrative breaks'});
          }
        }
        (t.steps || []).forEach((s,i) => citations(s.evidence,{kind:'step',step:i+1,stepTitle:s.title}));
        (t.links || []).forEach((l,i) => citations(l.evidence,{kind:'link',link:i+1,step:null,stepTitle:l.label || 'Tour link'}));
      }
    }
    const refs = [...new Map(tourReferences.map(r => [JSON.stringify([r.tourId,r.kind,r.step,r.link,r.path,r.start,r.end,r.symbol]),r])).values()];
    refs.sort((a,b) => compare(a.tourId,b.tourId) || compare(a.kind,b.kind) || (a.step || a.link)-(b.step || b.link) || a.start-b.start || a.end-b.end || compare(a.symbol,b.symbol));
    return {fileId,snapshot:map.meta.snapshot_commit || map.meta.commit,
      directConsumers:imports.filter(r => r.distance===1),transitiveConsumers:imports.filter(r => r.distance>1),
      linkedTests,coverage:'unknown',tourReferences:refs,toursStatus,orphanTourReferences,
      boundaryImpacts,
      limits:[
        'Potentially affected, not guaranteed to break. Static snapshot only; not a complete runtime graph.',
        'Direct/transitive consumers use reverse import edges only (consumer → dependency). Realtime excluded.',
        'Linked tests are observed import reachability, not execution or coverage proof. Coverage unknown even when linked tests exist.',
        'Boundary section includes transitive reverse import/HTTP/RPC paths with at least one HTTP/RPC; may overlap import consumers, never merged into import truth.',
        'Tour references cite exactly this file, including step and link citations; not inferred narrative breakage.',
        toursStatus==='available' ? 'Tours supplied by the validated raw/compiled version-1 snapshot pipeline.' : 'No curated tours available for this snapshot.',
        ...(orphanTourReferences.length ? ['Orphan tour citations excluded: '+orphanTourReferences.length] : [])
      ]};
  }
  return {analyzeImpact,testReason};
});
