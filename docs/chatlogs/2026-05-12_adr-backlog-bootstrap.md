---
title: Introduce .adr.md living backlog
topic: governance
date_added: 2026-05-12
tags: [chatlogs]
links:
  - .adr.md
  - AGENTS.md
  - docs/design/repoman.md
---

## Commit helper

**SemVer / version bump:** None — governance-only; no user-visible CLI or packaging
change in this batch.

**Tags / GitHub Release:** **None**. Stack on the default branch; no `v*` tag.

**Suggested commit message:**

```
docs(backlog): add .adr.md living task list
```

**Copy-paste:**

```bash
git add .adr.md docs/chatlogs/2026-05-12_adr-backlog-bootstrap.md
git commit -m 'docs(backlog): add .adr.md living task list'
```

## Session summary

### Goal

Align the repo with `AGENTS.md` backlog rules by adding `.adr.md`, and clarify the next
implementation slice after Phase 0–1 (`config` + `doctor`).

### Decisions

1. **`.adr.md`** mirrors the Nexus pattern: English, checkbox tasks only, completed items kept
   inline for history, traceability before non-trivial work.

2. **Next substantive feature commit** should start **Phase 2** (`local plan` /
   `local sync`) per `docs/design/repoman.md` §12—the natural continuation after CI and Phase 1.

3. Smaller orthogonal follow-ups (**MkDocs** + CI `mkdocs build --strict`, **README/license**)
   remain separate checklist items so they do not block core product progress.
