---
title: Agent slice workflow plus chatlog and examples conventions
topic: governance
date_added: 2026-05-12
tags: [chatlogs]
links:
  - AGENTS.md
  - docs/chatlogs/2026-05-12_phase2-local-plan-sync.md
  - examples/README.md
  - docs/chatlogs/2026-05-12_adr-backlog-bootstrap.md
---

## Commit helper

**SemVer / version bump:** **None** — policy/docs/chatlog scaffolding only; no behavioural or packaging drift beyond wording already accounted for elsewhere.

**Tags / GitHub Release:** **None** — merge to default branch without a SemVer push.

**Suggested commit message:**

```
docs(agents): document slice workflow and runnable examples layout
```

**Copy-paste:**

```bash
git add AGENTS.md docs/chatlogs/2026-05-12_agents-chatlogs-examples.md \
  docs/chatlogs/2026-05-12_phase2-local-plan-sync.md examples/
git commit -m 'docs(agents): document slice workflow and runnable examples layout'
```

(Add `.adr.md` if touched in same commit.)

## How to try

```bash
grep -n "Recommended slice workflow" AGENTS.md
grep -n "Runnable examples" AGENTS.md
grep -n "How to try" AGENTS.md
sed -n '1,120p' examples/README.md
```

Smoke the sample config that ships beside this governance change:

```bash
uv run repoman local plan --config examples/local-plan/repoman.yaml
```

## Session summary

### Goal

Formalise contributor guidance for (**a**) iterative `.adr`-driven slicing, (**b**) richer
chatlogs with executable verification snippets, (**c**) a checked-in **`examples/`** tree.

### Delivered docs & assets

1. **`AGENTS.md`** now describes the **slice loop** (.adr refresh → implementation → lint/tests →
   chatlog → .adr tidy) and forbids sprawling unrelated diffs unless justified.
2. **Chatlogs** MUST include **`## Commit helper`** first, **`## How to try` second**, then the
   descriptive narrative referencing modules/flags—not a terse one-liner summary for large merges.
3. **`examples/README.md`** + **`examples/local-plan/*`** illustrate how to invoke `repoman`
   without risking real workspace paths; placeholders only.
4. **Versioning** section calls out **`commit → branch push → annotated tag → tag push`** so the
   release automation always sees artefacts built from commits already reachable from `main`.
5. **Retro-updated** the Phase‑2 chatlog template to match these rules and clarified the tagging order.

### Rationale — tag vs commit order (FAQ)

Annotated tags are merely pointers **to commits**. Correct flow is therefore:

1. Create the integrating **commit locally** (`git commit`, already containing `pyproject.toml` bumps when releasing).
2. **Push commits** upstream so collaborators share the SHA.
3. **`git tag -a`** on **that SHA** (typically `HEAD` after the bump commit).
4. **`git push origin vX.Y.Z`**.

Publishing a tag pointing at stale history—or pushing a tag before the commit exists—breaks deterministic releases.

