/* Loaded only as trusted shipped source inside the template closure. */
var pendingAlias = null, importPreview = null, importText = null;
function aliasRefresh() {
  scorer = DagGpsScorer.createScorer(MAP, aliasStore.overlay());
  var state = aliasStore.snapshot();
  document.getElementById('alias-status').textContent = state.status;
  document.getElementById('alias-list').innerHTML = state.entries.map(function(e, i) {
    var n = NODE.get(e.nodeId);
    return '<p style="overflow-wrap:anywhere">' + esc(e.alias) + ' → ' + esc(e.nodeId) +
      ' · ' + esc(n ? n.kind === 'file' ? layerLabel(n.layer) : 'layer' : 'ORPHAN — not used; no rebinding') +
      (e.conflict ? ' · CONFLICT — requires choice' : '') +
      ' <button type="button" class="btn ghost" data-alias-remove="' + i + '">Remove</button></p>';
  }).join('') || '<p>No learned aliases.</p>';
}
function aliasChanged() {
  aliasRefresh(); pendingAlias = null;
  clearAnswerHighlight(); answer = null; overrides = {}; S.focused = null; applyHighlight(); panelFor();
  document.getElementById('answer').textContent = aliasStore.snapshot().status + ' Ask again to use the updated names.';
}
document.getElementById('answer').addEventListener('input', function() {
  pendingAlias = null;
  var area = document.getElementById('alias-confirmation'); if (area) area.textContent = '';
});
document.getElementById('answer').addEventListener('click', function(ev) {
  var area = document.getElementById('alias-confirmation');
  if (ev.target.closest('[data-override]')) pendingAlias = null;
  if (ev.target.id === 'alias-review') {
    try {
      if (!answer || answer.requestedOperation === 'PATH' || !overrides.locate_target) throw new Error('Choose a valid alternative first');
      DagGpsScorer.validateResult(answer, MAP);
      pendingAlias = DagGpsAliases.entry({alias: document.getElementById('alias-text').value, nodeId: overrides.locate_target});
      var conflict = aliasStore.snapshot().entries.some(function(e) {
        return DagGpsAliases.normalize(e.alias) === DagGpsAliases.normalize(pendingAlias.alias) && e.nodeId !== pendingAlias.nodeId;
      });
      area.innerHTML = '<p>Confirm exact alias <b>' + esc(pendingAlias.alias) + '</b> → <b>' + esc(pendingAlias.nodeId) +
        '</b> · ' + esc(NODE.get(pendingAlias.nodeId).kind === 'file' ? layerLabel(NODE.get(pendingAlias.nodeId).layer) : 'layer') +
        (conflict ? '. Conflict: both bindings will remain; future lookups require your choice.' : '') +
        '</p><button type="button" class="btn" id="alias-confirm">Confirm remember</button><button type="button" class="btn ghost" id="alias-cancel">Cancel</button>';
    } catch(e) { pendingAlias = null; area.textContent = e.message; }
  } else if (ev.target.id === 'alias-confirm' && pendingAlias && answer &&
             answer.requestedOperation !== 'PATH' && overrides.locate_target === pendingAlias.nodeId) {
    try { aliasStore.add(pendingAlias.alias, pendingAlias.nodeId); aliasChanged(); }
    catch(e) { area.textContent = e.message; }
  } else if (ev.target.id === 'alias-cancel') { pendingAlias = null; area.textContent = ''; }
});
document.getElementById('ask-form').addEventListener('submit', function() { pendingAlias = null; });
document.getElementById('alias-list').addEventListener('click', function(ev) {
  var b = ev.target.closest('[data-alias-remove]'); if (!b) return;
  var e = aliasStore.snapshot().entries[Number(b.getAttribute('data-alias-remove'))];
  if (e) { aliasStore.remove(e.alias, e.nodeId); aliasChanged(); }
});
document.getElementById('alias-clear').addEventListener('click', function() {
  if (window.confirm('Clear ALL learned aliases for ' + MAP.meta.repo + '?')) { aliasStore.clear(); aliasChanged(); }
});
document.getElementById('alias-export').addEventListener('click', function() {
  var url = URL.createObjectURL(new Blob([aliasStore.serialize()], {type: 'application/json'}));
  var a = document.createElement('a'); a.href = url; a.download = 'dag-gps-aliases.json'; a.click();
  setTimeout(function() { URL.revokeObjectURL(url); }, 1000);
});
function previewImport() {
  var area = document.getElementById('alias-preview'); importPreview = null;
  if (importText === null) return;
  try {
    importPreview = aliasStore.preview(importText, document.getElementById('alias-mode').value);
    area.innerHTML = '<p>' + esc(importPreview.mode.toUpperCase()) + ': ' + importPreview.imported +
      ' unique imported entries; ' + importPreview.entries.length + ' resulting aliases. ' + importPreview.orphans +
      ' orphan entries quarantined (not used); ' + importPreview.conflicts + ' conflicting bindings require choice.</p>' +
      importPreview.entries.map(function(e) { return '<p style="overflow-wrap:anywhere">' + esc(e.alias) + ' → ' + esc(e.nodeId) + '</p>'; }).join('') +
      '<button class="btn" type="button" id="alias-import-confirm">Confirm ' + esc(importPreview.mode) +
      '</button><button class="btn ghost" type="button" id="alias-import-cancel">Cancel</button>';
  } catch(e) { area.textContent = 'Import rejected; nothing changed: ' + e.message; }
}
document.getElementById('alias-mode').addEventListener('change', previewImport);
var importGeneration = 0;
document.getElementById('alias-import').addEventListener('change', async function(ev) {
  var generation = ++importGeneration; importText = null; importPreview = null;
  var file = ev.target.files[0]; if (!file) return;
  try {
    if (file.size > DagGpsAliases.MAX_BYTES) throw new Error('Alias file too large');
    var text = await file.text(); if (generation !== importGeneration) return;
    importText = text; previewImport();
  } catch(e) { document.getElementById('alias-preview').textContent = 'Import rejected; nothing changed: ' + e.message; }
  ev.target.value = '';
});
document.getElementById('alias-preview').addEventListener('click', function(ev) {
  if (ev.target.id === 'alias-import-confirm' && importPreview) {
    try { // Recompute against current state so an old merge preview cannot silently discard new edits.
      var fresh = aliasStore.preview(importText, importPreview.mode);
      if (JSON.stringify(fresh) !== JSON.stringify(importPreview)) { previewImport(); return; }
      aliasStore.commit(fresh); aliasChanged(); importText = null; importPreview = null;
      document.getElementById('alias-preview').textContent = 'Import applied. ' + fresh.orphans + ' orphan entries quarantined.';
    } catch(e) { document.getElementById('alias-preview').textContent = 'Import rejected; nothing changed: ' + e.message; }
  } else if (ev.target.id === 'alias-import-cancel') {
    importText = null; importPreview = null; document.getElementById('alias-preview').textContent = 'Import cancelled.';
  }
});
aliasRefresh();
