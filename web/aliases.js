/* Explicit user data only. Never execute imported strings. */
(function(root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.DagGpsAliases = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function() {
  'use strict';
  const VERSION = 1, MAX_BYTES = 262144, MAX_ENTRIES = 1000;
  function normalize(text) { return text.trim().toLowerCase().replace(/\s+/g, ' '); }
  function entry(value) {
    if (!value || typeof value !== 'object' || Array.isArray(value) ||
        Object.keys(value).sort().join(',') !== 'alias,nodeId' ||
        typeof value.alias !== 'string' || value.alias !== value.alias.trim() ||
        value.alias.length > 160 || !normalize(value.alias) ||
        /[\u0000-\u001f\u007f-\u009f\ud800-\udfff]/u.test(value.alias) ||
        typeof value.nodeId !== 'string' || !value.nodeId || value.nodeId.length > 1024 ||
        /[\u0000-\u001f\u007f]/.test(value.nodeId)) throw new Error('Invalid alias entry (1–160 characters, no control characters)');
    return {alias: value.alias, nodeId: value.nodeId};
  }
  function unique(entries) {
    if (entries.length > MAX_ENTRIES) throw new Error('Too many aliases');
    const seen = new Set();
    return entries.map(entry).filter(e => {
      const key = JSON.stringify([normalize(e.alias), e.nodeId]);
      if (seen.has(key)) return false;
      seen.add(key); return true;
    });
  }
  function validate(text, repo) {
    if (typeof text !== 'string' || new TextEncoder().encode(text).length > MAX_BYTES) throw new Error('Alias file too large');
    const data = JSON.parse(text);
    if (!data || Object.keys(data).sort().join(',') !== 'aliases,repo,version' ||
        data.version !== VERSION || data.repo !== repo || !Array.isArray(data.aliases))
      throw new Error('Wrong alias schema, repository or version');
    return unique(data.aliases);
  }
  function createStore(map, storage) {
    const repo = map.meta.repo, key = 'dag-gps:aliases:v1:' + encodeURIComponent(repo);
    const ids = new Set(map.nodes.map(n => n.id));
    let entries = [], status = 'No aliases saved.', error = '';
    try { const text = storage.getItem(key); if (text !== null) {
      entries = validate(text, repo);
      status = 'Loaded ' + entries.length + ' saved aliases (best-effort file storage).';
    } }
    catch (e) { error = 'Storage unavailable or invalid: ' + e.message; status = error; }
    function serialize(list = entries) { return JSON.stringify({version: VERSION, repo, aliases: list}, null, 2); }
    function snapshot() {
      return {entries: entries.map(e => ({...e, orphan: !ids.has(e.nodeId), conflict:
        entries.some(other => normalize(other.alias) === normalize(e.alias) && other.nodeId !== e.nodeId)})),
        status, error, key};
    }
    function apply(list) {
      const next = unique(list); const text = serialize(next);
      if (new TextEncoder().encode(text).length > MAX_BYTES) throw new Error('Alias file too large');
      entries = next;
      try { storage.setItem(key, text); if (storage.getItem(key) !== text) throw new Error('Read-back mismatch');
        error = ''; status = 'Saved locally (best-effort file storage).'; }
      catch (e) { error = e.message; status = 'Unsaved — active this session only: ' + e.message; }
      return snapshot();
    }
    return {snapshot, serialize, overlay: () => entries.filter(e => ids.has(e.nodeId)).map(e => ({...e})),
      add(alias, nodeId) { if (!ids.has(nodeId)) throw new Error('Unknown target'); return apply(entries.concat(entry({alias, nodeId}))); },
      remove(alias, nodeId) { return apply(entries.filter(e => !(normalize(e.alias) === normalize(alias) && e.nodeId === nodeId))); },
      clear: () => apply([]),
      preview(text, mode = 'merge') {
        if (!['merge', 'replace'].includes(mode)) throw new Error('Choose merge or replace');
        const imported = validate(text, repo);
        const next = unique((mode === 'merge' ? entries : []).concat(imported));
        // Validate the entire prospective result before confirmation/application.
        validate(serialize(next), repo);
        return {entries: next, imported: imported.length, orphans: next.filter(e => !ids.has(e.nodeId)).length,
          conflicts: next.filter(e => next.some(o => normalize(o.alias) === normalize(e.alias) && o.nodeId !== e.nodeId)).length, mode};
      },
      commit(preview) { return apply(validate(serialize(preview.entries), repo)); }
    };
  }
  return {normalize, entry, unique, validate, createStore, VERSION, MAX_BYTES, MAX_ENTRIES};
});
