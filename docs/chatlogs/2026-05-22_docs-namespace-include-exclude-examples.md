---
title: Namespace include/exclude examples in docs
topic: docs
date_added: 2026-05-22
tags: [chatlogs]
links:
  - docs/examples.md
  - docs/getting-started.md
  - docs/index.md
  - README.md
  - docs/design/repoman.md
---

## Commit helper

**SemVer / version bump:** **no bump** — documentation and navigation only; no CLI, config schema,
or runtime behaviour changes.

**Tags / GitHub Release:** **None** — merge to the default branch as usual; no new tag or release
artefact required for this slice.

**Suggested commit message:**

```
docs(examples): add namespace include/exclude recipes and cross-links
```

**Copy-paste:**

```bash
git add README.md docs/examples.md docs/getting-started.md docs/index.md \
  docs/chatlogs/2026-05-22_docs-namespace-include-exclude-examples.md
git commit -m 'docs(examples): add namespace include/exclude recipes and cross-links'
git push origin main
```

(Replace `main` with your integration branch.)

## How to try

```bash
uv sync --all-groups
uv run mkdocs build --strict   # may warn on pre-existing chatlog / out-of-docs links
uv run mkdocs serve            # browse Examples → “Namespace include and exclude”
```

Skim **[`docs/examples.md`](../examples.md)** for the new YAML snippets and the link to
[Design §10](../design/repoman.md#10-discovery-filter-include-exclude).

## Session summary

### Goal

Document how **`namespaces[]`** entries use **`include`** and **`exclude`** (glob lists, path
relative to `name`, order vs `visibility` and archived repos), with copy-pastable examples users can
adapt for GitHub (flat slugs) and GitLab (nested paths / `include_subgroups`).

### Shipped

- **`docs/examples.md`** — new section *Namespace include and exclude* with narrative plus seven
  recipes (allowlist, denylist, subgroup `include`, subtree `exclude`, prefix/suffix globs, combined
  app-* pattern, explicit list + subtree); note on `**/*` + exclude-all pitfall; anchor link to
  design doc §10 (`#10-discovery-filter-include-exclude`).
- **`docs/getting-started.md`** — cross-link after the first GitHub namespace example to the new
  Examples section.
- **`README.md`** — documentation table distinguishes **Examples** doc vs **`examples/`** repo
  directory.
- **`docs/index.md`** — quick links updated the same way.

### Follow-ups

- Optional: resolve **`mkdocs build --strict`** warnings from older docs/chatlog links and
  `getting-started.md` → template path so strict CI goes green without noise.
- Consider a short **`examples/`** YAML snippet mirroring one recipe if maintainers want runnable
  parity (not required for this session).
