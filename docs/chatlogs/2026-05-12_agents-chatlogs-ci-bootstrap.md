---
title: Agents guidelines, mandatory chatlogs, and CI bootstrap
topic: governance
date_added: 2026-05-12
tags: [chatlogs]
links:
  - AGENTS.md
  - docs/design/repoman.md
---

## Commit helper

**SemVer / release:** No version bump for this change set (documentation and chatlog
convention only). No tag or release.

**Suggested commit message:**

```
docs(chatlogs): require commit helper block at top of session logs
```

**Copy-paste:**

```bash
git add AGENTS.md docs/chatlogs/2026-05-12_agents-chatlogs-ci-bootstrap.md
git commit -m 'docs(chatlogs): require commit helper block at top of session logs'
```

# Session summary: governance and automation baseline

## Goal

Align contributor-facing rules with an open, version-controlled repo: clear agent
guidelines without leaking unrelated project context, **mandatory** session summaries
under `docs/chatlogs/`, and a documented path for documentation, GitHub Actions CI,
semantic versioning, and release artefacts.

## Decisions

1. **`AGENTS.md` is the canonical agent/contributor contract** for this repository.
   It describes intended product behaviour by reference to `docs/design/repoman.md`
   and spells out tooling, testing, security, chatlogs, docs layout, CI/CD, and
   releases—without naming other codebases or employer-specific environments.

2. **Session summaries are required** for substantive work (see `AGENTS.md` § Session
   summaries). They live only under `docs/chatlogs/`, use English, YAML frontmatter,
   and must contain no secrets or customer-specific identifiers.

3. **GitHub Actions** runs on pushes and pull requests to the default branch: `uv
   sync`, `ruff check`, `ruff format --check`, and `pytest`. A separate workflow runs
   when a SemVer tag `vX.Y.Z` is pushed: build sdist/wheel with `uv build`, attach
   artefacts to the GitHub Release, and document PyPI publishing as a future optional
   step (trusted publishing).

4. **Documentation system (target):** MkDocs Material plus API reference via
   mkdocstrings once the docs scaffold exists; until then, design material in
   `docs/design/` remains authoritative and CI does not fail on missing MkDocs config.

5. **Commit helper (follow-up):** Every chatlog must place a **Commit helper**
   section immediately after YAML frontmatter with SemVer/release guidance, a
   suggested message, and copy-paste `git add` / `git commit` commands (see `AGENTS.md`).

## Follow-ups

- Add `mkdocs.yml` and a docs scaffold; extend CI with `mkdocs build --strict`.
- Introduce `.adr.md` when the maintainers want a checkbox backlog in-repo.
- Optionally enable PyPI trusted publishing and align tag ↔ `pyproject.toml` version
  checks in CI.

## Related changes

- New: `docs/chatlogs/` (this file).
- Updated: `AGENTS.md` (governance, docs, CI/CD, versioning, releases, chatlog Commit helper).
- New: `.github/workflows/ci.yml`, `.github/workflows/release.yml`.
