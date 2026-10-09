/* Minimal M2.2 workspace client. Renders untrusted data with textContent only. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
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
  function item(listId, label, onClick) {
    const li = document.createElement('li');
    if (onClick) {
      const b = document.createElement('button');
      b.type = 'button'; b.textContent = label; b.addEventListener('click', onClick);
      li.appendChild(b);
    } else li.textContent = label;
    $(listId).appendChild(li);
    return li;
  }

  let projects = [], current = null, lastRequest = null, counter = 0;
  async function loadProjects(selectId) {
    projects = (await api('GET', '/api/projects')).projects;
    const select = $('project-select');
    select.replaceChildren();
    for (const p of projects) {
      const option = document.createElement('option');
      option.value = p.projectId;
      option.textContent = p.repo + ' @ ' + p.current.commit.slice(0, 7);
      select.appendChild(option);
    }
    if (selectId) select.value = selectId;
    pick();
  }
  function pick() {
    current = projects.find(p => p.projectId === $('project-select').value) || projects[0] || null;
    if (!current) { text('project-info', 'No projects yet. Import a repository above.'); return; }
    const c = current.current.counts || {};
    text('project-info', current.repo + ' at ' + current.current.commit + ' — ' + (c.files || 0) + ' mapped files, ' +
      (c.file_edges || 0) + ' file links, ' + (c.layers || 0) + ' proposed groups' +
      (current.current.extractionState === 'partial' ? ' (partial extraction)' : '') + '.');
  }
  $('project-select').addEventListener('change', pick);

  $('import-form').addEventListener('submit', async event => {
    event.preventDefault();
    const body = {url: $('repo-url').value.trim()};
    if ($('repo-commit').value.trim()) body.commit = $('repo-commit').value.trim();
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
      if (job.state === 'failed') { text('import-status', 'Import failed: ' + job.error); return; }
      text('import-status', 'Imported ' + job.repo + ' at ' + job.commit.slice(0, 7) + '.');
      await loadProjects(job.projectId);
    } catch (error) { text('import-status', 'Import failed: ' + error.message); }
  });

  const STATUS = {
    'matched': 'Found', 'needs-choice': 'Several possible matches — choose one',
    'no-match': 'No match', 'no-path': 'No directed path', 'unsupported': 'Not supported', 'stale': 'Out of date'
  };
  async function ask(extra) {
    if (!current) { text('answer-status', 'Import or select a project first.'); return; }
    const request = Object.assign({snapshotId: current.current.snapshotId, requestId: 'ui-' + (++counter),
      query: $('question').value}, extra || {});
    try {
      const packet = await api('POST', '/api/projects/' + current.projectId + '/query', request);
      lastRequest = request;
      render(packet, Boolean(extra && extra.continuation));
    } catch (error) { text('answer-status', 'Query failed: ' + error.message); }
  }
  function render(packet, append) {
    text('answer-status', (STATUS[packet.status] || packet.status) + ' · ' + packet.operation +
      (packet.highlightState === 'potential-impact' ? ' · potentially affected (not guaranteed to break)' : ''));
    text('answer-reason', packet.reason || '');
    clear('choices');
    $('choices-heading').hidden = !packet.alternatives.length;
    for (const a of packet.alternatives)
      item('choices', (a.path || a.nodeId) + ' — ' + a.reason, () => ask({chosenNodeId: a.nodeId}));
    if (!append) clear('files');
    const witnessFor = new Map(packet.witnesses.map(w => [w.nodeIds[0] === packet.seedNodeId ? w.nodeIds.at(-1) : w.nodeIds[0], w]));
    for (const id of packet.selectedNodeIds) {
      const w = witnessFor.get(id);
      const role = id === packet.seedNodeId ? ' (asked about)' : '';
      item('files', id + role + (w && w.nodeIds.length > 2 ? '  via ' + w.nodeIds.join(' → ') : ''));
    }
    $('files-heading').hidden = !$('files').children.length;
    $('more').hidden = !packet.truncated;
    $('more').onclick = () => ask({query: lastRequest.query, continuation: packet.continuation});
    clear('limitations');
    for (const l of packet.limitations) item('limitations', l);
    $('limitations-box').hidden = !packet.limitations.length;
  }
  $('ask-form').addEventListener('submit', event => { event.preventDefault(); ask(); });

  if (session) loadProjects().catch(error => text('project-info', 'Could not load projects: ' + error.message));
})();
