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
  // Explicit concept morphology, not query aliases: applies to all metadata and queries.
  // auth is the map's abbreviation; grader is the runner's documented responsibility.
  const MORPH = {authentication: 'auth', authenticated: 'auth', authenticating: 'auth',
    grading: 'grade', grader: 'grade', graded: 'grade'};
  function normalized(text) { return tokens(text).map(t => MORPH[t] || t).join(' '); }
  function terms(text) { return [...new Set(tokens(text).filter(t => !STOP.has(t)).map(t => MORPH[t] || t))]; }
  function editDistance(a, b) {
    let row = Array.from({length: b.length + 1}, (_, i) => i);
    for (let i = 1; i <= a.length; i++) {
      const next = [i];
      for (let j = 1; j <= b.length; j++) next[j] = Math.min(next[j - 1] + 1, row[j] + 1,
        row[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
      row = next;
    }
    return row[b.length];
  }
  function filenameText(text) {
    return text.trim().replace(/[?!]+$/, '').replace(/[`"']/g, '')
      .replace(/^(?:please\s+)?(?:where\s+(?:is|are|does)|find|locate|show(?:\s+me)?)\s+(?:the\s+)?/i, '')
      .replace(/\s+(?:live|lives|located)$/i, '')
      .replace(/^(?:file(?:name)?|named)\s+/i, '').replace(/\s+file$/i, '').trim();
  }
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
    if (result.evidenceVersion !== undefined && result.evidenceVersion !== 1) throw new Error('Unknown evidence version');
    for (const h of Object.values(result.targets)) {
      validateHead(h, ids);
      if (result.evidenceVersion === 1 || h.match !== undefined || h.suggestions !== undefined) {
        const m = h.match;
        if (!m || !['Exact match', 'Likely match', 'Needs your choice', 'No match'].includes(m.label) ||
            !['path', 'basename', 'stem', 'partial', 'fuzzy', 'none', 'lexical'].includes(m.tier) ||
            (m.label === 'Exact match' && m.mode === 'filename' && !['path', 'basename'].includes(m.tier)) ||
            !['filename', 'architecture'].includes(m.mode) || typeof m.query !== 'string' ||
            !Number.isFinite(m.margin) || m.margin < 0 || !Number.isFinite(m.coverage) || m.coverage < 0 || m.coverage > 1 ||
            typeof m.missingExact !== 'boolean' || !Array.isArray(h.suggestions) ||
            (h.yes !== ['Exact match', 'Likely match'].includes(m.label)) ||
            (h.yes && (m.missingExact || m.tier === 'fuzzy' || m.margin < 1 || m.coverage < 0.6)) ||
            (m.label === 'No match' && h.suggestions.length) ||
            (m.label !== 'No match' && !h.suggestions.length)) throw new Error('Invalid match evidence');
        let previous = Infinity;
        const seen = new Set();
        for (const a of h.suggestions) {
          const n = map.nodes.find(n => n.id === a.id);
          if (!n || seen.has(a.id) || (m.mode === 'filename' && n.kind !== 'file' && !(n.kind === undefined && n.path)) ||
              a.path !== (n.path || '') || JSON.stringify(a.aliases) !== JSON.stringify(n.aliases || []) ||
              typeof a.reason !== 'string' || !a.reason || !Number.isFinite(a.score) || a.score <= 0 ||
              a.probability !== h.probabilities[a.id] || a.probability > previous || !a.components ||
              Object.values(a.components).some(v => !Number.isFinite(v))) throw new Error('Invalid suggestion evidence');
          previous = a.probability; seen.add(a.id);
        }
      }
      if (typeof h.yes !== 'boolean' || typeof h.reason !== 'string' || !h.reason ||
          !Array.isArray(h.top3) || h.top3.length !== Math.min(3, ids.length) ||
          h.top3[0].id !== h.choice || new Set(h.top3.map(a => a.id)).size !== h.top3.length)
        throw new Error('Invalid alternatives');
      let previous = Infinity;
      for (const a of h.top3) {
        if (!ids.includes(a.id) || !Number.isFinite(a.score) || a.probability !== h.probabilities[a.id] || a.probability > previous ||
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
  function createScorer(map, learnedAliases = []) {
    if (!map || !Array.isArray(map.nodes) || !map.nodes.length) throw new Error('Map needs indexed nodes');
    const ids = map.nodes.map(n => n.id);
    if (ids.some(id => typeof id !== 'string' || !id) || new Set(ids).size !== ids.length)
      throw new Error('Map IDs must be unique strings');
    const aliasKey = value => value.trim().toLowerCase().replace(/\s+/g, ' ');
    if (!Array.isArray(learnedAliases) || learnedAliases.length > 1000) throw new Error('Invalid alias overlay');
    const overlay = learnedAliases.map(a => {
      if (!a || typeof a.alias !== 'string' || !a.alias.trim() || a.alias.length > 160 ||
          /[\u0000-\u001f\u007f-\u009f\ud800-\udfff]/u.test(a.alias) || !ids.includes(a.nodeId))
        throw new Error('Invalid alias overlay');
      return {alias: aliasKey(a.alias), nodeId: a.nodeId};
    });
    const incoming = Object.fromEntries(ids.map(id => [id, 0]));
    for (const e of [...(map.edges || []), ...(map.file_edges || [])]) {
      if (!ids.includes(e.from) || !ids.includes(e.to)) throw new Error('Unknown edge endpoint');
      if (e.type !== 'realtime') incoming[e.to]++;
    }
    const index = map.nodes.map(n => ({
      node: n, kind: n.kind, literalPath: n.path || '', basename: (n.path || '').split('/').at(-1),
      stem: (n.path || '').split('/').at(-1).replace(/\.[^.]+$/, ''),
      id: n.id, label: normalized(n.label), aliases: (n.aliases || []).map(normalized),
      identity: normalized(n.id), path: normalized(n.path),
      labelTerms: new Set(terms(n.label)), aliasTerms: new Set(terms((n.aliases || []).join(' '))),
      descTerms: new Set(terms(n.desc)), pathTerms: new Set(terms(n.path)),
      prior: Math.min(0.08, Math.log1p(incoming[n.id]) * 0.015)
    }));
    function fileRequest(text) {
      // Extract whole literal tokens, never truncate/repair a path into a different file.
      const literalNames = (text.match(/[^\s`"'?!,;()]+/g) || []).filter(name =>
        name.includes('.') && /^[\w./@\[\]-]+$/.test(name));
      const query = literalNames.length === 1 ? literalNames[0] : filenameText(text);
      const literal = /^[\w./@\[\]-]+$/.test(query);
      const explicit = /\bfile(?:name)?\b/i.test(text) || literalNames.length > 0 || (literal && /[/.]/.test(query));
      const known = index.some(n => n.kind === 'file' && (n.basename === query || n.stem === query));
      const layer = index.some(n => n.kind === 'layer' &&
        [n.identity, n.label, ...n.aliases].includes(normalized(query)));
      // Bare architectural aliases remain layers unless syntax explicitly asks for a file.
      const shaped = literal && (/_|[a-z][A-Z]/.test(query) || (query.includes('-') && !layer));
      const nearStem = !layer && literal && query.length >= 5 && index.some(n => {
        if (n.kind !== 'file' || Math.abs(query.length - n.stem.length) > 2) return false;
        const d = editDistance(query.toLowerCase(), n.stem.toLowerCase());
        return d > 0 && d <= (query.length < 8 ? 1 : 2) && d / Math.max(query.length, n.stem.length) <= 0.2;
      });
      return (explicit || (known && !layer) || shaped || nearStem) ? {query, explicit} : null;
    }
    function finish(scored, mode, query, missingExact) {
      const h = head(ids, scored.map(s => s.score));
      const sorted = scored.slice().sort((a, b) => b.score - a.score || ids.indexOf(a.id) - ids.indexOf(b.id));
      const best = sorted[0], margin = best.score - (sorted[1]?.score || 0);
      const present = sorted.filter(s => s.evidence > 0 && s.coverage >= 0.6);
      const exact = mode === 'filename' ? ['path', 'basename'].includes(best.tier) : best.exact;
      h.yes = best.evidence >= 4 && best.coverage >= 0.6 && margin >= 1 &&
        !missingExact && best.tier !== 'fuzzy';
      const label = h.yes ? (exact ? 'Exact match' : 'Likely match') : present.length ? 'Needs your choice' : 'No match';
      h.match = {label, mode, tier: best.tier || 'lexical', query, margin, coverage: best.coverage,
        missingExact: Boolean(missingExact)};
      const evidenceReason = h.yes ? best.matchReason : !present.length ?
        'Insufficient lexical evidence; no supported suggestions.' : margin < 1 ?
          'Multiple candidates have comparable evidence. Choose a full path or alternative explicitly.' :
          mode === 'filename' ? 'Nonexact filename suggestion only. Choose an override explicitly.' :
            'Insufficient responsibility evidence or separation. Choose a supported alternative explicitly.';
      h.reason = (missingExact ? 'No exact file named ' + query + '. ' : '') + evidenceReason;
      const alternative = s => {
        const n = map.nodes[ids.indexOf(s.id)];
        return {id: s.id, probability: h.probabilities[s.id], score: s.score, components: s.components,
          path: n.path || '', aliases: (n.aliases || []).slice(), reason: s.matchReason || 'No lexical evidence.'};
      };
      h.top3 = sorted.slice(0, 3).map(alternative);
      // Show all tied filenames (not only top three); never offer uniform argmax as evidence.
      const tied = present.filter(s => s.score === best.score);
      const suggestions = mode === 'filename' ? tied.concat(
        present.filter(s => s.score !== best.score).slice(0, Math.max(0, 3 - tied.length))) : present.slice(0, 3);
      h.suggestions = suggestions.map(alternative);
      return h;
    }
    function rankFile(request) {
      const query = request.query, base = query.split('/').at(-1), stem = base.replace(/\.[^.]+$/, '');
      const extension = base.includes('.') ? base.slice(base.lastIndexOf('.')) : '';
      const hasPath = query.includes('/');
      const q = tokens(stem);
      const scored = index.map(n => {
        let tier = 'none', score = 0, coverage = 0, matchReason = 'No filename evidence.';
        if (n.kind === 'file' || (n.kind === undefined && n.literalPath)) {
          // A bare name is a basename request even if one candidate happens to be at repo root.
          // Only a directory-qualified literal disambiguates duplicate basenames automatically.
          if (hasPath && n.literalPath === query) { tier = 'path'; score = 60; }
          else if (!hasPath && n.basename === query) { tier = 'basename'; score = 50; }
          else if (!extension && (hasPath ? n.literalPath.replace(/\.[^.]+$/, '') === query : n.stem === query)) { tier = 'stem'; score = 40; }
          else {
            const nt = tokens(n.stem);
            const tokenMatch = q.length > 0 && q.every(t => nt.includes(t));
            const partial = stem.length >= 4 && n.stem.toLowerCase().includes(stem.toLowerCase());
            if (!hasPath && (!extension || n.basename.endsWith(extension)) && stem.length >= 4 && (tokenMatch || partial)) {
              tier = 'partial'; score = 30; coverage = 1;
            } else {
              const a = query.toLowerCase(), b = (hasPath ? n.literalPath : extension ? n.basename : n.stem).toLowerCase();
              // Fuzzy can propose, never accept; only minor spelling edits on useful-length strings.
              if (a.length >= 5 && Math.abs(a.length - b.length) <= 2) {
                const distance = editDistance(a, b), limit = a.length < 8 ? 1 : 2;
                if (distance > 0 && distance <= limit && distance / Math.max(a.length, b.length) <= 0.2) {
                  tier = 'fuzzy'; score = 20 - distance; coverage = 1;
                  matchReason = 'Minor spelling difference (' + distance + ' edit' + (distance === 1 ? '' : 's') + '); suggestion only.';
                }
              }
            }
          }
          if (score && tier !== 'fuzzy') {
            coverage = 1;
            matchReason = {path: 'Exact full path.', basename: 'Exact basename.', stem: 'Exact filename stem (extension omitted).',
              partial: 'Filename token or partial-name evidence; not an exact filename.'}[tier];
          }
        }
        return {id: n.id, score, evidence: score, coverage, tier, matchReason,
          components: {path: tier === 'path' ? score : 0, basename: tier === 'basename' ? score : 0,
            stem: tier === 'stem' ? score : 0, partial: tier === 'partial' ? score : 0,
            fuzzy: tier === 'fuzzy' ? score : 0, structural: 0}};
      });
      const missingExact = Boolean((extension || hasPath) && !scored.some(s =>
        ['path', 'basename'].includes(s.tier) || (!extension && s.tier === 'stem')));
      return finish(scored, 'filename', query, missingExact);
    }
    function rank(text) {
      const file = fileRequest(text);
      // Real literal filenames/paths (including ambiguous basenames) always win.
      const realFile = file && index.some(n => n.kind === 'file' &&
        (file.query.includes('/') ? n.literalPath === file.query : n.basename === file.query));
      const learned = new Set(overlay.filter(a => a.alias === aliasKey(filenameText(text))).map(a => a.nodeId));
      if (learned.size && !realFile) {
        const h = finish(index.map(n => ({id: n.id, score: learned.has(n.id) ? 30 : 0,
          evidence: learned.has(n.id) ? 30 : 0, coverage: learned.has(n.id) ? 1 : 0,
          exact: true, components: {learnedAlias: learned.has(n.id) ? 30 : 0},
          matchReason: 'Explicitly confirmed learned alias.'})), 'architecture', text, false);
        if (learned.size > 1) {
          // Preserve all conflicting targets, including those beyond top three.
          h.suggestions = index.filter(n => learned.has(n.id)).map(n => ({id: n.id,
            score: 30, probability: h.probabilities[n.id], components: {learnedAlias: 30},
            path: n.node.path || '', aliases: (n.node.aliases || []).slice(), reason: 'Conflicting learned alias — choose explicitly.'}));
          h.reason = 'Conflicting learned alias — choose a real target explicitly.';
        }
        return h;
      }
      if (file) return rankFile(file);
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
        // Architecture retrieval uses layer responsibility metadata, not filename fragments.
        if (n.kind === 'file') Object.keys(c).forEach(k => { c[k] = 0; });
        const evidence = c.label + c.alias + c.description + c.path + c.identity;
        if (evidence > 0) c.structural = n.prior;
        const covered = q.filter(t => n.labelTerms.has(t) || n.aliasTerms.has(t) ||
          n.descTerms.has(t) || n.pathTerms.has(t) || tokens(n.id).includes(t)).length;
        const matches = q.filter(t => n.labelTerms.has(t) || n.aliasTerms.has(t) || n.descTerms.has(t));
        const literalQuery = tokens(filenameText(text)).join(' ');
        const literalExact = value => Boolean(value && tokens(value).join(' ') === literalQuery);
        return {id: n.id, components: c, score: evidence + c.structural, evidence,
          exact: literalExact(n.node.label) || (n.node.aliases || []).some(literalExact) || literalExact(n.id),
          matchReason: 'Layer metadata terms: ' + matches.join(', ') +
            ((n.node.aliases || []).some(literalExact) ? ' (exact alias)' : n.aliases.some(exact) ?
              ' (morphology-normalized alias, not literal spelling)' : literalExact(n.id) ? ' (exact identity)' : '') + '.',
          coverage: q.length ? covered / q.length : 0};
      });
      return finish(scored, 'architecture', text, false);
    }
    function score(query) {
      if (typeof query !== 'string') throw new TypeError('Query must be a string');
      const parsed = intent(query);
      const targets = parsed.op === 'PATH' ? {
        from_target: rank(parsed.from || ''), to_target: rank(parsed.to || '')
      } : {locate_target: rank(parsed.target || '')};
      const yes = !parsed.malformed && Object.values(targets).every(h => h.yes);
      const chosen = yes ? parsed.op : 'NOT_SURE';
      const result = {scoreKind: SCORE_KIND, evidenceVersion: 1, requestedOperation: parsed.op,
        operation: head(OPERATIONS, OPERATIONS.map(op => op === chosen ? 6 : 0)), targets, yes,
        reason: parsed.malformed ? 'PATH requires separately specified endpoints.' : yes ?
          'Accepted by local evidence heuristics; endpoint matching does not imply route success.' :
          Object.values(targets).filter(h => !h.yes).map(h => h.reason).join(' ')};
      validateResult(result, map);
      return result;
    }
    return {score};
  }
  return {createScorer, validateHead, validateResult, tokens, OPERATIONS, SCORE_KIND};
});
