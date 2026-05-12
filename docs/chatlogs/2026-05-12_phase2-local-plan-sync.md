---
title: Phase 2 local plan and sync
topic: feature
date_added: 2026-05-12
tags: [chatlogs]
links:
  - docs/design/repoman.md
  - .adr.md
  - AGENTS.md
  - examples/README.md
  - src/repoman/local/runner.py
  - src/repoman/cli.py
---

## Commit helper

**SemVer / version bump:** **MINOR** — new user-visible CLI (`repoman local plan`, `repoman local sync`)
and behaviour; backwards-compatible with existing `config` / `doctor` usage.


**Tags / GitHub Release:** **Tag after bump** — push annotated **`v0.2.0`** once the release merge is on `main`
to trigger [`.github/workflows/release.yml`](.github/workflows/release.yml).

**Important — commit before tag**

1. **`git commit`** everything on the integration branch (`pyproject.toml` + `src/repoman/__init__.py` bumped to `0.2.0` in the **same commit** as the feature).
2. **`git push origin <branch>`** so remote has that commit.
3. **`git tag -a v0.2.0 -m 'v0.2.0'`** on **that pushed commit**.
4. **`git push origin v0.2.0`**.

Creating or pushing **only** a tag without merging the committing branch first publishes a dangling tag and does **not** ship code to collaborators.

Optional one-liner after (2)-(3): `git push origin <branch> --follow-tags`.

**Suggested commit message:**

```
feat(local): add plan/sync with discovery cache and forge listings
```

**Copy-paste (Phase‑2 behaviour slice — adjust paths when squashing histories):**

```bash
git add .adr.md docs/design/repoman.md docs/chatlogs/2026-05-12_phase2-local-plan-sync.md \
  pyproject.toml src/repoman/__init__.py src/repoman/cache.py src/repoman/cli.py \
  src/repoman/local/ src/repoman/remotes/catalog.py src/repoman/remotes/clone_urls.py \
  src/repoman/remotes/discovery.py src/repoman/remotes/github_client.py \
  src/repoman/remotes/gitlab_client.py src/repoman/remotes/url_normalize.py tests/
git commit -m 'feat(local): add plan/sync with discovery cache and forge listings'
git push origin main
git tag -a v0.2.0 -m 'v0.2.0'
git push origin v0.2.0
```

(Replace `main` with your integration branch; later **`docs(chatlogs)`** commits may refresh this file with `examples/` / `AGENTS.md` layering without redoing semver.)

## How to try

From repository root:

```bash
uv sync --all-groups
uv run pytest
uv run repoman config validate --config examples/local-plan/repoman.yaml
uv run repoman local plan --config examples/local-plan/repoman.yaml
uv run pytest tests/integration/test_local_smoke.py tests/unit/test_planner_local.py -q
```

To probe a real forge, **copy** `examples/local-plan/repoman.yaml` outside Git, plug in valid `namespaces:` + `$REPOMAN_*` tokens from your shell, keep `repos: []` until you explicitly need explicit entries (`docs/design/repoman.md` §8).

## Session summary — what shipped

### Goal

Implement **Roadmap Phase 2** primitives: declarative namespaces with GitLab/GitHub listing,
filters & cache TTL, deterministic layout for discovered repos, **`local plan`** preview and
**`local sync`** with guarded pull semantics.

### Shipped CLI

- **`repoman local plan`** — dry listing + per-repo intents (`WOULD UPDATE`, `SKIP`, …); no clones by default.
- **`repoman local sync [--write|--strategy|--namespace|--parallel|--refresh-discovery|--changes-only]`**
  mirrors the same orchestration path with optional mutations.

### Key modules added or extended

- **`repoman/remotes/catalog.py`** — `ListedProject` cache-friendly DTO + JSON helpers.
- **`repoman/remotes/discovery.py`** — Pure glob + visibility helpers; sentinel handling so default `**/*` matches single-segment repo names (`ok` vs `team/ok`).
- **`repoman/cache.py`** + runner wiring — deterministic JSON cache files under `${cache_root}/discovery/`.
- **`repoman/remotes/{gitlab_client,github_client}.py`** — paginated-ish listings using python-gitlab / PyGithub respectively.
- **`repoman/remotes/clone_urls.py`**, **`clone_url.py`**, **`url_normalize.py`** — HTTPS token injection helpers + drift comparisons.
- **`repoman/local/{runner,planner,status_probe,git_ops}.py`** — parallel execution for git steps, SKIP policy for dirty / detached / divergence / `.gitmodules`, WARN on origin drift without auto-fix yet.

### Behaviour notes for reviewers / operators

- **Explicit `repos[]`:** `local` path is honoured verbatim under `workspace_root` per design; discovered repos use rendered `layout`.
- **`CI=true`:** discovery TTL forced to "always refresh" (`_cache_needs_refresh` honours zero TTL aggressively).
- **Parallelism:** only per-repo subprocess work scales; forge discovery executes sequentially to simplify cache coherence.
- **Exit codes unchanged:** nonzero when any emitted line is `ERROR`.

### Governance follow-up (later session)

Contributor guide now documents **slice workflow**, mandatory **`## How to try`** in chatlogs after the Commit helper, and runnable **`examples/`** — see **`AGENTS.md`** and companion chatlog **`2026-05-12_agents-chatlogs-examples.md`** if adjusting policy again.

### Follow-ups (product)

- `local status`, `--json` (Phase 3).
- Automated integration tests hitting bare clones + mocked HTTP transports.
- Optional `--fix-remotes` replacing WARN-only drift handling.
