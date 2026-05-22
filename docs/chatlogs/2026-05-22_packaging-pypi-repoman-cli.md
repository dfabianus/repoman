---
title: PyPI distribution repoman-cli and trusted publishing from release tags
topic: packaging
date_added: 2026-05-22
tags: [chatlogs]
links:
  - pyproject.toml
  - uv.lock
  - .github/workflows/release.yml
  - docs/deployment/ci-cd.md
  - AGENTS.md
  - README.md
  - docs/getting-started.md
  - docs/index.md
  - docs/design/repoman.md
---

## Commit helper

**SemVer / version bump:** **no bump required for this merge** if `project.version` / `__version__`
stay **`0.4.0`** — the change is distribution metadata, Hatch wheel layout, CI, and docs. PyPI will
accept **`repoman-cli==0.4.0`** on first successful upload.

**If `v0.4.0` already exists on GitHub** but was created **before** this workflow landed on the tagged
commit, the tag does **not** automatically re-run. See **“PyPI after an existing tag”** under *Session
summary* below; do **not** blindly bump only to “fix CI” unless you intend a new public release.

**Tags / GitHub Release:** **None** for this documentation/packaging merge alone — stack commits on
`main`. After merge, choose one path to get **PyPI** populated (see session summary). When you next
intend a release, continue the usual **annotated tag `vX.Y.Z`** on the commit that already bumps
`pyproject.toml` + `__init__.py`.

**Suggested commit message:**

```
feat(release): publish repoman-cli to PyPI via trusted publishing
```

**Copy-paste:**

```bash
git add .github/workflows/release.yml AGENTS.md README.md docs/deployment/ci-cd.md \
  docs/design/repoman.md docs/getting-started.md docs/index.md pyproject.toml uv.lock \
  docs/chatlogs/2026-05-22_packaging-pypi-repoman-cli.md
git commit -m 'feat(release): publish repoman-cli to PyPI via trusted publishing'
git push origin main
```

(Replace `main` with your integration branch.)

## How to try

```bash
uv sync --all-groups
uv build
ls dist/   # expect repoman_cli-0.4.0-*.whl and .tar.gz
uv run pytest
```

PyPI upload is exercised only from **GitHub Actions** after a matching tag push (or after aligning
**Trusted publishing** + GitHub **environment `pypi`** — see [`docs/deployment/ci-cd.md`](../deployment/ci-cd.md)).

## Session summary

### Goal

Ship the project on PyPI under the available project name **`repoman-cli`**, keep the **CLI command**
and **Python import** as **`repoman`**, and wire **`release.yml`** to **Trusted publishing (OIDC)**
via **`pypa/gh-action-pypi-publish`**.

### Shipped

- **`pyproject.toml`** — `project.name = repoman-cli`, `readme`, `[project.urls]`,
  `[tool.hatch.build.targets.wheel]` with `packages = ["src/repoman"]` so Hatchling packages the
  `repoman` tree under a hyphenated distribution name.
- **`uv.lock`** — workspace package renamed to `repoman-cli`.
- **`.github/workflows/release.yml`** — `id-token: write`, GitHub **environment `pypi`**, publish
  step to PyPI after build + GitHub Release assets.
- **Docs / `AGENTS.md`** — install instructions (`pip install repoman-cli`), deployment notes
  (trusted publisher must reference workflow **`release.yml`** and environment **`pypi`** unless
  PyPI was configured without an environment — then remove or align the workflow `environment:` block).

### PyPI after an existing **`v0.4.0`** tag on GitHub

GitHub runs **`release.yml` only when the tag pattern matches a push**. Tags are immutable pointers;
**pushing the same tag again** is awkward and may not re-trigger as expected.

Pick **one** of these (best first for a clean story):

1. **Patch release (recommended for tag-driven automation)**  
   Merge this work to `main`, then bump **`0.4.0` → `0.4.1`** in both `pyproject.toml` and
   `src/repoman/__init__.py`, commit, and tag **`v0.4.1`**. The new tag runs the workflow and uploads
   **`repoman-cli==0.4.1`**. Mention in GitHub Release notes that **0.4.1** is packaging/PyPI parity
   if there is no functional delta.

2. **One-off manual upload for `0.4.0`**  
   If you must keep **0.4.0** as the first PyPI version and the GitHub tag already points at a commit
   that includes this `release.yml`, use a **maintainer machine** with PyPI credentials (or a
   one-time API token) and run **`uv publish`** (or `twine`) against `dist/` from `uv build` at that
   commit — only if **`repoman-cli==0.4.0`** is not already on PyPI.

3. **Re-tag only if the tag points at the wrong commit**  
   If **`v0.4.0`** points at a commit **without** the PyPI publish step, you would need a **new commit**
   on `main` anyway; prefer **(1)** with a patch bump instead of rewriting a published tag.

### Follow-ups

- Confirm PyPI **pending publisher** matches **repository**, workflow **`release.yml`**, and
  environment **`pypi`**, and that GitHub **Environments → `pypi`** exists.
- Optional: add **`workflow_dispatch`** to `release.yml` for manual “build + publish” without a new
  tag (policy choice; not required if patch releases are acceptable).
