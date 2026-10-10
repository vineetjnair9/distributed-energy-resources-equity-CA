# Setup, deployment, and operations

## Local development

Prerequisites: Python 3.11 and Node 22 or newer. Docker is optional.

```bash
python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m backend.fixtures.build_fixture_db          # data/der_fixture.db
DER_DB_PATH=data/der_fixture.db .venv/bin/uvicorn backend.api.api:app --reload
npm --prefix frontend ci && npm --prefix frontend run dev       # http://localhost:5173
```

Vite proxies `/api` to uvicorn on port 8000. To serve everything from one port as in
production, run `npm --prefix frontend run build`; FastAPI then serves
`frontend/dist` at `/`.

### Tests

```bash
.venv/bin/python -m pytest -q -rs            # schema, API, grounding, regression, deploy
npm --prefix frontend test                   # UI unit and integration tests
python scripts/export_openapi.py --check     # API contract file is current
python scripts/smoke_check.py http://127.0.0.1:8000   # against any running server
```

On a clean clone the three release-data tests skip, with a reason, because
`data/processed/` is generated. Everything else runs against the fixture.

## Environment variables

| Variable | Used by | Default | Purpose |
| --- | --- | --- | --- |
| `DER_DB_PATH` | API, builders, generator | `data/der_tool.db` | Database file |
| `DER_DB_URL` | `backend/serve.py` | unset | https URL of a built database (`.db` or `.db.gz`) to fetch at container start; capped at 4 GB |
| `DER_DB_SHA256` | `backend/serve.py` | unset | Expected checksum of that download; set it, or the origin is unverified |
| `PORT` | `backend/serve.py` | `8000` | Bind port (Render sets it) |
| `DER_FRONTEND_DIST` | API | `frontend/dist` | Built frontend to serve |
| `OPENAI_API_KEY` | summary generator only | unset | Offline summary generation; the server never needs it |
| `DER_SUMMARY_MODEL` | summary generator only | `gpt-5.6-luna` | LLM for generation |
| `CENSUS_API_KEY` | data pipeline only | unset | ACS pull |

## Building the real database

```bash
python scripts/fetch_exact_public_data.py
python scripts/run_all.py --only data models database      # add --replace-database to rebuild
python backend/schemas/generate_summaries.py --all          # optional, needs OPENAI_API_KEY
```

The builder stages a new file, validates it (`integrity_check`, foreign keys,
required tables and columns, non-empty core tables), archives any existing database,
and then swaps the new one in atomically. A failed build leaves the live database
untouched.

## Deployment (Render)

The deploy path: push → GitHub Actions (Python tests, OpenAPI check, frontend
types/tests/build, Docker build, container smoke check) → Render builds the
`Dockerfile` → health check on `/health` → smoke check.

1. In Render, choose **New → Blueprint** and select this repository. `render.yaml`
   defines one free Docker web service, `ca-der-explorer`.
   `autoDeployTrigger: checksPass` makes Render wait for CI to pass.
2. Without `DER_DB_URL`, the service serves the bundled synthetic fixture, and the
   UI shows a "Synthetic demo data" banner.
3. To serve real data, upload a built database. A GitHub Release asset works; the
   file is about 740 MB (70 MB gzipped), too large to commit. The current build is the `db-2026-10` release.

   ```bash
   gzip -k data/der_tool.db && shasum -a 256 data/der_tool.db.gz
   gh release create db-2026-10 data/der_tool.db.gz
   ```

   Then set `DER_DB_URL` to the asset's download URL and `DER_DB_SHA256` to the
   checksum, and redeploy. The download is checksum-verified and fully validated
   before it replaces the fixture; on any failure the service keeps the fixture and
   logs why.
4. After each deploy: `python scripts/smoke_check.py https://<service>.onrender.com --retries 20`.

The image has three stages: the Node build runs the UI tests, the Python stage
builds the fixture with pandas, and the slim runtime has no pandas and runs as a
non-root user. A container `HEALTHCHECK` polls `/health`.

## Known failure modes

| Symptom | Cause | Fix |
| --- | --- | --- |
| `/health` returns 503 `not_ready`; UI shows a red banner | Database missing, empty, or schema mismatch | Run the `setup_command` from the health response, or build the fixture |
| Every API route returns 503 | Same as above; the server never creates a database | Same |
| Summary panel says "No stored summary" | Summaries not generated for that region or category | Run `generate_summaries.py` for the region; the UI shows the evidence meanwhile |
| Summary withheld as "cites no evidence" or "another region" | A summary row was edited or evidence was rebuilt without regenerating summaries | Regenerate summaries (`--replace-existing`) |
| Region page has no model outputs | ZCTA not in the fitted sample (no ACS data) | Expected; the UI says so |
| Values look implausible (for example, burden over 100%) | Unit mismatch between pipeline output and `METRIC_COLUMNS` | Shares must be stored as 0–1 |
| First request after idle is slow | Render's free tier spins down | Upgrade the plan, or use `--retries` in smoke checks |
| `DER_DB_URL` set but data is still synthetic | Download failed checksum or validation | Check the service logs for `Could not fetch DER_DB_URL` |
| Build lock error when rebuilding | A previous build was interrupted | Confirm no build is running, then delete `data/.der_tool.db.build.lock` |
| Map tiles missing | Browser blocks OpenStreetMap tiles | The boundary still loads; tiles are cosmetic |
