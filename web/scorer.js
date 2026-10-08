/* Local System-1 chooser. No network, dependencies, DOM, or calibrated accuracy. */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.DagGpsScorer = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const OPERATIONS = ['LOCATE', 'UPSTREAM', 'DOWNSTREAM', 'PATH', 'NOT_SURE'];
  const SCORE_KIND = 'heuristic model score (not measured accuracy)';
  const STOP = new Set(('a an the this that these those where which what who does do is are can could would please ' +
    'me tell show find locate live lives located code implementation implement handles handle about for of in on to from ' +
    'get goes reach how through between and with it its into trace route path dependencies depend depends dependents ' +
    'upstream downstream uses use imports import built changed change break if').split(' '));
  function tokens(text) {
    return String(text || '').replace(/([a-z0-9])([A-Z])/g, '$1 $2').toLowerCase().match(/[a-z0-9]+/g) || [];
  }
  function normalized(text) { return tokens(text).join(' '); }
  function terms(text) { return [...new Set(tokens(text).filter(t => !STOP.has(t)))]; }
  function intent(query) {
    const q = query.trim().replace(/[?!]+$/, '');
    let m;
    // Endpoints are split before scoring; one endpoint cannot supply evidence for the other.
    if ((m = q.match(/\bfrom\s+(.+?)\s+to\s+(.+)$/i)) ||
        (m = q.match(/\b(?:path|route)\s+between\s+(.+?)\s+and\s+(.+)$/i)) ||
        (m = q.match(/^how\s+(?:does\s+)?(.+?)\s+(?:reach|connect to|get to)\s+(.+)$/i)))
      return {op: 'PATH', from: m[1], to: m[2]};
    if (/^(?:(?:show|trace|find)\s+(?:a\s+)?)?(?:path|route)(?:\s+(?!handlers\b)|$)/i.test(q) ||
        /^from\s+/i.test(q) || /^how\b.*\b(?:reach|connect|get to)\b/i.test(q))
      return {op: 'PATH', malformed: true};
    if ((m = q.match(/^(?:what|which|who)\s+(?:\w+\s+)?(?:depends? on|uses?|imports?)\s+(.+)$/i)) ||
        (m = q.match(/\b(?:dependents|downstream)(?:\s+(?:of|from))?\s+(.+)$/i)) ||
        (m = q.match(/^what would break if\s+(.+?)\s+changed$/i)))
      return {op: 'DOWNSTREAM', target: m[1]};
    if ((m = q.match(/^(?:what|which)\s+(?:does|do)\s+(.+?)\s+(?:depend on|import|use)$/i)) ||
        (m = q.match(/\b(?:dependencies|upstream)(?:\s+(?:of|from))?\s+(.+)$/i)) ||
        (m = q.match(/^what is\s+(.+?)\s+built on$/i)))
      return {op: 'UPSTREAM', target: m[1]};
    return {op: 'LOCATE', target: q};
  }
  function head(ids, scores) {
    const max = Math.max(...scores);
    const weights = scores.map(s => Math.exp((s - max) / 1.5));
    const sum = weights.reduce((a, b) => a + b, 0);
    const probabilities = Object.fromEntries(ids.map((id, i) => [id, weights[i] / sum]));
    let winner = 0;
    scores.forEach((s, i) => { if (s > scores[winner]) winner = i; });
    return {choice: ids[winner], probabilities, confidence: probabilities[ids[winner]]};
  }
  function validateHead(h, ids) {
    if (!h || !ids.includes(h.choice) || !h.probabilities ||
        Object.keys(h.probabilities).length !== ids.length ||
        ids.some(id => !Object.hasOwn(h.probabilities, id))) throw new Error('Unknown or missing head IDs');
    const ps = ids.map(id => h.probabilities[id]);
    if (ps.some(p => typeof p !== 'number' || !Number.isFinite(p) || p < 0 || p > 1) ||
        Math.abs(ps.reduce((a, b) => a + b, 0) - 1) > 1e-9) throw new Error('Invalid probability distribution');
    if (h.probabilities[h.choice] !== Math.max(...ps)) throw new Error('Choice is not argmax');
    if (!Number.isFinite(h.confidence) || h.confidence !== h.probabilities[h.choice])
      throw new Error('Invalid confidence');
    return true;
  }
  function validateResult(result, map) {
    const ids = map.nodes.map(n => n.id);
    validateHead(result.operation, OPERATIONS);
    if (result.scoreKind !== SCORE_KIND || typeof result.yes !== 'boolean' ||
        typeof result.reason !== 'string' || !result.reason || !result.targets) throw new Error('Invalid result');
    const names = Object.keys(result.targets).sort();
    const expected = result.requestedOperation === 'PATH' ? ['from_target', 'to_target'] : ['locate_target'];
    if (!OPERATIONS.includes(result.requestedOperation) || JSON.stringify(names) !== JSON.stringify(expected))
      throw new Error('Invalid target heads');
    for (const h of Object.values(result.targets)) {
      validateHead(h, ids);
      if (typeof h.yes !== 'boolean' || typeof h.reason !== 'string' || !h.reason ||
          !Array.isArray(h.top3) || h.top3.length !== Math.min(3, ids.length) ||
          h.top3[0].id !== h.choice || new Set(h.top3.map(a => a.id)).size !== h.top3.length)
        throw new Error('Invalid alternatives');
      let previous = Infinity;
      for (const a of h.top3) {
        if (!ids.includes(a.id) || a.probability !== h.probabilities[a.id] || a.probability > previous ||
            !a.components || Object.values(a.components).some(v => !Number.isFinite(v)))
          throw new Error('Invalid alternative score');
        previous = a.probability;
      }
    }
    if (result.yes !== (result.operation.choice !== 'NOT_SURE') ||
        (result.yes && (result.operation.choice !== result.requestedOperation ||
          Object.values(result.targets).some(h => !h.yes)))) throw new Error('Inconsistent acceptance');
    return true;
  }
  function createScorer(map) {
    if (!map || !Array.isArray(map.nodes) || !map.nodes.length) throw new Error('Map needs indexed nodes');
    const ids = map.nodes.map(n => n.id);
    if (ids.some(id => typeof id !== 'string' || !id) || new Set(ids).size !== ids.length)
      throw new Error('Map IDs must be unique strings');
    const incoming = Object.fromEntries(ids.map(id => [id, 0]));
    for (const e of [...(map.edges || []), ...(map.file_edges || [])]) {
      if (!ids.includes(e.from) || !ids.includes(e.to)) throw new Error('Unknown edge endpoint');
      if (e.type !== 'realtime') incoming[e.to]++;
    }
    const index = map.nodes.map(n => ({
      id: n.id, label: normalized(n.label), aliases: (n.aliases || []).map(normalized),
      identity: normalized(n.id), path: normalized(n.path),
      labelTerms: new Set(terms(n.label)), aliasTerms: new Set(terms((n.aliases || []).join(' '))),
      descTerms: new Set(terms(n.desc)), pathTerms: new Set(terms(n.path)),
      prior: Math.min(0.08, Math.log1p(incoming[n.id]) * 0.015)
    }));
    function rank(text) {
      const q = terms(text); const phrase = q.join(' '); const raw = normalized(text);
      const overlap = set => q.length ? q.filter(t => set.has(t)).length / q.length : 0;
      const scored = index.map(n => {
        const exact = field => Boolean(field && (field === raw || field === phrase));
        // Preserve literal IDs/paths even when their segments are also intent words (route.ts).
        const literal = field => Boolean(field && (` ${raw} `).includes(` ${field} `));
        const c = {
          label: exact(n.label) ? 8 : 4 * overlap(n.labelTerms),
          alias: n.aliases.some(exact) ? 9 : 4.5 * overlap(n.aliasTerms),
          description: 1.5 * overlap(n.descTerms),
          path: literal(n.path) ? 14 : 3 * overlap(n.pathTerms),
          identity: (exact(n.identity) || (n.path && literal(n.identity))) ? 11 : 0,
          structural: 0
        };
        const evidence = c.label + c.alias + c.description + c.path + c.identity;
        if (evidence > 0) c.structural = n.prior;
        const covered = q.filter(t => n.labelTerms.has(t) || n.aliasTerms.has(t) ||
          n.descTerms.has(t) || n.pathTerms.has(t) || tokens(n.id).includes(t)).length;
        return {id: n.id, components: c, score: evidence + c.structural, evidence,
          coverage: q.length ? covered / q.length : 0};
      });
      const h = head(ids, scored.map(s => s.score));
      const sorted = scored.slice().sort((a, b) => b.score - a.score || ids.indexOf(a.id) - ids.indexOf(b.id));
      const best = sorted[0]; const margin = best.score - (sorted[1]?.score || 0);
      h.yes = q.length > 0 && best.evidence >= 4 && best.coverage >= 0.6 && margin >= 1;
      h.reason = !q.length ? 'No searchable terms.' : best.evidence < 4 || best.coverage < 0.6 ?
        'Insufficient lexical evidence; structural prior cannot create a match.' : margin < 1 ?
          'Ambiguous candidates: lexical score margin is below 1.' : 'Lexical evidence and separation pass heuristic thresholds.';
      h.top3 = sorted.slice(0, 3).map(s => ({id: s.id, probability: h.probabilities[s.id],
        score: s.score, components: s.components}));
      return h;
    }
    function score(query) {
      if (typeof query !== 'string') throw new TypeError('Query must be a string');
      const parsed = intent(query);
      const targets = parsed.op === 'PATH' ? {
        from_target: rank(parsed.from || ''), to_target: rank(parsed.to || '')
      } : {locate_target: rank(parsed.target || '')};
      const yes = !parsed.malformed && Object.values(targets).every(h => h.yes);
      const chosen = yes ? parsed.op : 'NOT_SURE';
      const result = {scoreKind: SCORE_KIND, requestedOperation: parsed.op,
        operation: head(OPERATIONS, OPERATIONS.map(op => op === chosen ? 6 : 0)), targets, yes,
        reason: parsed.malformed ? 'PATH requires separately specified endpoints.' : yes ?
          'Accepted by local lexical heuristics; graph traversal is deferred to M3.' :
          Object.values(targets).filter(h => !h.yes).map(h => h.reason).join(' ')};
      validateResult(result, map);
      return result;
    }
    return {score};
  }
  return {createScorer, validateHead, validateResult, tokens, OPERATIONS, SCORE_KIND};
});
