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
  const TIERS = ['resolved', 'instance-local', 'typed', 'through-decorator'];
  const weakest = edges => TIERS[Math.max(0, ...edges.map(e => TIERS.indexOf(e.confidence)))];
  function certainEdge(e) {
    const sites = e.sites.filter(s => !s.confidence || s.confidence === 'resolved');
    return sites.length ? {from: e.from, to: e.to, type: 'call', confidence: 'resolved', sites} : null;
  }

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

  function createConceptIndex(map) {
    const started = performance.now();
    const text = map.search_text;
    const available = text?.schema === 'dag-gps-search-text/v1';
    const postings = new Map(), docs = [];
    const extraStop = new Set(['we', 'our', 'i', 'my', 'please']);
    const stem = t => t.length > 4 && t.endsWith('s') && !t.endsWith('ss') ? t.slice(0, -1) : t;
    const terms = value => Scorer.terms(value).filter(t => !extraStop.has(t)).map(stem);
    if (available) for (const node of [...map.nodes, ...(map.symbol_graph?.nodes || [])]) {
      const stored = text.nodes[node.id];
      const fields = stored || {name: (node.name || node.label || '').slice(0, 80),
        path: (node.path || node.label || '').slice(0, 120), docstring: ''};
      const counts = new Map();
      for (const [field, weight] of [['name', 2], ['path', 0.5], ['docstring', 1.5]]) {
        for (const term of terms(fields[field])) {
          if (!counts.has(term)) counts.set(term, {tf: 0, fields: new Set()});
          counts.get(term).tf += weight; counts.get(term).fields.add(field);
        }
      }
      const index = docs.length, length = [...counts.values()].reduce((n, c) => n + c.tf, 0);
      docs.push({node, length});
      for (const [term, c] of counts) {
        if (!postings.has(term)) postings.set(term, []);
        postings.get(term).push({index, tf: c.tf, fields: [...c.fields]});
      }
    }
    const average = docs.reduce((n, d) => n + d.length, 0) / (docs.length || 1) || 1;
    function search(query) {
      const q = [...new Set(terms(Scorer.normalizeQuestion(query)))];
      if (!available || !q.length || q.some(term => !postings.has(term))) return [];
      const scores = new Map();
      for (const term of q) {
        const hits = postings.get(term) || [];
        const idf = Math.log(1 + (docs.length - hits.length + 0.5) / (hits.length + 0.5));
        for (const hit of hits) {
          if (!scores.has(hit.index)) scores.set(hit.index, {score: 0, evidence: []});
          const result = scores.get(hit.index);
          result.score += idf * hit.tf * 2.2 / (hit.tf + 1.2 * (0.25 + 0.75 * docs[hit.index].length / average));
          result.evidence.push(term + ' [' + hit.fields.join(', ') + ']');
        }
      }
      const hint = Scorer.kindHint(query);
      return [...scores].filter(([, r]) => r.score >= 4 && r.evidence.length / q.length >= 0.5)
        .sort(([a, x], [b, y]) => y.score - x.score ||
          Number(docs[b].node.kind === hint) - Number(docs[a].node.kind === hint) || compare(docs[a].node.id, docs[b].node.id))
        .slice(0, 8).map(([i, r]) => ({nodeId: docs[i].node.id,
          path: docs[i].node.kind === 'symbol' ? docs[i].node.id : docs[i].node.path || null,
          query: docs[i].node.kind === 'symbol' ? 'locate symbol ' + docs[i].node.id : undefined,
          reason: 'BM25 candidate only: ' + r.evidence.join('; ') + '; score ' + r.score.toFixed(3)}));
    }
    return {search, stats: {available, documents: docs.length, buildMs: performance.now() - started,
      omittedDocstrings: text?.omitted || 0, scoreFloor: 4}};
  }

  function createQueryService(snapshot, options = {}) {
    requireSnapshot(snapshot);
    const map = snapshot.map;
    const concepts = createConceptIndex(map);
    const scorer = Scorer.createScorer(map, options.learnedAliases || []);
    const router = Router.createRouter(map);
    const nodes = new Map(map.nodes.map(n => [n.id, n]));
    const inventory = new Map((snapshot.inventory || []).map(f => [f.path, f]));
    const symbols = map.symbol_graph || null;
    const symbolNodes = new Map((symbols ? symbols.nodes : []).map(n => [n.id, n]));
    const symbolNames = new Map();
    for (const n of symbolNodes.values()) for (const name of new Set([n.id, n.name, n.qualname, n.path + ':' + n.qualname])) {
      const key = Scorer.normalizeQuestion(name);
      if (!symbolNames.has(key)) symbolNames.set(key, []);
      if (!symbolNames.get(key).includes(n.id)) symbolNames.get(key).push(n.id);
    }
    for (const ids of symbolNames.values()) ids.sort(compare);
    const literalNames = new Map();
    const exactNames = new Map();
    for (const n of nodes.values()) for (const value of new Set([n.id, n.path, n.kind === 'layer' ? n.label : null].filter(Boolean))) {
      const key = value.toLowerCase();
      if (!exactNames.has(key)) exactNames.set(key, []);
      exactNames.get(key).push(n.id);
    }
    for (const n of [...nodes.values(), ...symbolNodes.values()]) {
      const name = n.kind === 'symbol' ? n.name : n.kind === 'file' ?
        n.path.split('/').at(-1).replace(/\.[^.]+$/, '') : n.label?.split('/').at(-1);
      if (!name) continue;
      const key = name.toLowerCase();
      if (!literalNames.has(key)) literalNames.set(key, []);
      literalNames.get(key).push(n);
    }
    function lookupSymbol(name) {
      if (symbolNames.has(name)) return symbolNames.get(name);
      return [...new Set(Scorer.synonymQueries(name).flatMap(v => symbolNames.get(v.query) || []))].sort(compare);
    }
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
    if (concepts.stats.omittedDocstrings) baseLimitations.push('Search-text budget omitted ' + concepts.stats.omittedDocstrings + ' node records; those nodes use bounded names/paths only.');
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
      if (router.isFolder(seed)) return folderReach(packet, op, seed, offset);
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
      const q = Scorer.normalizeQuestion(text);
      let m;
      if ((m = /^where is (.+?) defined$/i.exec(q))) return {op: 'LOCATE', names: [m[1]]};
      if ((m = /^(?:locate|find) (?:function|class|method|symbol) (.+)$/i.exec(q))) return {op: 'LOCATE', names: [m[1]]};
      if ((m = /^(?:what calls|who invokes|who calls|callers of) (.+)$/i.exec(q)) ||
          (m = /^where is (.+?) called from$/i.exec(q))) return {op: 'CALLERS', names: [m[1]]};
      if ((m = /^what does (.+) call$/i.exec(q))) return {op: 'CALLEES', names: [m[1]]};
      if ((m = /^callees of (.+)$/i.exec(q))) return {op: 'CALLEES', names: [m[1]]};
      if ((m = /^how does (.+?) reach (.+)$/i.exec(q))) return {op: 'FLOW', names: [m[1], m[2]]};
      if ((m = /^trace from (.+)$/i.exec(q))) return {op: 'TRACE', names: [m[1]]};
      if (symbolNames.has(q) && !nodes.has(q)) return {op: 'LOCATE', names: [q]};
      const name = Scorer.filenameText(q);
      if (lookupSymbol(name).length && (Scorer.kindHint(q) === 'symbol' ||
          Object.values(scorer.score(q).targets).every(h => h.match.label === 'No match' || h.match.tier === 'fuzzy')))
        return {op: 'LOCATE', names: [name]};
      return null;
    }

    function symbolQuery(packet, request, parsed, offset) {
      packet.operation = parsed.op;
      packet.limitations = ['Python lexical calls only, not runtime execution. Decorators, DI, dynamic dispatch, inherited methods and external calls are unresolved.'];
      const certain = request.certainOnly === true;
      if (certain) packet.certainOnly = true;
      else packet.limitations = ['Static evidence, not runtime execution. Confidence tiers: resolved → instance-local → typed → through-decorator (weakest). Decorator links identify the underlying definition, not wrapper behavior. External/dynamic calls remain unknown.'];
      if (!symbols) {
        packet.status = 'unsupported'; packet.reason = 'This snapshot has no Python symbol extension.';
        return packet;
      }
      const candidates = parsed.names.map(lookupSymbol);
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
      const reverse = ['CALLERS', 'DOWNSTREAM'].includes(parsed.op), adj = reverse ? callBackward : callForward;
      const linksFrom = id => certain ? adj.get(id).map(certainEdge).filter(Boolean) : adj.get(id);
      const prev = new Map([[seed, null]]), via = new Map(), order = [], queue = [seed];
      if (parsed.op !== 'LOCATE') for (let i = 0; i < queue.length; i++) {
        for (const edge of linksFrom(queue[i])) {
          const next = reverse ? edge.from : edge.to;
          if (!prev.has(next)) { prev.set(next, queue[i]); via.set(next, edge); order.push(next); queue.push(next); }
        }
        if (parsed.op === 'CALLERS' || parsed.op === 'CALLEES') break;
      }
      function witness(id) {
        const chain = [], links = [];
        for (let n = id; n !== null; n = prev.get(n)) { chain.push(n); if (via.has(n)) links.push(via.get(n)); }
        const result = {nodeIds: reverse ? chain : chain.reverse(), edges: reverse ? links : links.reverse()};
        if (!certain) result.confidence = weakest(links);
        return result;
      }
      const selected = new Set([seed]), selectedEdges = new Map(), witnesses = [];
      if (['CALLERS', 'CALLEES', 'TRACE', 'UPSTREAM', 'DOWNSTREAM'].includes(parsed.op)) for (const e of linksFrom(seed)) if (e.from === e.to) {
        selectedEdges.set(edgeKey(e), e);
        packet.limitations.push('A recursive self-call is retained as an edge, not an invented acyclic witness chain.');
      }
      packet.status = 'matched';
      if (['FLOW', 'PATH'].includes(parsed.op) && !prev.has(end)) {
        selected.add(end); packet.status = 'no-path';
        packet.reason = 'No ' + (certain ? 'resolved ' : '') + 'static call path. Missing runtime links are unknown, not proof of no flow.';
      } else {
        const targets = ['FLOW', 'PATH'].includes(parsed.op) ? [end] : order;
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
        packet.reason = parsed.op + ': ' + selected.size + ' symbol(s), ' + selectedEdges.size + (certain ? ' resolved' : ' static') + ' call edge(s).';
      }
      packet.selectedNodeIds = [...selected]; packet.selectedEdges = [...selectedEdges.values()]; packet.witnesses = witnesses;
      packet.sourceRefs = [...selected].map(id => {
        const n = symbolNodes.get(id), f = inventory.get(n.path);
        return {path: n.path, start: n.start, end: n.end, sha256: f.sha256,
          snapshotId: snapshot.snapshotId, evidenceKind: 'observed-source'};
      });
      let allUnknown = symbols.unresolved;
      if (certain) {
        allUnknown = []; let j = 0;
        const additions = symbols.certainAdditions || [];
        for (let i = 0; i <= symbols.unresolved.length; i++) {
          while (j < additions.length && additions[j][0] === i) {
            const [, ei, si] = additions[j++], edge = symbols.edges[ei], site = edge.sites[si];
            allUnknown.push({from: edge.from, to: null, confidence: 'unresolved', path: site.path,
              start: site.start, end: site.end, expression: site.expression,
              reason: 'No unique supported lexical target; runtime dispatch not inferred'});
          }
          if (i < symbols.unresolved.length) allUnknown.push(symbols.unresolved[i]);
        }
      }
      const unknown = allUnknown.filter(c => selected.has(c.from));
      if (!certain) packet.entryPoints = [...selected].filter(id => symbolNodes.get(id).entryPoint)
        .map(id => ({nodeId: id, decorators: symbolNodes.get(id).entryPoint}));
      packet.unresolvedCalls = unknown.slice(0, 100);
      packet.unresolvedCallCount = unknown.length;
      packet.reason += ' ' + unknown.length + ' unresolved call site(s) in selected symbols (not edges).';
      for (const name of parsed.names) if (!symbolNames.has(name)) {
        const matches = Scorer.synonymQueries(name).filter(v => symbolNames.has(v.query));
        packet.reason += ' ' + matches.map(v => v.reason).join('; ') + '.';
      }
      if (parsed.op === 'CALLERS' && !packet.selectedEdges.length)
        packet.reason += ' No resolved callers observed; this does not mean no callers exist.';
      packet.limitations.push(unknown.length + ' unresolved call site(s) in selected symbols; ' + packet.unresolvedCalls.length + ' listed. They are not edges.');
      return packet;
    }

    function operationQuery(op, names) {
      if (op === 'PATH') return 'path from ' + names[0] + ' to ' + names[1];
      if (op === 'FLOW') return 'how does ' + names[0] + ' reach ' + names[1];
      return ({LOCATE: 'where is ', UPSTREAM: 'upstream of ', DOWNSTREAM: 'downstream of ',
        CALLERS: 'callers of ', CALLEES: 'callees of ', TRACE: 'trace from '})[op] + names[0];
    }

    function boundedSymbolQuery(packet, request, parsed, offset) {
      const result = symbolQuery(packet, request, parsed, offset);
      if (packetBytes(result) <= LIMITS.packetBytes) return result;
      const bounded = base(request);
      bounded.operation = parsed.op; bounded.status = 'unsupported';
      bounded.reason = 'Complete call evidence exceeds the 1 MiB packet budget; use a narrower symbol question.';
      return bounded;
    }

    // Resolve endpoints independently, before choosing the import or call graph.
    // Only literal cross-kind names enter this guard; aliases and fuzzy/concept
    // suggestions keep their existing evidence policy.
    function resolveOperation(packet, request, intent, symbolOp, offset) {
      if (intent.malformed) return null;
      const op = symbolOp?.op || intent.op;
      const names = symbolOp?.names || (intent.op === 'PATH' ? [intent.from, intent.to] : [intent.target]);
      const targets = names.map(text => {
        if (map.meta?.folderTree === 1) text = text.replace(/^the\s+/i, '');
        const name = Scorer.filenameText(text), hint = Scorer.kindHint(text) ||
          (op === 'LOCATE' ? Scorer.kindHint(request.query) : null);
        const alias = (options.learnedAliases || []).some(a => Scorer.normalizeQuestion(a.alias) === name);
        const literal = !alias && /^[\w-]+$/.test(name) ? literalNames.get(name) || [] : [];
        const collision = new Set(literal.map(n => n.kind)).size > 1 ||
          (map.meta?.folderTree === 1 && literal.filter(n => n.kind === 'layer').length > 1);
        if (collision) {
          const preferred = hint ? literal.filter(n => n.kind === hint) : [];
          return {collision, ids: (preferred.length ? preferred : literal).map(n => n.id)};
        }
        const exactSymbol = symbolNames.get(Scorer.normalizeQuestion(text)) ||
          (hint === 'symbol' ? lookupSymbol(name) : []);
        if (exactSymbol.length) return {collision, ids: exactSymbol};
        return {collision, ids: exactNames.get(name) || []};
      });
      const collision = targets.some(t => t.collision);
      const fileOp = {CALLERS: 'DOWNSTREAM', CALLEES: 'UPSTREAM', TRACE: 'UPSTREAM', FLOW: 'PATH'}[op] || op;
      const canonicalFolder = names.some(text => Scorer.kindHint(text) === 'layer' && nodes.has(Scorer.filenameText(text)));
      // Explicit graph-qualified syntax also needs graph-appropriate dispatch:
      // callers of a file means static import dependents, never LOCATE.
      const explicit = targets.every(t => t.ids.length === 1) &&
        (canonicalFolder || symbolOp && symbolOp.op !== 'LOCATE' && intent.op !== fileOp || intent.op !== 'LOCATE' &&
          targets.some(t => symbolNodes.has(t.ids[0])));
      if (!collision && !explicit && !(request.chosenNodeId !== undefined && op !== 'LOCATE')) return null;
      for (let i = 0; i < targets.length; i++) if (!targets[i].ids.length) {
        const h = scorer.score('where is ' + names[i]).targets.locate_target;
        targets[i].ids = h.yes ? [h.choice] : (h.suggestions || []).filter(s => s.score > 0).map(s => s.id);
        targets[i].needsChoice = !h.yes && targets[i].ids.length > 0;
        targets[i].reason = h.reason;
      }
      if (request.chosenNodeId !== undefined) {
        const first = targets.findIndex(t => t.ids.length > 1 || t.needsChoice);
        // The UI sends both alternative.query and its ID. A kind-qualified
        // endpoint in that query already records the choice; do not apply the
        // same ID again to a second endpoint with the same ambiguous name.
        const confirmed = targets.findIndex((t, i) => t.ids.length === 1 && !t.needsChoice &&
          t.ids[0] === request.chosenNodeId && Scorer.kindHint(names[i]));
        const i = confirmed >= 0 ? confirmed : first >= 0 && targets[first].ids.includes(request.chosenNodeId) ? first :
          targets.findIndex(t => t.ids.length === 1 && t.ids.includes(request.chosenNodeId));
        if (i < 0 || !targets[i].ids.includes(request.chosenNodeId)) throw new Error('Chosen node is not an alternative for this question');
        targets[i].ids = [request.chosenNodeId];
        targets[i].needsChoice = false;
      }
      packet.operation = op;
      const ambiguous = targets.findIndex(t => t.ids.length > 1 || t.needsChoice);
      const canonical = id => {
        const n = nodes.get(id);
        return n ? (n.kind === 'layer' ? 'folder ' : 'file ') + (n.path || n.id) : 'function ' + id;
      };
      if (ambiguous >= 0) {
        const ordered = targets[ambiguous].ids.slice().sort((a, b) => {
          const x = nodes.get(a) || symbolNodes.get(a), y = nodes.get(b) || symbolNodes.get(b);
          return compare(x.kind, y.kind) || compare(a, b);
        });
        if (offset >= ordered.length) throw new Error('Continuation is past the alternatives');
        packet.status = 'needs-choice';
        packet.reason = map.meta?.folderTree === 1 ?
          'Literal name matches multiple targets; choose a file, folder or symbol explicitly.' :
          'Literal name matches different kinds; choose a file, folder or symbol explicitly.';
        packet.alternatives = ordered.slice(offset, offset + LIMITS.alternatives).map(id => {
          const n = nodes.get(id) || symbolNodes.get(id);
          const selected = names.map((text, i) => i === ambiguous ? canonical(id) :
            targets[i].ids.length === 1 && !targets[i].needsChoice ? canonical(targets[i].ids[0]) : text);
          return {nodeId: id, path: n.kind === 'symbol' ? id : n.path || null,
            query: operationQuery(op, selected), reason: (n.symbolKind || n.kind) + ': ' + (n.path || n.label)};
        });
        if (offset + LIMITS.alternatives < ordered.length) {
          packet.truncated = true; packet.continuation = 'offset:' + (offset + LIMITS.alternatives);
        }
        return packet;
      }
      if (targets.some(t => !t.ids.length)) { packet.reason = 'No exact endpoint matches this operation.'; return packet; }
      const ids = targets.map(t => t.ids[0]);
      if (ids.some(id => symbolNodes.has(id))) {
        if (!ids.every(id => symbolNodes.has(id))) {
          packet.status = 'unsupported'; packet.reason = 'Mixed symbol and file/folder endpoints are not converted.';
          return packet;
        }
        return boundedSymbolQuery(packet, {...request, chosenNodeId: undefined},
          {op, names: ids.map(Scorer.normalizeQuestion)}, offset);
      }
      // After an explicit choice, a continuation pages the chosen traversal itself.
      return fileOperation(packet, fileOp, ids, offset,
        'Explicit literal target. ' + targets.map(t => t.reason || '').filter(Boolean).join(' '));
    }

    function folderReach(packet, op, seed, offset) {
      const downstream = op === 'DOWNSTREAM';
      const {prev, order} = router.traversal(seed, downstream);
      if (offset > order.length) throw new Error('Continuation is past the end of the result');
      const selected = [seed], witnesses = [];
      let bytes = packetBytes(packet);
      let next = offset;
      for (; next < order.length && selected.length < LIMITS.selectedNodes; next++) {
        const chain = chainTo(prev, order[next]);
        if (chain.length > LIMITS.selectedNodes) {
          if (next > offset) break;
          packet.status = 'unsupported';
          packet.reason = 'Complete folder witness exceeds the 200-node budget; choose a narrower file question.';
          return packet;
        }
        const witness = witnessFromChain(downstream ? chain.reverse() : chain);
        selected.push(order[next]); witnesses.push(witness);
        // Byte-bounded pages retain complete evidence, never silently cut a chain.
        bytes += packetBytes(witness) + packetBytes(order[next]);
        if (bytes > LIMITS.packetBytes / 2) {
          selected.pop(); witnesses.pop();
          if (next === offset) {
            packet.status = 'unsupported'; packet.reason = 'Complete folder witness exceeds the packet byte budget.';
            return packet;
          }
          break;
        }
      }
      packet.operation = op; packet.status = 'matched'; packet.seedNodeId = seed;
      packet.highlightState = downstream && witnesses.length ? 'potential-impact' : 'relevant';
      packet.reason = (downstream ? 'Dependents' : 'Dependencies') + ' outside ' + seed + ': ' + order.length + '.';
      packet.limitations.push('Folder results exclude internal files; witnesses start/end at real descendant files, not synthetic folder edges.');
      if (downstream) packet.limitations.push('Dependents are potentially affected via static imports, not guaranteed to break.');
      if (next < order.length) { packet.truncated = true; packet.continuation = 'offset:' + next; }
      const links = new Map(witnesses.flatMap(w => w.edges).map(e => [edgeKey(e), e]));
      return finishSelection(packet, selected, [...links.values()], witnesses);
    }

    function fileOperation(packet, requested, ids, offset, evidence) {
      packet.operation = requested;
      if (requested === 'PATH') {
        const [from, to] = ids;
        if (nodes.get(from).kind !== nodes.get(to).kind) {
          packet.status = 'unsupported';
          packet.limitations.push('Paths between a group and a file are not converted; choose two files or two groups.');
          packet.reason = 'Mixed group/file endpoints.';
          return packet;
        }
        const path = router.shortestPath(from, to);
        if (!path) {
          packet.status = 'no-path';
          packet.reason = 'No directed static route from ' + from + ' to ' + to + '.' + evidence;
          return finishSelection(packet, [...new Set([from, to])], [], []);
        }
        packet.status = 'matched';
        packet.reason = 'Shortest directed static route (' + (path.length - 1) + ' hops).' + evidence;
        if (path.length > LIMITS.selectedNodes) {
          packet.status = 'unsupported';
          packet.reason = 'Complete path exceeds the 200-node budget; choose closer endpoints.';
          return packet;
        }
        const w = witnessFromChain(path);
        return finishSelection(packet, path, w.edges, path.length > 1 || router.isFolder(from) ? [w] : []);
      }
      if (requested === 'LOCATE') {
        packet.status = 'matched'; packet.reason = evidence;
        if (router.isFolder(ids[0])) {
          const all = router.folderNodes(ids[0]);
          if (offset > all.length) throw new Error('Continuation is past the end of the result');
          const end = offset + LIMITS.selectedNodes - 1;
          if (end < all.length) { packet.truncated = true; packet.continuation = 'offset:' + end; }
          return finishSelection(packet, [ids[0], ...all.slice(offset, end)], [], []);
        }
        return finishSelection(packet, ids, [], []);
      }
      const reached = reach(packet, requested, ids[0], offset);
      reached.reason += ' ' + evidence;
      return reached;
    }

    function query(request) {
      if (!request || typeof request.requestId !== 'string' || !request.requestId || request.requestId.length > 512)
        throw new Error('requestId is required');
      if (typeof request.query !== 'string' || request.query.length > LIMITS.queryChars)
        throw new Error('query must be a bounded string');
      if (request.certainOnly !== undefined && typeof request.certainOnly !== 'boolean') throw new Error('certainOnly must be boolean');
      const packet = base(request);
      if (request.snapshotId !== undefined && request.snapshotId !== snapshot.snapshotId) {
        packet.status = 'stale';
        packet.reason = 'Request was made against a different snapshot; rerun it against the current revision.';
        return packet;
      }
      const offset = parseContinuation(request.continuation);
      const normalized = Scorer.normalizeQuestion(request.query), intent = Scorer.intent(normalized);
      const symbolOp = symbolRequest(request.query);
      const resolved = resolveOperation(packet, request, intent, symbolOp, offset);
      if (resolved) return resolved;
      if (symbolOp) symbolOp.names = symbolOp.names.map(name => lookupSymbol(name).length ? name :
        Scorer.filenameText(name.replace(/^the\s+/, '')));
      // Resolve lexical file/group evidence before dispatch, including ambiguous
      // stems. Explicit missing call symbols must not silently become files.
      const preferSymbol = Scorer.kindHint(request.query) === 'symbol' &&
        (symbolOp?.op !== 'LOCATE' || symbolOp?.names.every(name => lookupSymbol(name).length));
      const legacyTarget = !preferSymbol && symbolOp && symbolOp.names.some(name => nodes.has(name) ||
        [...nodes.values()].some(n => n.path === name || n.label === name) ||
        ((!lookupSymbol(name).length || ['file', 'layer'].includes(Scorer.kindHint(request.query))) &&
          Object.values(scorer.score(name).targets).some(h =>
          h.match.label !== 'No match' && h.match.tier !== 'fuzzy' && !h.match.missingExact)));
      if (symbolOp && symbols && !legacyTarget &&
          (symbolOp.op !== 'LOCATE' || symbolOp.names.some(name => lookupSymbol(name).length))) {
        return boundedSymbolQuery(packet, request, symbolOp, offset);
      }
      // Explicit human choice from a previous needs-choice packet: only known IDs, never fuzzy.
      if (request.chosenNodeId !== undefined) {
        if (!nodes.has(request.chosenNodeId)) throw new Error('Unknown chosen node ID');
        packet.operation = 'LOCATE'; packet.status = 'matched';
        packet.reason = 'Explicitly chosen by the user.';
        return fileOperation(packet, 'LOCATE', [request.chosenNodeId], offset, packet.reason);
      }
      const fileOp = symbolOp && legacyTarget && symbolOp.op !== 'LOCATE' ?
        ({CALLERS: 'DOWNSTREAM', CALLEES: 'UPSTREAM', TRACE: 'UPSTREAM', FLOW: 'PATH'})[symbolOp.op] : null;
      const result = scorer.score(fileOp ? operationQuery(fileOp, symbolOp.names) : request.query); // validates its own result contract
      const requested = result.requestedOperation;
      if (!result.yes) {
        packet.alternatives = alternativesFrom(result);
        if (!packet.alternatives.length && requested === 'LOCATE' &&
            Object.values(result.targets).every(h => !h.match.missingExact)) {
          packet.alternatives = concepts.search(request.query);
          if (packet.alternatives.length) {
            packet.status = 'needs-choice';
            packet.reason = 'Concept search found possible locations, not an exact answer. Choose a candidate explicitly.';
            return packet;
          }
        }
        packet.status = packet.alternatives.length ? 'needs-choice' : 'no-match';
        packet.reason = result.reason;
        return packet;
      }
      if (requested === 'PATH') {
        const from = result.targets.from_target.choice, to = result.targets.to_target.choice;
        const evidence = ' From: ' + result.targets.from_target.reason + ' To: ' + result.targets.to_target.reason;
        return fileOperation(packet, requested, [from, to], offset, evidence);
      }
      const seed = result.targets.locate_target.choice;
      return fileOperation(packet, requested, [seed], offset, result.targets.locate_target.reason);
    }
    return {query, limits: LIMITS, conceptStats: concepts.stats};
  }

  function querySnapshot(snapshot, request, options) {
    return createQueryService(snapshot, options).query(request);
  }
  return {createQueryService, querySnapshot, createConceptIndex, PACKET_SCHEMA, LIMITS};
});
