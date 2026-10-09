# Deploy DealCompass to Railway

Deployment preparation, 10 October 2026. This document does **not** mean that
the app is already online. See `docs/handoffs/MAIN.md` for actual verification.

## Architecture

One Railway service builds the React frontend and runs FastAPI. The browser uses
one HTTPS origin for `/`, `/assets/*`, and `/api/*`; there is no Vite server or
separate frontend host in production. `/health` is public for Railway probes.
All other routes, including API documentation, require the demo login.

- `Dockerfile`: Node 24 build stage, Python 3.12 runtime; explicit file copies.
- `.dockerignore`: allowlist excludes local secrets, databases and dependencies.
- `railway.json`: Docker build, healthcheck, bounded failure restarts.
- `backend/deployment.py`: built UI + API, authentication, one Uvicorn worker.
- Persistent volume `/data`: existing team usage ledger and analysis cache.

Use **one service instance, one region, one worker**. All teammates use this backend
after cutover. No second live deployment, separate laptop counter, or live PR
environment. Rules-only previews are fine. The current hybrid cache/single-flight
design is intended for a single process. The ledger remains the spending guard.

## 1. Connect Railway and prepare a rules-only deployment

1. Sign in to Railway and select the intended workspace. Review and approve the
   hosting plan/spending limit before provisioning paid resources. Do not assume
   this is free; TypeSafe's 100M input-token ceiling is separate from hosting cost.
2. Create a project/service from `feboyfierlyan/dealcompass` using the **reviewed
   commit containing this setup and the latest UI changes**. Preparation is currently
   on `integrator/english-graph-runtime`; do not select an old `main` by accident.
   Root directory is the repository root. Railway detects `Dockerfile`.
3. Attach a volume to this service at `/data`. Keep one replica and one region.
   Do not enable PR deployments with the live key or clone live variables into previews.
4. Set Railway Variables:

   ```text
   DEALCOMPASS_ENGINE_MODE=rules
   DEALCOMPASS_DEMO_USER=team
   DEALCOMPASS_DEMO_PASSWORD=<unique random password, at least 16 characters>
   TYPESAFE_USAGE_DB=/data/typesafe-usage.sqlite3
   DEALCOMPASS_ANALYSIS_CACHE_DB=/data/analysis-cache.sqlite3
   TYPESAFE_BASE_URL=https://api.typesafe.ai/v1
   TYPESAFE_MODEL=jev-latest
   TYPESAFE_TIMEOUT_S=20
   DEALCOMPASS_ANALYSIS_BUDGET_S=15
   ```

   Keep `TYPESAFE_API_KEY` unset until cutover. Enter passwords/keys privately in
   Variables; never commit them, put them in browser code, or paste into logs/chat.
   Do not override Railway's `PORT`. No custom build/start command is necessary.
5. Deploy, generate a Railway HTTPS domain, open `/health`, then `/` and enter the
   demo login. Verify all five deals, the evidence panel and graph. Analysis should
   explicitly report rules mode. A 401 without login is expected.

For CLI setup, the official CLI is prepared locally at
`/tmp/dealcompass-railway-cli/node_modules/.bin/railway` (5.64.2 at preparation time).
It is temporary and **not yet authenticated**. Run its `login` command when ready.
An already installed global CLI can instead be used as `railway`.
GitHub deployment is preferable to uploading the entire working folder; it publishes
only the selected committed revision and does not upload `.env` or the local ledger.

## 2. Move the existing usage ledger before enabling Jev

Do this during a brief maintenance window. **Never run `init-budget 0` on the cloud.**
The real ledger already includes earlier paid calls.

1. Stop the existing local live backend and ask teammates to stop all direct TypeSafe
   callers. Keep cloud mode `rules`. Wait for in-flight work to finish gracefully.
2. Read the local ledger summary. Require zero pending/reserved requests and
   `blocked=false`. Unknown receipts must be reconciled; do not delete them.
3. Create a consistent backup using SQLite's backup API. The following code is an
   operator step **after callers have stopped**, not a build/start command:

   ```bash
   python - <<'PY'
   import json, os, sqlite3
   from pathlib import Path
   from backend.integrations.jev_live import load_env_file
   from backend.integrations.usage import UsageLedger
   load_env_file('.env')
   ledger = UsageLedger()
   summary = ledger.summary()
   if summary['blocked'] or summary['reserved_input_tokens']:
       raise SystemExit('Resolve ledger receipts before migration; do not reset.')
   destination = Path('.local/railway-cutover.sqlite3')
   destination.parent.mkdir(parents=True, exist_ok=True)
   fd = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
   os.close(fd)  # Refuse to overwrite an earlier cutover snapshot.
   source = sqlite3.connect(ledger.path.as_uri() + '?mode=ro', uri=True)
   target = sqlite3.connect(destination)
   try:
       source.backup(target)
       assert target.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
   finally:
       target.close()
       source.close()
   assert UsageLedger(destination).summary() == summary
   print(json.dumps(summary, indent=2))  # Counts only; no key or source data.
   PY
   ```

4. Upload this SQLite backup into the attached volume as
   `/data/typesafe-usage.sqlite3`. With the current CLI, `railway volume files`
   provides upload/download operations; volume paths are relative to its root.
   Link and verify the intended project, environment, service and volume first.
   **Inspect the destination first and never overwrite an existing cloud ledger.**
5. Through Railway SSH, inspect the uploaded file and run:

   ```bash
   python -m backend.integrations.jev_live usage
   ```

   Compare every summary field, particularly request count, input/output totals,
   pending/reserved and cap, with the local export. Optionally move a consistent
   cache backup as well; cache migration is not needed for accounting. An empty
   cloud cache means the first eligible analysis makes metered requests again.
6. Only after verification, set `TYPESAFE_API_KEY` privately and change
   `DEALCOMPASS_ENGINE_MODE=jev`. Redeploy. Startup checks the official endpoint,
   explicit persistent paths and the existing unblocked ledger; it makes no paid
   test request and never initializes a new budget.
7. Run **one** intentional smoke analysis. Confirm Rules + Jev, real receipts,
   and an increased ledger total. Reopening the same deal should use the cache.
   Read the usage total before and after a restart to verify persistence.

Keep the former local live backend stopped. If local development is needed, use
`DEALCOMPASS_ENGINE_MODE=rules`. Do not resume the old ledger after cloud use starts.

## Monitoring and rollback

- Read the usage summary via SSH with the command above; SQLite stores each request
  receipt. Input usage across the **team** must remain below 100,000,000. Output
  tokens are also recorded. Missing receipts block subsequent spending.
- Check Railway logs for startup errors and resource metrics for hosting cost.
  Healthchecks validate deployment startup; they are not continuous monitoring.
- Configure volume backups. A redeploy with a volume can cause brief downtime.
- For a provider problem, set cloud mode to `rules` and redeploy; preserve the volume.
- Roll back application code without replacing the ledger with an older backup.
  An old ledger loses charges. Moving execution back to a laptop requires a new
  controlled cutover from the latest cloud ledger.
- Demo Basic Auth is a small-team gate over HTTPS, not individual accounts/RBAC.
  Share its password only with teammates and judges. A public launch needs proper
  user authorization and per-user request controls.

## Verification commands

```bash
npm --prefix frontend run build
python -m unittest tests.test_deployment -v
python -m unittest discover -s tests -v
python scripts/check_handoff.py --all
docker build -t dealcompass:railway .
```

For a local production-server smoke test, export a temporary demo password and
`DEALCOMPASS_ENGINE_MODE=rules`, then run `python -m backend.deployment`. It uses
port 8080 by default and does not load `.env`. Use test credentials locally, real
credentials only via Railway's HTTPS domain.

Official references: [Railway CLI](https://docs.railway.com/cli),
[Config as Code](https://docs.railway.com/config-as-code/reference),
[Volumes](https://docs.railway.com/volumes),
[Healthchecks](https://docs.railway.com/deployments/healthchecks).
