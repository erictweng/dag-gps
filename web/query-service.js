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
    alternatives: 20, sourceRefs: 200, queryChars: 2048, packetBytes: 1024 * 1024});
  const STATIC_LIMITATION = 'Static extracted relationships only; dynamic imports, runtime calls and unsupported files may be missing.';
  const compare = (a, b) => (a < b ? -1 : a > b ? 1 : 0);
  const edgeKey = e => JSON.stringify([e.from, e.to, e.type]);

  // Python's contract serializes UTF-8 JSON with a space after each structural
  // comma/colon. Count those outside strings, not punctuation in source evidence.
  function packetBytes(packet) {
    const text = JSON.stringify(packet);
    let spaces = 0, quoted = false, escaped = false;
    for (const c of text) {
      if (escaped) { escaped = false; continue; }
      if (quoted && c === '\\') { escaped = true; continue; }
      if (c === '"') quoted = !quoted;
      else if (!quoted && (c === ',' || c === ':')) spaces++;
    }
    return new TextEncoder().encode(text).length + spaces;
  }

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
    const symbols = map.symbol_graph || null;
    const symbolNodes = new Map((symbols ? symbols.nodes : []).map(n => [n.id, n]));
    const symbolNames = new Map();
    for (const n of symbolNodes.values()) for (const name of new Set([n.id, n.name, n.qualname, n.path + ':' + n.qualname])) {
      if (!symbolNames.has(name)) symbolNames.set(name, []);
      symbolNames.get(name).push(n.id);
    }
    for (const ids of symbolNames.values()) ids.sort(compare);
    const callForward = new Map([...symbolNodes.keys()].map(id => [id, []]));
    const callBackward = new Map([...symbolNodes.keys()].map(id => [id, []]));
    for (const e of symbols ? symbols.edges : []) {
      callForward.get(e.from).push(e); callBackward.get(e.to).push(e);
    }
    for (const adj of [callForward, callBackward]) for (const list of adj.values()) list.sort((a, b) => compare(edgeKey(a), edgeKey(b)));
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

    function symbolRequest(text) {
      const q = text.trim().replace(/[?]+$/, '').replace(/`/g, '');
      let m;
      if ((m = /^where is (.+?) defined$/i.exec(q))) return {op: 'LOCATE', names: [m[1]]};
      if ((m = /^(?:locate|find) (?:function|class|method|symbol) (.+)$/i.exec(q))) return {op: 'LOCATE', names: [m[1]]};
      if ((m = /^(?:what calls|callers of) (.+)$/i.exec(q))) return {op: 'CALLERS', names: [m[1]]};
      if ((m = /^what does (.+) call$/i.exec(q))) return {op: 'CALLEES', names: [m[1]]};
      if ((m = /^callees of (.+)$/i.exec(q))) return {op: 'CALLEES', names: [m[1]]};
      if ((m = /^how does (.+?) reach (.+)$/i.exec(q))) return {op: 'FLOW', names: [m[1], m[2]]};
      if ((m = /^trace from (.+)$/i.exec(q))) return {op: 'TRACE', names: [m[1]]};
      if (symbolNames.has(q) && !nodes.has(q)) return {op: 'LOCATE', names: [q]};
      return null;
    }

    function symbolQuery(packet, request, parsed, offset) {
      packet.operation = parsed.op;
      packet.limitations = ['Python lexical calls only, not runtime execution. Decorators, DI, dynamic dispatch, inherited methods and external calls are unresolved.'];
      if (!symbols) {
        packet.status = 'unsupported'; packet.reason = 'This snapshot has no Python symbol extension.';
        return packet;
      }
      const candidates = parsed.names.map(name => symbolNames.get(name) || []);
      if (request.chosenNodeId !== undefined) {
        const index = candidates.findIndex(ids => ids.includes(request.chosenNodeId));
        if (index < 0) throw new Error('Chosen symbol is not an alternative for this question');
        candidates[index] = [request.chosenNodeId];
      }
      if (candidates.some(ids => !ids.length)) {
        packet.reason = 'No exact symbol matches ' + parsed.names.filter((_, i) => !candidates[i].length).join(', ') + '.';
        return packet;
      }
      if (candidates.some(ids => ids.length > 1)) {
        const ambiguous = candidates.findIndex(ids => ids.length > 1), ids = candidates[ambiguous];
        if (offset >= ids.length) throw new Error('Continuation is past the alternatives');
        packet.status = 'needs-choice'; packet.reason = 'Multiple definitions; choose a qualified symbol.';
        packet.alternatives = ids.slice(offset, offset + LIMITS.alternatives).map(id => {
          const names = candidates.map((values, i) => i === ambiguous ? id : values.length === 1 ? values[0] : parsed.names[i]);
          const query = parsed.op === 'FLOW' ? 'how does ' + names[0] + ' reach ' + names[1] :
            ({LOCATE: 'locate symbol ', CALLERS: 'callers of ', CALLEES: 'callees of ', TRACE: 'trace from '})[parsed.op] + names[0];
          return {nodeId: id, path: id, query, reason: symbolNodes.get(id).path + ':' + symbolNodes.get(id).start};
        });
        if (offset + LIMITS.alternatives < ids.length) {
          packet.truncated = true; packet.continuation = 'offset:' + (offset + LIMITS.alternatives);
        }
        return packet;
      }
      const seed = candidates[0][0], end = candidates[1] && candidates[1][0];
      packet.seedNodeId = seed;
      const reverse = parsed.op === 'CALLERS', adj = reverse ? callBackward : callForward;
      const prev = new Map([[seed, null]]), via = new Map(), order = [], queue = [seed];
      if (parsed.op !== 'LOCATE') for (let i = 0; i < queue.length; i++) {
        for (const edge of adj.get(queue[i])) {
          const next = reverse ? edge.from : edge.to;
          if (!prev.has(next)) { prev.set(next, queue[i]); via.set(next, edge); order.push(next); queue.push(next); }
        }
        if (parsed.op === 'CALLERS' || parsed.op === 'CALLEES') break;
      }
      function witness(id) {
        const chain = [], links = [];
        for (let n = id; n !== null; n = prev.get(n)) { chain.push(n); if (via.has(n)) links.push(via.get(n)); }
        return {nodeIds: reverse ? chain : chain.reverse(), edges: reverse ? links : links.reverse()};
      }
      const selected = new Set([seed]), selectedEdges = new Map(), witnesses = [];
      if (['CALLERS', 'CALLEES', 'TRACE'].includes(parsed.op)) for (const e of adj.get(seed)) if (e.from === e.to) {
        selectedEdges.set(edgeKey(e), e);
        packet.limitations.push('A recursive self-call is retained as an edge, not an invented acyclic witness chain.');
      }
      packet.status = 'matched';
      if (parsed.op === 'FLOW' && !prev.has(end)) {
        selected.add(end); packet.status = 'no-path';
        packet.reason = 'No resolved static call path. Missing runtime links are unknown, not proof of no flow.';
      } else {
        const targets = parsed.op === 'FLOW' ? [end] : order;
        if (offset > targets.length) throw new Error('Continuation is past the result');
        let next = offset;
        for (; next < targets.length; next++) {
          const w = witness(targets[next]);
          const added = w.nodeIds.filter(id => !selected.has(id));
          if (selected.size + added.length > LIMITS.selectedNodes || witnesses.length >= LIMITS.witnesses) break;
          for (const id of added) selected.add(id);
          for (const e of w.edges) selectedEdges.set(edgeKey(e), e);
          if (w.edges.length) witnesses.push(w);
        }
        if (next < targets.length) {
          if (next === offset) { packet.status = 'unsupported'; packet.reason = 'A complete call chain exceeds the 200-node packet bound.'; return packet; }
          packet.truncated = true; packet.continuation = 'offset:' + next;
        }
        packet.reason = parsed.op + ': ' + selected.size + ' symbol(s), ' + selectedEdges.size + ' resolved call edge(s).';
      }
      packet.selectedNodeIds = [...selected]; packet.selectedEdges = [...selectedEdges.values()]; packet.witnesses = witnesses;
      packet.sourceRefs = [...selected].map(id => {
        const n = symbolNodes.get(id), f = inventory.get(n.path);
        return {path: n.path, start: n.start, end: n.end, sha256: f.sha256,
          snapshotId: snapshot.snapshotId, evidenceKind: 'observed-source'};
      });
      const unknown = symbols.unresolved.filter(c => selected.has(c.from));
      packet.unresolvedCalls = unknown.slice(0, 100);
      packet.unresolvedCallCount = unknown.length;
      packet.reason += ' ' + unknown.length + ' unresolved call site(s) in selected symbols (not edges).';
      if (parsed.op === 'CALLERS' && !packet.selectedEdges.length)
        packet.reason += ' No resolved callers observed; this does not mean no callers exist.';
      packet.limitations.push(unknown.length + ' unresolved call site(s) in selected symbols; ' + packet.unresolvedCalls.length + ' listed. They are not edges.');
      return packet;
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
      const symbolOp = symbolRequest(request.query);
      // Existing file/group questions keep the unchanged scorer/router path.
      const legacyTarget = symbolOp && symbolOp.names.some(name => nodes.has(name) ||
        [...nodes.values()].some(n => n.path === name || n.label === name));
      if (symbolOp && symbols && !legacyTarget) {
        const result = symbolQuery(packet, request, symbolOp, offset);
        if (packetBytes(result) <= LIMITS.packetBytes) return result;
        // Never cut call sites or whole-chain witnesses into misleading evidence.
        // Oversized results explicitly abstain, with no selections to highlight.
        const bounded = base(request);
        bounded.operation = symbolOp.op; bounded.status = 'unsupported';
        bounded.reason = 'Complete call evidence exceeds the 1 MiB packet budget; use a narrower symbol question.';
        return bounded;
      }
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
