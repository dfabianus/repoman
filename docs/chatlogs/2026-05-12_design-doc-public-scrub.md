---
title: Sanitize public design doc (repoman.md)
topic: governance
date_added: 2026-05-12
tags: [chatlogs]
links:
  - docs/design/repoman.md
  - .adr.md
---

## Commit helper

**SemVer / version bump:** **None** — documentation and editorial neutralization only; no installable
behaviour change.

**Tags / GitHub Release:** **None** — merge to default branch without a new `v*` tag.

**Suggested commit message:**

```
docs(design): scrub repoman.md for public publication
```

**Copy-paste:**

```bash
git add docs/design/repoman.md .adr.md docs/chatlogs/2026-05-12_design-doc-public-scrub.md
git commit -m 'docs(design): scrub repoman.md for public publication'
```

## How to try

Diff review (no runtime dependency):

```bash
git diff main -- docs/design/repoman.md | head -n 200
rg -n "dnmlr|dfabianus|donabaum|Festo|nexus|vitrum|\\[\\[|==>" docs/design/repoman.md || echo "no banned tokens"
```

Optional: render Markdown locally if you use a preview extension.

## Session summary

### Goal

Make [`docs/design/repoman.md`](docs/design/repoman.md) safe for **public** hosting: no real usernames,
home paths, company names, Obsidian wiki links, or filesystem pointers into other repositories.

### Changes

- **Frontmatter:** replaced Obsidian-centric `Template` / `Context: Private` / wiki `Links` with a small
  public `see_also` URL list (third-party docs only).
- **Examples:** GitLab/GitHub names and CLI samples now use **`acme-org`**, **`example-user`**, and
  `~/repositories` instead of identifiable group slugs or `/home/<person>/…`.
- **§13:** renamed to **„Integration mit anderen Werkzeugen“** — describes subprocess/dependency
  integration **without** naming sibling repos or `.adr.md` paths elsewhere.
- **§14:** removed informal `==>` first-person threads; folded mirror / profile / lock-file guidance
  into neutral bullets; removed employer-specific narrative.
- **§17:** dropped internal wiki and cross-repo file references; kept only public URLs already used
  elsewhere in the ecosystem section.
- **§18 / roadmap checklist:** pilot item uses placeholder `<org>/sandbox-*`; coordination bullet no
  longer names external roadmap tooling.
- **Misc:** replaced `user_rule` pointer with `AGENTS.md`; fixed German phrasing where edits touched
  sentences (`typischem` stack wording).

### Follow-ups

- If the product narrative should be **fully English** under `docs/`, plan a dedicated translation pass
  (large change; out of scope for this scrub).
