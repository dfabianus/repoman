---
title: Phase 3 local status and JSON output
topic: feature
date_added: 2026-05-16
tags: [chatlogs]
links:
  - docs/design/repoman.md
  - .adr.md
  - AGENTS.md
  - README.md
  - src/repoman/cli.py
  - src/repoman/local/runner.py
  - src/repoman/local/status_report.py
  - src/repoman/local/status_probe.py
---

## Commit helper

**SemVer / version bump:** **MINOR** — new user-visible CLI (`repoman local status`, `--json`);
backwards-compatible with existing `config`, `doctor`, `local plan`, and `local sync`.

**Tags / GitHub Release:** **Tag after bump** — push annotated **`v0.3.0`** once the release merge is on
`main` to trigger [`.github/workflows/release.yml`](.github/workflows/release.yml).

**Important — commit before tag**

1. **`git commit`** everything on the integration branch (`pyproject.toml` + `src/repoman/__init__.py`
   bumped to `0.3.0` in the **same commit** as the feature).
2. **`git push origin <branch>`** so remote has that commit.
3. **`git tag -a v0.3.0 -m 'v0.3.0'`** on **that pushed commit**.
4. **`git push origin v0.3.0`**.

Creating or pushing **only** a tag without merging the committing branch first publishes a dangling
tag and does **not** ship code to collaborators.

Optional one-liner after (2)-(3): `git push origin <branch> --follow-tags`.

**Suggested commit message:**

```
feat(local): add status command with --json output
```

**Copy-paste:**

```bash
git add .adr.md README.md pyproject.toml src/repoman/__init__.py src/repoman/cli.py \
  src/repoman/local/runner.py src/repoman/local/status_probe.py src/repoman/local/status_report.py \
  tests/integration/test_local_smoke.py tests/integration/test_local_status_git.py \
  tests/unit/test_planner_local.py tests/unit/test_status_report.py \
  docs/chatlogs/2026-05-16_phase3-local-status.md uv.lock
git commit -m 'feat(local): add status command with --json output'
git push origin main
git tag -a v0.3.0 -m 'v0.3.0'
git push origin v0.3.0
```

(Replace `main` with your integration branch.)

## How to try

From repository root:

```bash
uv sync --all-groups
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run repoman local status --config examples/local-plan/repoman.yaml
uv run repoman local status --config examples/local-plan/repoman.yaml --json
uv run pytest tests/unit/test_status_report.py tests/integration/test_local_status_git.py -q
```

With an explicit `repos[]` entry and a local clone, `local status` reports dirty/ahead/behind without
mutating the worktree. Copy `examples/local-plan/repoman.yaml` outside Git and add namespaces when
probing a live forge (same workflow as Phase 2).

## Session summary — what shipped

### Goal

Implement **Roadmap Phase 3**: read-only workspace reporting (`local status`) with machine-readable
**`--json`** output for automation, reusing namespace discovery and on-disk Git probes.

### Shipped CLI

- **`repoman local status`** — ahead/behind, dirty, detached, clone presence, submodule hint, origin
  drift; no fetch/clone/merge.
- Flags aligned with other `local` commands: `--namespace`, `--parallel`, `--refresh-discovery`,
  `--changes-only`, `--config`.
- **`--json`** — top-level document with `schema_version`, `workspace_root`, `prelude`, and
  `repositories[]` (stable field names per repo).

### Key modules

- **`repoman/local/status_report.py`** (pure) — `summarize_local_repo_status`, `RepoStatusSnapshot`,
  JSON serializers. Informational levels: `OK` for “not cloned” / “N commits behind”; `WARN` for dirty,
  diverged, detached, submodules; separate `WARN` line for origin URL drift (same policy as sync).
- **`repoman/local/status_probe.py`** — `last_fetch_epoch` from `FETCH_HEAD` mtime via
  `git rev-parse --git-path`.
- **`repoman/local/runner.py`** — `_prepare_local_workspace()` extracted from plan/sync discovery;
  `run_local_status()` + `LocalStatusResult`; `run_local()` now shares discovery path.
- **`repoman/cli.py`** — `local status` subcommand; JSON via `json.dumps(..., sort_keys=True)`.

### Tests

- **`tests/unit/test_status_report.py`** — pure summarization and JSON shape.
- **`tests/integration/test_local_smoke.py`** — help lists `status`; empty-config `--json` smoke.
- **`tests/integration/test_local_status_git.py`** — real worktree: dirty tree → `WARN` in text and JSON.

### Governance / docs

- **`.adr.md`** — Phase 3 checked; Phase 4+ (`mirrors`) remains open.
- **`README.md`** — documents `local status` and removes it from “not yet shipped”.
- **Version** — `0.3.0` in `pyproject.toml` and `src/repoman/__init__.py`.

### Behaviour notes for reviewers

- **Read-only:** status never calls `git fetch`, `clone`, or `merge`; discovery cache/API listing
  behaviour matches `local plan` / `local sync`.
- **Level vocabulary** differs from sync for some cases (e.g. missing clone is `OK` + “not cloned”,
  not `WOULD UPDATE`; dirty is `WARN`, not `SKIP`) because the command reports state rather than
  planning mutations.
- **Exit codes** unchanged: `1` when any line is `ERROR` (including config/discovery failures in
  prelude).

### Follow-ups (product)

- **Phase 4** — `mirrors plan` / `mirrors sync` (`gitlab_remote_mirror`).
- **`--fix-remotes`**, `--submodules`, `local prune` per design roadmap §12 / §8.
- **MkDocs scaffold** (`.adr.md` open task).
- Optional **`examples/local-status/`** snippet if maintainers want a dedicated runnable example.
