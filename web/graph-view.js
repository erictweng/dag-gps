/* DAG GPS workspace graph view.
 * Pure part (Node-testable): layoutMap(map) and highlightFor(packet).
 * DOM part (browser): createGraphView(container, options).
 * Layout: consumers left -> dependencies right (column = longest consumer depth of the
 * file's strongly connected component, so genuine cycles share a column and keep every
 * edge), proposed groups as labeled horizontal lanes. All labels are inert text. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.DagGpsGraphView = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const LIMITS = Object.freeze({maxFileNodes: 1500});
  const G = Object.freeze({margin: 24, colW: 230, nodeW: 196, nodeH: 24, row: 32, laneTop: 30, laneBottom: 12, laneGap: 10});
  const compare = (a, b) => (a < b ? -1 : a > b ? 1 : 0);
  const edgeKey = e => e.from + '\u0000' + e.to + '\u0000' + e.type;

  // Iterative Tarjan SCC; returns component index per id (deterministic over sorted ids/adjacency).
  function components(ids, adj) {
    let index = 0, count = 0;
    const idx = new Map(), low = new Map(), on = new Set(), stack = [], comp = new Map();
    for (const start of ids) {
      if (idx.has(start)) continue;
      const work = [[start, 0]];
      idx.set(start, index); low.set(start, index); index++; stack.push(start); on.add(start);
      while (work.length) {
        const frame = work[work.length - 1], v = frame[0], next = adj.get(v);
        if (frame[1] < next.length) {
          const w = next[frame[1]++];
          if (!idx.has(w)) {
            idx.set(w, index); low.set(w, index); index++; stack.push(w); on.add(w);
            work.push([w, 0]);
          } else if (on.has(w)) low.set(v, Math.min(low.get(v), idx.get(w)));
        } else {
          work.pop();
          if (work.length) { const u = work[work.length - 1][0]; low.set(u, Math.min(low.get(u), low.get(v))); }
          if (low.get(v) === idx.get(v)) {
            let w;
            do { w = stack.pop(); on.delete(w); comp.set(w, count); } while (w !== v);
            count++;
          }
        }
      }
    }
    return {comp, count};
  }

  // Column = longest path from a pure consumer in the condensed (acyclic) graph.
  function columns(ids, edges) {
    const adj = new Map(ids.map(id => [id, []]));
    for (const e of edges) adj.get(e.from).push(e.to);
    for (const list of adj.values()) list.sort(compare);
    const {comp, count} = components(ids, adj);
    const out = Array.from({length: count}, () => new Set()), indeg = new Array(count).fill(0);
    for (const e of edges) {
      const a = comp.get(e.from), b = comp.get(e.to);
      if (a !== b && !out[a].has(b)) { out[a].add(b); indeg[b]++; }
    }
    const depth = new Array(count).fill(0), queue = [];
    for (let c = 0; c < count; c++) if (!indeg[c]) queue.push(c);
    for (let i = 0; i < queue.length; i++) for (const d of out[queue[i]]) {
      depth[d] = Math.max(depth[d], depth[queue[i]] + 1);
      if (--indeg[d] === 0) queue.push(d);
    }
    return new Map(ids.map(id => [id, depth[comp.get(id)]]));
  }

  function place(items, edges, laneOf, laneLabel) {
    const ids = items.map(n => n.id).sort(compare);
    const col = columns(ids, edges);
    const laneIds = [...new Set(items.map(laneOf))].sort((a, b) => compare(laneLabel(a), laneLabel(b)) || compare(a, b));
    const byId = new Map(items.map(n => [n.id, n]));
    const lanes = [], nodes = [];
    let y = G.margin, maxCol = 0;
    for (const lane of laneIds) {
      const members = ids.filter(id => laneOf(byId.get(id)) === lane);
      const perCol = new Map();
      for (const id of members) {
        const c = col.get(id);
        maxCol = Math.max(maxCol, c);
        if (!perCol.has(c)) perCol.set(c, []);
        perCol.get(c).push(id);
      }
      const rows = Math.max(1, ...[...perCol.values()].map(list => list.length));
      const h = G.laneTop + rows * G.row + G.laneBottom;
      lanes.push({id: lane, label: laneLabel(lane), y, h, count: members.length});
      for (const [c, list] of perCol) list.forEach((id, r) => {
        const n = byId.get(id);
        nodes.push({id, label: n.label, path: n.path || null, layer: lane, column: c,
          x: G.margin + c * G.colW, y: y + G.laneTop + r * G.row, w: G.nodeW, h: G.nodeH});
      });
      y += h + G.laneGap;
    }
    nodes.sort((a, b) => compare(a.id, b.id));
    const drawn = edges.map(e => ({from: e.from, to: e.to, type: e.type, weight: e.weight === undefined ? null : e.weight,
      back: col.get(e.to) <= col.get(e.from)})).sort((a, b) => compare(edgeKey(a), edgeKey(b)));
    return {nodes, edges: drawn, lanes, width: G.margin * 2 + (maxCol + 1) * G.colW, height: y + G.margin};
  }

  function layoutMap(map) {
    const all = map.nodes || [];
    const layers = new Map(all.filter(n => n.kind === 'layer').map(n => [n.id, n]));
    const files = all.filter(n => n.kind === 'file');
    const label = id => (layers.get(id) && layers.get(id).label) || id || 'ungrouped';
    const unique = list => [...new Map(list.map(e => [edgeKey(e), e])).values()];
    if (files.length > LIMITS.maxFileNodes) {
      const ids = new Set(layers.keys());
      const edges = unique((map.edges || []).filter(e => e.type !== 'realtime' && ids.has(e.from) && ids.has(e.to)));
      const items = [...layers.values()].map(n => ({id: n.id, label: n.label || n.id, path: null}));
      const placed = place(items, edges, () => 'groups', () => 'Proposed groups');
      return Object.assign({mode: 'groups', notice: files.length + ' mapped files is too many to draw individually; showing proposed groups. Use the file list and questions to reach individual files.'}, placed);
    }
    const ids = new Set(files.map(n => n.id));
    const edges = unique((map.file_edges || []).filter(e => e.type !== 'realtime' && ids.has(e.from) && ids.has(e.to)));
    const placed = place(files, edges, n => n.layer || 'ungrouped', label);
    return Object.assign({mode: 'files', notice: null}, placed);
  }

  const EMPTY = () => ({mode: 'none', dim: false, nodes: new Set(), edges: new Set(), seed: null, kind: null});
  // Only a confident match dims the rest. Uncertain answers never highlight a guess.
  function highlightFor(packet) {
    if (!packet) return EMPTY();
    if (packet.status === 'no-path') {
      return {mode: 'mark', dim: false, nodes: new Set(packet.selectedNodeIds), edges: new Set(), seed: null, kind: 'relevant'};
    }
    if (packet.status !== 'matched' || !packet.selectedNodeIds.length) return EMPTY();
    return {mode: 'highlight', dim: true, nodes: new Set(packet.selectedNodeIds),
      edges: new Set(packet.selectedEdges.map(edgeKey)), seed: packet.seedNodeId || null, kind: packet.highlightState};
  }
  // Observed direct links of one file, used when the user selects a file.
  function neighborhood(map, id) {
    const edges = (map.file_edges || []).filter(e => e.type !== 'realtime' && (e.from === id || e.to === id));
    return {mode: 'highlight', dim: true, nodes: new Set([id, ...edges.map(e => e.from), ...edges.map(e => e.to)]),
      edges: new Set(edges.map(edgeKey)), seed: id, kind: 'relevant'};
  }

  // ---------------------------------------------------------------- DOM ---
  const SVG = 'http://www.w3.org/2000/svg';
  function el(name, attrs, parent) {
    const node = document.createElementNS(SVG, name);
    for (const [k, v] of Object.entries(attrs || {})) node.setAttribute(k, String(v));
    if (parent) parent.appendChild(node);
    return node;
  }
  function shorten(text, max) { return text.length > max ? '…' + text.slice(text.length - max + 1) : text; }

  function createGraphView(container, options = {}) {
    let layout = null, nodeEls = new Map(), edgeEls = new Map(), byId = new Map();
    const reduced = () => typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;
    function render(map) {
      layout = layoutMap(map);
      byId = new Map(layout.nodes.map(n => [n.id, n]));
      nodeEls = new Map(); edgeEls = new Map();
      container.replaceChildren();
      if (layout.notice) {
        const p = document.createElement('p');
        p.className = 'graph-notice'; p.textContent = layout.notice;
        container.appendChild(p);
      }
      const svg = el('svg', {width: layout.width, height: layout.height, viewBox: '0 0 ' + layout.width + ' ' + layout.height,
        role: 'img', 'aria-label': summary(null)});
      container.appendChild(svg);
      const defs = el('defs', {}, svg);
      const marker = el('marker', {id: 'dg-arrow', viewBox: '0 0 10 10', refX: 10, refY: 5, markerWidth: 7, markerHeight: 7, orient: 'auto-start-reverse'}, defs);
      el('path', {d: 'M0,0 L10,5 L0,10 z', class: 'arrow'}, marker);
      for (const lane of layout.lanes) {
        el('rect', {x: 4, y: lane.y, width: layout.width - 8, height: lane.h, rx: 6, class: 'lane'}, svg);
        el('text', {x: 12, y: lane.y + 19, class: 'lane-label'}, svg).textContent = lane.label + ' (' + lane.count + ')';
      }
      const edgeLayer = el('g', {class: 'edges'}, svg);
      for (const e of layout.edges) {
        const a = byId.get(e.from), b = byId.get(e.to);
        const x1 = a.x + a.w, y1 = a.y + a.h / 2, x2 = b.x, y2 = b.y + b.h / 2;
        const d = e.back
          ? 'M' + (a.x + a.w / 2) + ',' + a.y + ' C' + (a.x + a.w / 2) + ',' + (a.y - 26) + ' ' + (b.x + b.w / 2) + ',' + (b.y - 26) + ' ' + (b.x + b.w / 2) + ',' + b.y
          : 'M' + x1 + ',' + y1 + ' C' + (x1 + 40) + ',' + y1 + ' ' + (x2 - 40) + ',' + y2 + ' ' + x2 + ',' + y2;
        const path = el('path', {d, class: 'edge' + (e.back ? ' back' : ''), 'marker-end': 'url(#dg-arrow)'}, edgeLayer);
        el('title', {}, path).textContent = e.from + ' → ' + e.to + ' (' + e.type + (e.weight ? ', ' + e.weight : '') + ')';
        edgeEls.set(edgeKey(e), path);
      }
      for (const n of layout.nodes) {
        const g = el('g', {class: 'node', transform: 'translate(' + n.x + ',' + n.y + ')', 'data-id': n.id}, svg);
        el('rect', {width: n.w, height: n.h, rx: 4}, g);
        el('text', {x: 8, y: 16, class: 'node-label'}, g).textContent = shorten(n.path || n.label, 28);
        el('title', {}, g).textContent = (n.path || n.label) + (n.path ? '' : ' (group)');
        g.addEventListener('click', () => options.onSelect && options.onSelect(n.id));
        nodeEls.set(n.id, g);
      }
      return layout;
    }
    function summary(h) {
      if (!layout) return 'Dependency graph';
      const base = layout.mode === 'files' ? layout.nodes.length + ' files, ' + layout.edges.length + ' links' :
        layout.nodes.length + ' groups';
      if (!h || h.mode === 'none') return 'Dependency graph: ' + base + '. Nothing highlighted.';
      return 'Dependency graph: ' + base + '. ' + h.nodes.size + ' highlighted' + (h.seed ? ', centered on ' + h.seed : '') + '.';
    }
    function apply(h) {
      h = h || EMPTY();
      container.dataset.highlight = h.mode;
      for (const [id, g] of nodeEls) {
        const state = id === h.seed ? 'seed' : h.nodes.has(id) ? 'on' : h.dim ? 'dim' : '';
        if (state) g.setAttribute('data-state', state); else g.removeAttribute('data-state');
        if (h.kind) g.setAttribute('data-kind', h.kind); else g.removeAttribute('data-kind');
      }
      for (const [key, path] of edgeEls) {
        const state = h.edges.has(key) ? 'on' : h.dim ? 'dim' : '';
        if (state) path.setAttribute('data-state', state); else path.removeAttribute('data-state');
      }
      const svg = container.querySelector('svg');
      if (svg) svg.setAttribute('aria-label', summary(h));
      const focus = h.seed || [...h.nodes][0];
      if (focus && nodeEls.has(focus)) nodeEls.get(focus).scrollIntoView({block: 'center', inline: 'center', behavior: reduced() ? 'auto' : 'smooth'});
    }
    return {render, apply, layout: () => layout, has: id => nodeEls.has(id)};
  }

  return {layoutMap, highlightFor, neighborhood, edgeKey, createGraphView, LIMITS};
});
