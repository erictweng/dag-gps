/* DAG GPS workspace client (M2.3). Untrusted repository data is rendered with
 * textContent / SVG text only. Highlights come from evidence packets or observed edges. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const GV = window.DagGpsGraphView;
  const MAX_LIST = 2000;
  const fromHash = /(?:^|[#&])session=([A-Za-z0-9_-]{20,128})/.exec(location.hash);
  if (fromHash) {
    sessionStorage.setItem('dag-gps-session', fromHash[1]);
    history.replaceState(null, '', location.pathname);
  }
  const session = sessionStorage.getItem('dag-gps-session');
  if (!session) $('session-warning').hidden = false;

  async function api(method, path, body) {
    const options = {method, headers: {'X-DAG-GPS-Session': session || ''}, credentials: 'omit', cache: 'no-store'};
    if (body !== undefined) { options.headers['Content-Type'] = 'application/json'; options.body = JSON.stringify(body); }
    const response = await fetch(path, options);
    const value = await response.json().catch(() => ({error: 'Unreadable response'}));
    if (!response.ok) throw new Error(value.error || ('HTTP ' + response.status));
    return value;
  }
  const text = (id, value) => { $(id).textContent = value; };
  const clear = id => $(id).replaceChildren();
  function li(listId, label, onClick, extra) {
    const item = document.createElement('li');
    if (onClick) {
      const b = document.createElement('button');
      b.type = 'button'; b.textContent = label; b.addEventListener('click', onClick);
      if (extra) Object.assign(b.dataset, extra);
      item.appendChild(b);
    } else item.textContent = label;
    $(listId).appendChild(item);
    return item;
  }

  const graph = GV.createGraphView($('graph'), {onSelect: id => selectFile(id, {fromGraph: true})});
  const state = {projects: [], project: null, snapshot: null, request: null,
    files: new Map(), nodes: new Map(), groupLabel: new Map(), packet: null, context: null,
    epoch: 0, sourceVersion: 0, consentVersion: 0};

  // ---------------------------------------------------------------- projects
  async function loadProjects(selectId) {
    state.projects = (await api('GET', '/api/projects')).projects;
    const select = $('project-select');
    select.replaceChildren();
    for (const p of state.projects) {
      const option = document.createElement('option');
      option.value = p.projectId; option.textContent = p.repo;
      select.appendChild(option);
    }
    if (selectId) select.value = selectId;
    if (!state.projects.length) {
      text('project-info', 'No projects yet. Open "Import a repository" above.');
      $('import-box').open = true;
      return;
    }
    await pickProject();
  }
  async function pickProject() {
    state.project = state.projects.find(p => p.projectId === $('project-select').value) || state.projects[0];
    const revs = Object.values(state.project.snapshots).sort((a, b) => b.importedAt - a.importedAt);
    const select = $('revision-select');
    select.replaceChildren();
    for (const r of revs) {
      const option = document.createElement('option');
      option.value = r.snapshotId;
      option.textContent = r.commit.slice(0, 7) + (r.snapshotId === state.project.current.snapshotId ? ' (latest)' : '');
      select.appendChild(option);
    }
    select.value = state.project.current.snapshotId;
    await loadSnapshot(select.value);
  }
  async function loadSnapshot(snapshotId) {
    const graphBox = $('graph'), scroll = [graphBox.scrollLeft, graphBox.scrollTop];
    const sameProject = Boolean(state.snapshot && state.snapshot.projectId === state.project.projectId);
    resetAnswer();
    const epoch = state.epoch;
    const snap = await api('GET', '/api/projects/' + state.project.projectId + '/snapshots/' + snapshotId);
    if (epoch !== state.epoch) return;
    state.snapshot = snap;
    state.files = new Map(snap.inventory.map(f => [f.path, f]));
    state.nodes = new Map(snap.map.nodes.map(n => [n.id, n]));
    state.groupLabel = new Map(snap.map.nodes.filter(n => n.kind === 'layer').map(n => [n.id, n.label || n.id]));
    const counts = (snap.map.meta && snap.map.meta.counts) || {};
    text('project-info', snap.source.repo + ' @ ' + snap.source.commit.slice(0, 7) + ' — ' + snap.inventory.length + ' files, ' +
      (counts.files || 0) + ' mapped, ' + (counts.file_edges || 0) + ' links' +
      (snap.extractionState === 'partial' ? ' · partial extraction (some imports could not be resolved)' : '') +
      '. Groups are proposed from folders, not reviewed.');
    graph.render(snap.map);
    if (sameProject) { graphBox.scrollLeft = scroll[0]; graphBox.scrollTop = scroll[1]; }
    renderFileList();
    resetAnswer();
  }
  $('project-select').addEventListener('change', () => pickProject().catch(showError));
  $('revision-select').addEventListener('change', () => loadSnapshot($('revision-select').value).catch(showError));

  // ---------------------------------------------------------------- file list
  function renderFileList() {
    const filter = $('file-filter').value.trim().toLowerCase();
    clear('file-list');
    const all = state.snapshot ? state.snapshot.inventory : [];
    const shown = all.filter(f => !filter || f.path.toLowerCase().includes(filter));
    for (const f of shown.slice(0, MAX_LIST)) {
      const mapped = state.nodes.has(f.path);
      li('file-list', f.path + (mapped ? '' : '  (not mapped)'), () => selectFile(f.path), {path: f.path});
    }
    text('file-count', shown.length + ' of ' + all.length + ' files' +
      (shown.length > MAX_LIST ? ' (first ' + MAX_LIST + ' shown; filter to narrow)' : ''));
  }
  $('file-filter').addEventListener('input', renderFileList);

  // ---------------------------------------------------------------- answers
  const STATUS = {
    'matched': 'Found', 'needs-choice': 'Several possible matches — choose one',
    'no-match': 'No match', 'no-path': 'No directed path', 'unsupported': 'Not supported', 'stale': 'Out of date'
  };
  function hideAnswerLists() {
    for (const id of ['choices', 'results', 'limitations']) clear(id);
    $('choices-heading').hidden = $('results-heading').hidden = $('more').hidden = true;
    $('limitations-box').hidden = true;
  }
  function resetAnswer(message) {
    resetAgent();
    state.epoch++; state.sourceVersion++;
    $('source-viewer').hidden = true;
    graph.apply(null);
    text('answer-status', message || 'Ask a question or pick a file.');
    text('answer-reason', '');
    hideAnswerLists();
    $('detail').hidden = true;
    for (const b of document.querySelectorAll('#file-list button[aria-current]')) b.removeAttribute('aria-current');
  }
  function showError(error) { text('answer-status', 'Something went wrong: ' + error.message); }

  async function ask(extra) {
    if (!state.snapshot) { text('answer-status', 'Import or select a project first.'); return; }
    const snapshot = state.snapshot, project = state.project;
    const epoch = ++state.epoch;
    resetAgent();
    const request = Object.assign({snapshotId: snapshot.snapshotId, requestId: 'ui-' + crypto.randomUUID(),
      query: $('question').value.trim()}, extra || {});
    if (!request.query) return;
    try {
      const packet = await api('POST', '/api/projects/' + project.projectId + '/query', request);
      if (epoch !== state.epoch || snapshot !== state.snapshot) return;
      state.request = request; state.packet = packet;
      render(packet, Boolean(extra && extra.continuation));
    } catch (error) { if (epoch === state.epoch) showError(error); }
  }
  function render(packet, append) {
    const request = state.request;
    $('detail').hidden = true;
    text('answer-status', (STATUS[packet.status] || packet.status) +
      (packet.operation !== 'NOT_SURE' ? ' · ' + packet.operation.toLowerCase() : '') +
      (packet.highlightState === 'potential-impact' ? ' · potentially affected, not guaranteed to break' : ''));
    text('answer-reason', packet.reason || '');
    clear('choices');
    $('choices-heading').hidden = !packet.alternatives.length;
    for (const a of packet.alternatives)
      li('choices', (a.path || a.nodeId) + ' — ' + a.reason, () => ask({query: request.query, chosenNodeId: a.nodeId}));
    if (!append) clear('results');
    const witness = new Map(packet.witnesses.map(w => [w.nodeIds[0] === packet.seedNodeId ? w.nodeIds.at(-1) : w.nodeIds[0], w]));
    for (const id of packet.selectedNodeIds) {
      const w = witness.get(id);
      const label = id + (id === packet.seedNodeId ? ' (asked about)' : '') +
        (w && w.nodeIds.length > 2 ? '  via ' + w.nodeIds.join(' → ') : '');
      li('results', label, () => selectFile(id, {keepAnswer: true}));
    }
    $('results-heading').hidden = !$('results').children.length;
    $('more').hidden = !packet.truncated;
    $('more').onclick = () => ask({query: request.query, continuation: packet.continuation});
    clear('limitations');
    for (const l of packet.limitations) li('limitations', l);
    $('limitations-box').hidden = !packet.limitations.length;
    graph.apply(GV.highlightFor(packet));
    $('agent-section').hidden = false;
    refreshExplanations(request).catch(error => { if (request === state.request) text('agent-error', error.message); });
  }
  $('ask-form').addEventListener('submit', event => { event.preventDefault(); ask(); });

  // ---------------------------------------------------------------- selection
  function selectFile(path, options = {}) {
    if (!state.snapshot) return;
    const node = state.nodes.get(path);
    if (node && node.kind === 'layer') { $('question').value = node.label || node.id; ask(); return; }
    const file = state.files.get(path);
    if (!file) return;
    if (!options.keepAnswer) {
      resetAgent(); state.epoch++;
      hideAnswerLists();
      text('answer-status', 'Selected ' + path);
      text('answer-reason', node ? 'Highlighted with its direct observed import links.'
        : 'This file is inventoried but not part of the dependency map.');
    }
    state.sourceVersion++; $('source-viewer').hidden = true;
    $('view-source').onclick = () => openSource(file.path);
    text('detail-path', file.path);
    text('detail-group', node ? (state.groupLabel.get(node.layer) || node.layer) : 'Not mapped');
    text('detail-lines', file.lineCount === null ? 'Unknown' : String(file.lineCount));
    text('detail-sha', file.sha256);
    text('detail-extraction', file.extraction ?
      (file.extraction.status + (file.extraction.reason ? ' — ' + file.extraction.reason : '')) : 'Unknown');
    clear('detail-out'); clear('detail-in');
    const edges = (state.snapshot.map.file_edges || []).filter(e => e.type !== 'realtime');
    const out = edges.filter(e => e.from === path), inc = edges.filter(e => e.to === path);
    for (const e of out) li('detail-out', e.to + ' (' + e.type + ')', () => selectFile(e.to));
    for (const e of inc) li('detail-in', e.from + ' (' + e.type + ')', () => selectFile(e.from));
    if (!out.length) li('detail-out', 'None observed');
    if (!inc.length) li('detail-in', 'None observed');
    $('detail-dependents').disabled = $('detail-dependencies').disabled = !node;
    $('detail-dependents').onclick = () => { $('question').value = 'what depends on ' + path; ask(); };
    $('detail-dependencies').onclick = () => { $('question').value = 'dependencies of ' + path; ask(); };
    $('detail').hidden = false;
    for (const b of document.querySelectorAll('#file-list button')) {
      if (b.dataset.path === path) b.setAttribute('aria-current', 'true'); else b.removeAttribute('aria-current');
    }
    if (!options.keepAnswer) graph.apply(node ? GV.neighborhood(state.snapshot.map, path) : null);
    if (!options.fromGraph) $('detail-heading').focus({preventScroll: true});
  }
  $('detail-heading').tabIndex = -1;

  // ------------------------------------------------ revision-bound source / agents
  function resetAgent() {
    state.request = state.packet = state.context = null;
    state.consentVersion++;
    $('agent-section').hidden = true;
    $('agent-consent').checked = false;
    $('prepare-context').disabled = true;
    $('attach-explanation').disabled = false;
    $('context-export').hidden = true;
    $('context-json').value = $('explanation-json').value = '';
    for (const id of ['agent-error', 'copy-status', 'explanation-warning', 'explanation-list', 'other-explanations']) clear(id);
    $('other-explanations-section').hidden = true;
  }
  async function openSource(path, start = null, end = null, append = false) {
    const snapshot = state.snapshot, project = state.project;
    if (!snapshot) return;
    const version = ++state.sourceVersion;
    $('source-viewer').hidden = false;
    $('source-more').hidden = true;
    if (!append) clear('source-lines');
    text('source-error', 'Loading source…');
    text('source-meta', path + ' · Commit ' + snapshot.source.commit);
    if (!append) $('source-heading').focus();
    const body = {snapshotId: snapshot.snapshotId, path};
    if (start !== null) body.start = start;
    if (end !== null) body.end = end;
    try {
      const source = await api('POST', '/api/projects/' + project.projectId + '/source', body);
      if (snapshot !== state.snapshot || version !== state.sourceVersion) return;
      text('source-meta', path + ' · Commit ' + snapshot.source.commit + ' · SHA-256 ' + source.sha256);
      if (!append) $('source-lines').start = source.start || 1;
      for (const line of source.lines) li('source-lines', line || ' ');
      text('source-error', source.lines.length ? '' : (source.truncated ? 'A whole line exceeds the excerpt byte limit.' : 'Empty file.'));
      $('source-more').hidden = source.nextStart === null || !source.lines.length;
      $('source-more').onclick = () => openSource(path, source.nextStart, end, true);
    } catch (error) {
      if (snapshot === state.snapshot && version === state.sourceVersion) text('source-error', error.message);
    }
  }
  $('agent-consent').addEventListener('change', () => {
    state.consentVersion++;
    $('prepare-context').disabled = !$('agent-consent').checked;
    if (!$('agent-consent').checked) {
      state.context = null;
      $('context-export').hidden = true; $('context-json').value = '';
    }
  });
  $('prepare-context').addEventListener('click', async () => {
    if (!$('agent-consent').checked || !state.request) return;
    const request = state.request, consentVersion = state.consentVersion;
    $('prepare-context').disabled = true;
    text('agent-error', '');
    try {
      const bundle = await api('POST', '/api/projects/' + state.project.projectId + '/context', {...request, consent: true});
      if (request !== state.request || consentVersion !== state.consentVersion || !$('agent-consent').checked) return;
      state.context = bundle.context;
      $('context-json').value = JSON.stringify(bundle, null, 2);
      $('context-export').hidden = false;
      await refreshExplanations(request);
    } catch (error) { if (request === state.request) text('agent-error', error.message); }
    finally { if (request === state.request) $('prepare-context').disabled = !$('agent-consent').checked; }
  });
  $('copy-context').addEventListener('click', async () => {
    const value = $('context-json').value;
    if (!value || !$('agent-consent').checked) return;
    try {
      await navigator.clipboard.writeText(value);
      text('copy-status', 'Copied JSON.');
    } catch (_) {
      $('context-json').focus(); $('context-json').select();
      text('copy-status', 'JSON selected. Press Ctrl+C or Command+C to copy.');
    }
  });
  $('attach-explanation').addEventListener('click', async () => {
    const request = state.request;
    if (!request) return;
    text('agent-error', ''); $('attach-explanation').disabled = true;
    try {
      let explanation;
      try { explanation = JSON.parse($('explanation-json').value); }
      catch (_) { throw new Error('Invalid JSON. Paste the complete dag-gps-explanation/v1 object.'); }
      const {snapshotId, ...query} = request;
      await api('POST', '/api/projects/' + state.project.projectId + '/explanations',
        {snapshotId, request: query, explanation, useContext: Boolean(state.context)});
      if (request === state.request) await refreshExplanations(request);
    } catch (error) { if (request === state.request) text('agent-error', error.message); }
    finally { if (request === state.request) $('attach-explanation').disabled = false; }
  });
  function element(parent, tag, value, className) {
    const node = document.createElement(tag); node.textContent = value;
    if (className) node.className = className;
    parent.appendChild(node); return node;
  }
  function citations(parent, entries) {
    for (const citation of entries) {
      const b = element(parent, 'button', citation.path + (citation.start === null ? ' (file)' :
        ':' + citation.start + '–' + citation.end), 'citation');
      b.type = 'button';
      b.addEventListener('click', () => openSource(citation.path, citation.start, citation.end));
    }
  }
  // JSON objects are unordered; arrays and every nested key remain significant.
  // Only the packet's top-level request identity is transport-specific.
  function sameAnswer(a, b, topLevel = true) {
    if (a === b) return true;
    if (a === null || b === null || typeof a !== 'object' || typeof b !== 'object') return false;
    if (Array.isArray(a) || Array.isArray(b)) {
      return Array.isArray(a) && Array.isArray(b) && a.length === b.length &&
        a.every((value, i) => sameAnswer(value, b[i], false));
    }
    const keys = Object.keys(a).filter(key => !topLevel || key !== 'requestId');
    const otherKeys = Object.keys(b).filter(key => !topLevel || key !== 'requestId');
    return keys.length === otherKeys.length && keys.every(key =>
      Object.prototype.hasOwnProperty.call(b, key) && sameAnswer(a[key], b[key], false));
  }
  async function refreshExplanations(request) {
    const snapshot = state.snapshot;
    const result = await api('GET', '/api/projects/' + snapshot.projectId + '/snapshots/' + snapshot.snapshotId + '/explanations');
    if (request !== state.request || snapshot !== state.snapshot) return;
    clear('explanation-list');
    clear('other-explanations');
    $('other-explanations-section').hidden = true;
    const invalid = result.explanations.filter(item => !item.valid).length;
    text('explanation-warning', invalid ? invalid + ' invalid stored explanation(s) hidden.' : '');
    for (const item of result.explanations) {
      if (!item.valid) continue; // Never render invalid record text or errors.
      const explanation = item.record.explanation;
      const packet = item.record.packet;
      if (packet.projectId !== snapshot.projectId || packet.snapshotId !== snapshot.snapshotId) continue;
      if (!sameAnswer(packet, state.packet)) {
        li('other-explanations', packet.query + ' — ' + explanation.agent.name + ' — Ask again', () => {
          $('question').value = packet.query;
          $('question').focus();
          ask({query: packet.query});
        });
        $('other-explanations-section').hidden = false;
        continue;
      }
      const article = element($('explanation-list'), 'article', '');
      element(article, 'h4', 'Agent explanation — ' + explanation.agent.name);
      element(article, 'p', 'Model: ' + (explanation.agent.model ?? 'unknown') +
        ' · Input tokens: ' + (explanation.usage.inputTokens ?? 'unknown') +
        ' · Output tokens: ' + (explanation.usage.outputTokens ?? 'unknown'), 'muted');
      for (const paragraph of explanation.paragraphs) {
        if (paragraph.inferred) element(article, 'strong', 'Agent inference', 'inference-label');
        element(article, 'p', paragraph.text); citations(article, paragraph.citations);
      }
      if (explanation.suggestedRelationships.length) {
        element(article, 'h4', 'Suggested (unverified) relationships');
        const list = element(article, 'ul', '');
        for (const relation of explanation.suggestedRelationships) {
          const item = element(list, 'li', relation.from + ' → ' + relation.to + ' (' + relation.type + '): ' + relation.reason);
          citations(item, relation.citations);
        }
      }
      for (const limitation of explanation.limitations) element(article, 'p', 'Agent limitation: ' + limitation, 'muted');
    }
  }

  // ---------------------------------------------------------------- clear / keys
  function clearAll() { resetAnswer(); $('question').focus(); }
  $('clear').addEventListener('click', clearAll);
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !event.defaultPrevented && document.activeElement.tagName !== 'SELECT') clearAll();
  });

  // ---------------------------------------------------------------- import
  $('import-form').addEventListener('submit', async event => {
    event.preventDefault();
    const body = {url: $('repo-url').value.trim()};
    if ($('repo-commit').value.trim()) body.commit = $('repo-commit').value.trim();
    const button = $('import-form').querySelector('button');
    button.disabled = true;
    try {
      let job = await api('POST', '/api/imports', body);
      text('import-status', 'Import queued…');
      while (!['ready', 'failed'].includes(job.state)) {
        await new Promise(r => setTimeout(r, 400));
        job = await api('GET', '/api/imports/' + job.jobId);
        const last = job.events.at(-1);
        text('import-status', 'Importing ' + job.repo + ': ' + (last ? last.stage : job.state) +
          (last && last.files ? ' (' + last.files + ' files)' : '') + '…');
      }
      if (job.state === 'failed') { text('import-status', 'Import failed: ' + job.error + ' — fix the link and try again.'); return; }
      text('import-status', 'Imported ' + job.repo + ' at ' + job.commit.slice(0, 7) + '.');
      $('import-box').open = false;
      await loadProjects(job.projectId);
      $('question').focus();
    } catch (error) {
      text('import-status', 'Import failed: ' + error.message + ' — fix the link and try again.');
    } finally { button.disabled = false; }
  });

  if (session) loadProjects().catch(error => text('project-info', 'Could not load projects: ' + error.message));
})();
