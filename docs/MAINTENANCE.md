# Restore and maintenance

## Restore the project on another machine

```bash
git clone https://github.com/feboyfierlyan/dealcompass.git
cd dealcompass
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
npm --prefix frontend ci
```

Follow the [README](../README.md#run-locally) to run in rules mode without a key. Dependencies and build artifacts are intentionally reproducible and are not backups.

## What GitHub preserves

The source code, bundled original challenge data/materials, documentation, handoffs, tests and committed evaluation receipts live in Git history. The final README assets and benchmark charts are included. No environment secret, provider key or live usage database belongs in Git.

The repository is public. Do not add private customer uploads or raw private operational backups. Challenge data is fictional; that does not give arbitrary third-party uploads the same publishing permission.

## What must be preserved separately

- The canonical live TypeSafe usage ledger and any unresolved receipts on Railway's `/data` volume.
- Backend environment configuration in the deployment service.
- Any local-only receipts, scripts or working changes before deleting a checkout.

A local retirement recovery archive may contain historical `.local` files and private environment files. Keep it owner-readable only and outside the public repository; do not upload it as a release asset. Treat its ledger as historical. **Never restore an older counter over the current cloud ledger.**

## Retire a local checkout safely

1. Commit intended work, run relevant checks, push the PR and merge it into `main`.
2. Fetch the remote and verify the final commit is reachable from `origin/main`; compare committed file contents.
3. Inspect ignored files, additional worktrees and local branches. Preserve anything unique before deletion.
4. Stop only project-owned development servers. Remove generated dependencies/builds and reviewed project-specific temporary environments.
5. Archive/remove attached managed worktrees before deleting their primary Git directory.
6. Remove the local project folder only after these checks. A compact private recovery archive can retain non-reproducible local state while freeing dependency storage.

Do not clear unrelated caches, all of `/tmp`, or the user's Trash. Deleting a local checkout does not delete the GitHub repository or stop hosted services.

## Cloud operations remain separate

The historical Railway setup followed `integrator/english-graph-runtime`; merging a PR does not automatically change a service's source branch. Check the service's actual source setting before future deployments. Do not delete that remote branch until the service has deliberately moved to `main`.

To retire paid live analysis later, change the existing service to rules mode and preserve its usage ledger. Stopping/deleting hosting, removing a volume and revoking provider credentials are separate operations from local cleanup. Hosting and provider usage may continue while the service remains active.

See [deployment and migration details](DEPLOY_RAILWAY.md). Never create a second live backend with a fresh counter against the same team key.
