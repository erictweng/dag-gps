# Local workspace service (M2.2)

A loopback-only local app: paste a public GitHub link, import it, ask questions.
Single user, local prototype. Python's `http.server` is not a production server;
a hosted or shared deployment needs a separate design.

## Run

```sh
python3 -m app.server            # optional: --root DIR --port 8765
```

It prints a private link such as `http://127.0.0.1:8765/#session=...`. Open that
link. The page moves the session key into tab storage and removes it from the
address bar. Without the key, every API call is refused.

## Boundary

- Binds 127.0.0.1 or ::1 only; any other host is rejected at startup.
- `Host` must be this loopback address and port, which blocks DNS rebinding.
  A present `Origin` must be the same origin, and cross-site `Sec-Fetch-Site`
  values are rejected. No CORS headers are sent.
- Every `/api/*` route requires the per-run `X-DAG-GPS-Session` capability,
  compared in constant time. Static UI routes are an exact allowlist of three
  files; there is no directory serving.
- JSON bodies only, at most 64 KiB, with exact field allowlists. Project,
  snapshot and job IDs are opaque and regex-validated, never filesystem paths.
- `Content-Security-Policy` is `default-src 'none'` plus self scripts, styles and
  connections only. The page renders all repository data with `textContent`.
- No request logging, so tokens and paths stay out of logs.

## API

- `POST /api/imports {url, commit?}` → 202 job. URLs are validated before any job.
- `GET /api/imports/{jobId}`: state `queued|running|ready|failed` with stage
  events (`inventory-ready` precedes `ready`) and a bounded error message.
- `GET /api/projects`: projects with the current revision and counts.
- `GET /api/projects/{projectId}/snapshots/{snapshotId}`: the immutable envelope.
- `POST /api/projects/{projectId}/query {snapshotId, requestId, query, continuation?, chosenNodeId?}`
  returns a `dag-gps-evidence/v1` packet. The snapshot must belong to the project.

Imports run one at a time, with at most 4 queued. Revisions live under
`ROOT/projects/<projectId>/commits/<commit>/` and are never mutated in place.

## Query worker (`app/query_worker.py`)

One persistent Node process per snapshot (at most 4, least recently used
evicted) runs `scripts/query_worker.cjs` with no shell, a minimal environment and
its own process group. Requests are serial. Each reply must echo the request ID
and pass `validate_evidence_packet` against the snapshot the manager holds, so a
worker cannot return another project or revision. Replies over 2 MiB, timeouts
(10 s default) and crashes kill the process; the next request restarts it.
stderr is kept separately, bounded to 16 KiB. At most 8 requests wait at once.

## Not yet

The graph view and three-panel UI are documented in `docs/WORKSPACE_UI.md`. Source/context fetch is M3. There
is no live refresh (M4) and no persistent job history across restarts.

## Verify

```sh
python3 -m unittest discover -s tests -p test_workspace_server.py -v
python3 -m unittest discover -s tests -p test_query_worker.py -v
node scripts/smoke_workspace_server.cjs "$PRIVATE_URL" https://github.com/OWNER/REPO COMMIT SHOTS_DIR REPORT.json
```
