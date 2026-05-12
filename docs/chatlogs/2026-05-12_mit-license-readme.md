---
title: MIT LICENSE and README license section
topic: governance
date_added: 2026-05-12
tags: [chatlogs]
links:
  - LICENSE
  - README.md
  - pyproject.toml
  - docs/design/repoman.md
  - .adr.md
---

## Commit helper

**SemVer / version bump:** **None** — legal metadata and prose only (`LICENSE`, README linkage,
[`pyproject.toml`](pyproject.toml) `license = "MIT"`). No behavioural or CLI change; omit a version bump unless
you need a PATCH solely to refresh release artefacts (`metadata only; behavioural surface unchanged`).

**Tags / GitHub Release:** **None** — integrate on the default branch; tag only when packaging a numbered
release per your release train.

**Suggested commit message:**

```
docs(license): add MIT LICENSE and project metadata
```

**Copy-paste:**

```bash
git add LICENSE README.md pyproject.toml docs/design/repoman.md .adr.md \
  docs/chatlogs/2026-05-12_mit-license-readme.md
git commit -m 'docs(license): add MIT LICENSE and project metadata'
```

## How to try

Verify packaging metadata picks up PEP 621 `license`:

```bash
uv sync --all-groups
uv build --sdist --wheel
tar -tzf dist/repoman-*.tar.gz | head -n 40
grep -q "MIT License" LICENSE && echo OK
grep 'license = "MIT"' pyproject.toml
rg -n "MIT License" README.md
```

Read-only spot-check without building:

```bash
head -n 5 LICENSE
```

## Session summary

### Goal

Provide an explicit **MIT** grant for distributors and downstream users (design doc roadmap: MIT-Lizenz
analog vitrum) and align **`README.md`**, **`pyproject.toml`**, backlog, and the German roadmap line so
OSS posture stays consistent without changing runtime behaviour.

### Shipped artefacts

| Item | Detail |
| --- | --- |
| **`LICENSE`** | Standard MIT body text; copyright Fabian Müller, year **2026** (aligned with `[project] authors`). |
| **`pyproject.toml`** | Added PEP 621 `license = "MIT"` for hatch/`uv build` metadata. |
| **`README.md`** | Replaced the provisional license placeholder with a short MIT subsection linking to **`LICENSE`**. |
| **`docs/design/repoman.md` §18** | Publication checklist still **open** for “GitHub veröffentlichen”, wording references the tracked MIT file path. |
| **`.adr.md`** | **`Repository polish`** checkbox completed for the README + license + packaging-metadata slice (public hosting remains backlog). |

### Follow-ups

- When the repo is public: close the checklist item in **`docs/design/repoman.md`**, optionally add
  **`classifiers`** (e.g. `License :: OSI Approved :: MIT License`), and bump / tag alongside the first
  distributable milestone if publishing to PyPI or broad GitHub Releases.
