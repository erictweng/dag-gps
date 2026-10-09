/* Shared System 1 query service: one deterministic evidence packet for browser,
 * worker and agent consumers. Wraps the unchanged scorer/router; no model calls,
 * no network, no source execution. Uncertain results never highlight a guess. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory(require('./scorer.js'), require('./router.js'));
  } else {
    root.DagGpsQueryService = factory(root.DagGpsScorer, root.DagGpsRouter);
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function (Scorer, Router) {
  'use strict';
  const PACKET_SCHEMA = 'dag-gps-evidence/v1';
  const SNAPSHOT_SCHEMA = 'dag-gps-workspace/v1';
  // Mirrors app/contracts.py bounds; a full page leaves room for the seed.
  const LIMITS = Object.freeze({selectedNodes: 200, selectedEdges: 400, witnesses: 200,
    alternatives: 20, sourceRefs: 200, queryChars: 2048});
  const STATIC_LIMITATION = 'Static extracted relationships only; dynamic imports, runtime calls and unsupported files may be missing.';
  const compare = (a, b) => (a < b ? -1 : a > b ? 1 : 0);
  const edgeKey = e => JSON.stringify([e.from, e.to, e.type]);

  function requireSnapshot(snapshot) {
    if (!snapshot || snapshot.schema !== SNAPSHOT_SCHEMA || !snapshot.map || !Array.isArray(snapshot.map.nodes))
      throw new Error('querySnapshot requires a dag-gps-workspace/v1 snapshot from the trusted store');
    for (const field of ['projectId', 'snapshotId', 'mapSha256', 'scorerSha256'])
      if (typeof snapshot[field] !== 'string' || !snapshot[field]) throw new Error('Snapshot missing ' + field);
    if (!snapshot.source || typeof snapshot.source.manifestSha256 !== 'string')
      throw new Error('Snapshot missing source manifest digest');
  }

  function parseContinuation(value) {
    if (value === undefined || value === null) return 0;
    const m = typeof value === 'string' && /^offset:(\d{1,9})$/.exec(value);
    if (!m) throw new Error('Invalid continuation');
    return Number(m[1]);
  }

  function createQueryService(snapshot, options = {}) {
    requireSnapshot(snapshot);
    const map = snapshot.map;
    const scorer = Scorer.createScorer(map, options.learnedAliases || []);
    const router = Router.createRouter(map);
    const nodes = new Map(map.nodes.map(n => [n.id, n]));
    const inventory = new Map((snapshot.inventory || []).map(f => [f.path, f]));
    // Traversal edges exactly as the router uses them (realtime excluded), sorted deterministically.
    const edges = [...(map.edges || []), ...(map.file_edges || [])]
      .filter(e => e.type !== 'realtime')
      .map(e => ({from: e.from, to: e.to, type: e.type}))
      .sort((a, b) => compare(edgeKey(a), edgeKey(b)));
    const firstEdge = new Map();
    for (const e of edges) {
      const k = JSON.stringify([e.from, e.to]);
      if (!firstEdge.has(k)) firstEdge.set(k, e);
    }
    const hop = (a, b) => firstEdge.get(JSON.stringify([a, b]));
    const forward = new Map([...nodes.keys()].map(id => [id, []]));
    const backward = new Map([...nodes.keys()].map(id => [id, []]));
    for (const e of edges) { forward.get(e.from).push(e.to); backward.get(e.to).push(e.from); }
    for (const adj of [forward, backward]) for (const [id, list] of adj) adj.set(id, [...new Set(list)].sort(compare));
    const baseLimitations = [STATIC_LIMITATION];
    if (snapshot.state !== 'validated-map') baseLimitations.push('Grouping is a proposal, not a reviewed architecture.');
    for (const l of snapshot.limitations || []) if (typeof l === 'string' && l && baseLimitations.length < 100) baseLimitations.push(l.slice(0, 2048));

    // Shortest predecessor tree from seed. reverse=false follows consumer->dependency.
    function tree(seed, reverse) {
      const adj = reverse ? backward : forward;
      const prev = new Map([[seed, null]]), order = [];
      const queue = [seed];
      for (let i = 0; i < queue.length; i++) for (const next of adj.get(queue[i])) {
        if (!prev.has(next)) { prev.set(next, queue[i]); order.push(next); queue.push(next); }
      }
      return {prev, order};
    }
    function chainTo(prev, id) {
      const chain = [];
      for (let cursor = id; cursor !== null; cursor = prev.get(cursor)) chain.push(cursor);
      return chain.reverse(); // seed ... id
    }
    function witnessFromChain(chain) {
      const links = [];
      for (let i = 0; i + 1 < chain.length; i++) links.push(hop(chain[i], chain[i + 1]));
      return {nodeIds: chain, edges: links};
    }
    function sourceRef(id) {
      const n = nodes.get(id);
      if (!n || n.kind !== 'file') return null;
      const f = inventory.get(n.path);
      if (!f) return null;
      return {path: n.path, sha256: f.sha256, snapshotId: snapshot.snapshotId,
        evidenceKind: 'observed-source', start: null, end: null};
    }

    function base(request) {
      return {schema: PACKET_SCHEMA, requestId: request.requestId, projectId: snapshot.projectId,
        snapshotId: snapshot.snapshotId, mapSha256: snapshot.mapSha256, scorerSha256: snapshot.scorerSha256,
        manifestSha256: snapshot.source.manifestSha256, operation: 'NOT_SURE', status: 'no-match',
        highlightState: 'relevant', query: request.query, selectedNodeIds: [], selectedEdges: [],
        witnesses: [], alternatives: [], sourceRefs: [], limitations: baseLimitations.slice(),
        truncated: false, continuation: null, reason: ''};
    }
    function alternativesFrom(result) {
      const seen = new Set(), out = [];
      for (const h of Object.values(result.targets)) for (const s of h.suggestions || []) {
        if (seen.has(s.id) || out.length >= LIMITS.alternatives) continue;
        seen.add(s.id);
        out.push({nodeId: s.id, path: s.path || null, reason: s.reason});
      }
      return out;
    }
    function finishSelection(packet, selected, selEdges, witnesses) {
      packet.selectedNodeIds = selected;
      const set = new Set(selected);
      packet.selectedEdges = selEdges.filter(e => set.has(e.from) && set.has(e.to)).slice(0, LIMITS.selectedEdges);
      if (packet.selectedEdges.length < selEdges.filter(e => set.has(e.from) && set.has(e.to)).length)
        packet.limitations.push('Selected edges capped at ' + LIMITS.selectedEdges + '; witnesses remain complete for shown nodes.');
      packet.witnesses = witnesses;
      packet.sourceRefs = selected.map(sourceRef).filter(Boolean).slice(0, LIMITS.sourceRefs);
      return packet;
    }

    // UPSTREAM: seed -> deps (witness seed..dep). DOWNSTREAM: consumers -> seed (witness consumer..seed).
    // Pages grow whole chains: every selected non-seed node carries its own witness.
    function reach(packet, op, seed, offset) {
      const downstream = op === 'DOWNSTREAM';
      const {prev, order} = tree(seed, downstream);
      if (offset > order.length) throw new Error('Continuation is past the end of the result');
      const selected = [seed], set = new Set(selected), witnesses = [];
      let next = offset;
      for (; next < order.length; next++) {
        const chain = chainTo(prev, order[next]);
        const missing = chain.filter(id => !set.has(id));
        if (selected.length + missing.length > LIMITS.selectedNodes) break;
        for (const id of missing) {
          set.add(id); selected.push(id);
          const own = chainTo(prev, id);
          witnesses.push(witnessFromChain(downstream ? own.reverse() : own));
        }
      }
      const selEdges = [], seenEdge = new Set();
      for (const w of witnesses) for (const e of w.edges) {
        const k = edgeKey(e);
        if (!seenEdge.has(k)) { seenEdge.add(k); selEdges.push(e); }
      }
      packet.operation = op;
      packet.status = 'matched';
      packet.seedNodeId = seed;
      packet.highlightState = downstream && witnesses.length ? 'potential-impact' : 'relevant';
      packet.reason = (downstream ? 'Dependents' : 'Dependencies') + ' of ' + seed + ': ' + order.length +
        (offset > 0 || next < order.length ? ' (showing results ' + (offset + 1) + '–' + next + ')' : '') + '.';
      if (downstream) packet.limitations.push('Dependents are potentially affected via static imports, not guaranteed to break.');
      if (next < order.length) { packet.truncated = true; packet.continuation = 'offset:' + next; }
      return finishSelection(packet, selected, selEdges, witnesses);
    }

    function query(request) {
      if (!request || typeof request.requestId !== 'string' || !request.requestId || request.requestId.length > 512)
        throw new Error('requestId is required');
      if (typeof request.query !== 'string' || request.query.length > LIMITS.queryChars)
        throw new Error('query must be a bounded string');
      const packet = base(request);
      if (request.snapshotId !== undefined && request.snapshotId !== snapshot.snapshotId) {
        packet.status = 'stale';
        packet.reason = 'Request was made against a different snapshot; rerun it against the current revision.';
        return packet;
      }
      const offset = parseContinuation(request.continuation);
      // Explicit human choice from a previous needs-choice packet: only known IDs, never fuzzy.
      if (request.chosenNodeId !== undefined) {
        if (!nodes.has(request.chosenNodeId)) throw new Error('Unknown chosen node ID');
        packet.operation = 'LOCATE'; packet.status = 'matched';
        packet.reason = 'Explicitly chosen by the user.';
        return finishSelection(packet, [request.chosenNodeId], [], []);
      }
      const result = scorer.score(request.query); // score() validates its own result contract
      const requested = result.requestedOperation;
      if (!result.yes) {
        packet.alternatives = alternativesFrom(result);
        packet.status = packet.alternatives.length ? 'needs-choice' : 'no-match';
        packet.reason = result.reason;
        return packet;
      }
      if (requested === 'PATH') {
        const from = result.targets.from_target.choice, to = result.targets.to_target.choice;
        packet.operation = 'PATH';
        if (nodes.get(from).kind !== nodes.get(to).kind) {
          packet.status = 'unsupported';
          packet.limitations.push('Paths between a group and a file are not converted; choose two files or two groups.');
          packet.reason = 'Mixed group/file endpoints.';
          return packet;
        }
        const path = router.shortestPath(from, to);
        if (!path) {
          packet.status = 'no-path';
          packet.reason = 'No directed static route from ' + from + ' to ' + to + '.';
          return finishSelection(packet, [...new Set([from, to])], [], []);
        }
        packet.status = 'matched';
        packet.reason = 'Shortest directed static route (' + (path.length - 1) + ' hops).';
        const w = witnessFromChain(path);
        return finishSelection(packet, path, w.edges, path.length > 1 ? [w] : []);
      }
      const seed = result.targets.locate_target.choice;
      if (requested === 'LOCATE') {
        packet.operation = 'LOCATE'; packet.status = 'matched';
        packet.reason = result.targets.locate_target.reason;
        return finishSelection(packet, [seed], [], []);
      }
      return reach(packet, requested, seed, offset);
    }
    return {query, limits: LIMITS};
  }

  function querySnapshot(snapshot, request, options) {
    return createQueryService(snapshot, options).query(request);
  }
  return {createQueryService, querySnapshot, PACKET_SCHEMA, LIMITS};
});
