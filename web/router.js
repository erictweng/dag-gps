/* Directed consumer -> dependency routing. No inference or realtime traversal. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.DagGpsRouter = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  function createRouter(map) {
    const nodes = new Map(map.nodes.map(n => [n.id, n]));
    if (nodes.size !== map.nodes.length) throw new Error('Duplicate node IDs');
    const allEdges = [...(map.edges || []), ...(map.file_edges || [])];
    const edges = allEdges.filter(e => e.type !== 'realtime').sort((a,b) => {
      const ak = JSON.stringify([a.from,a.to,a.type]), bk = JSON.stringify([b.from,b.to,b.type]);
      return ak < bk ? -1 : ak > bk ? 1 : 0;
    });
    for (const e of allEdges) {
      if (!nodes.has(e.from) || !nodes.has(e.to)) throw new Error('Unknown edge endpoint');
      if (nodes.get(e.from).kind !== nodes.get(e.to).kind) throw new Error('Mixed graph edge');
    }
    function requireId(id) { if (!nodes.has(id)) throw new Error('Unknown node ID: ' + id); }
    function adjacency(reverse) {
      const adj = new Map([...nodes.keys()].map(id => [id, new Set()]));
      edges.forEach(e => adj.get(reverse ? e.to : e.from).add(reverse ? e.from : e.to));
      return new Map([...adj].map(([id, ids]) => [id, [...ids].sort()]));
    }
    const forward = adjacency(false), backward = adjacency(true);
    function reachable(id, reverse) {
      requireId(id);
      const seen = new Set([id]), queue = [id], adj = reverse ? backward : forward;
      for (let i = 0; i < queue.length; i++) for (const next of adj.get(queue[i])) {
        if (!seen.has(next)) { seen.add(next); queue.push(next); }
      }
      return queue.slice(1);
    }
    function shortestPath(from, to) {
      requireId(from); requireId(to);
      if (nodes.get(from).kind !== nodes.get(to).kind) return null;
      const prev = new Map([[from, null]]), queue = [from];
      for (let i = 0; i < queue.length; i++) {
        const id = queue[i];
        if (id === to) {
          const path = []; let cursor = to;
          while (cursor !== null) { path.push(cursor); cursor = prev.get(cursor); }
          return path.reverse();
        }
        for (const next of forward.get(id)) if (!prev.has(next)) { prev.set(next, id); queue.push(next); }
      }
      return null;
    }
    function route(op, from, to) {
      requireId(from);
      if (!['LOCATE', 'UPSTREAM', 'DOWNSTREAM', 'PATH'].includes(op)) throw new Error('Unsupported operation');
      let ids = [from], path = null, status = 'Located node';
      if (op === 'PATH') {
        requireId(to); path = shortestPath(from, to); ids = path || [...new Set([from, to])];
        status = path ? 'Directed route found' : 'No directed route found';
        if (nodes.get(from).kind !== nodes.get(to).kind) status += ' — mixed layer/file endpoints unsupported (no conversion)';
      } else if (op !== 'LOCATE') {
        ids.push(...reachable(from, op === 'DOWNSTREAM'));
        status = (op === 'UPSTREAM' ? 'Dependencies' : 'Dependents') + ': ' + (ids.length - 1);
      }
      const set = new Set(ids);
      const selectedEdges = op === 'PATH' ? (path ? edges.filter(e => path.some((id, i) => id === e.from && path[i + 1] === e.to)) : []) :
        op === 'LOCATE' ? [] : edges.filter(e => set.has(e.from) && set.has(e.to));
      return {op, from, to: op === 'PATH' ? to : null, ids, path, edges: selectedEdges, status,
        kind: nodes.get(from).kind === (to ? nodes.get(to).kind : nodes.get(from).kind) ? nodes.get(from).kind : 'mixed'};
    }
    return {reachable, shortestPath, route};
  }
  return {createRouter};
});
