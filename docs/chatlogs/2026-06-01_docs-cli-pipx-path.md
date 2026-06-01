---
title: Docs assume repoman on PATH; pipx install; credentials chmod
topic: docs
date_added: 2026-06-01
tags: [chatlogs]
links:
  - docs/getting-started.md
  - docs/index.md
  - README.md
  - docs/examples.md
  - docs/commands/config.md
  - docs/commands/doctor.md
  - docs/commands/local.md
  - docs/design/repoman.md
  - examples/local-plan/README.md
  - examples/local-plan/repoman.yaml
  - src/repoman/cli.py
---

## Commit helper

**SemVer / version bump:** **no bump** — user-facing documentation and CLI help text only; no
packaged behaviour or schema changes.

**Tags / GitHub Release:** **None** — merge to the default branch as usual.

**Suggested commit message:**

```
docs: assume repoman on PATH; pipx install; document credentials chmod
```

**Copy-paste:**

```bash
git add README.md docs/getting-started.md docs/index.md docs/examples.md \
  docs/commands/config.md docs/commands/doctor.md docs/commands/local.md \
  docs/design/repoman.md examples/local-plan/README.md examples/local-plan/repoman.yaml \
  src/repoman/cli.py docs/chatlogs/2026-06-01_docs-cli-pipx-path.md
git commit -m 'docs: assume repoman on PATH; pipx install; document credentials chmod'
git push origin main
```

(Replace `main` with your integration branch.)

## How to try

```bash
uv sync --all-groups
uv run mkdocs build --strict
```

Skim **[`docs/getting-started.md`](../getting-started.md)** for `pipx install repoman-cli`, the
`chmod 600` example for `credentials.toml`, and `repoman …` command blocks.

## Session summary

### Goal

Align published documentation with PyPI installs: prefer **`repoman …`** over **`uv run repoman …`**
where the CLI is expected on `PATH`, surface **`pipx install repoman-cli`** (PyPI name remains
**`repoman-cli`**), document **`chmod 600`** for `credentials.toml` on POSIX, and keep **`uv run repoman`**
only for clone-only development snippets.

### Shipped

- **`docs/getting-started.md`** — intro, install block, all user command examples, `chmod` for
  default `~/.config/repoman/credentials.toml` with note for `REPOMAN_HOME` / custom `--config`.
- **`docs/index.md`**, **`README.md`** — PyPI install shows `pipx`; examples use `repoman`.
- **`docs/commands/*.md`**, **`docs/examples.md`** — command samples use `repoman`.
- **`docs/design/repoman.md`** — Phase 0 acceptance cell uses `repoman --version`.
- **`examples/local-plan/`** — README and YAML comment updated for consistency.
- **`src/repoman/cli.py`** — missing-config hint lines use `repoman` for parity with docs.

Historical **`docs/chatlogs/**`** entries were left unchanged as archives.

### Follow-ups

- None required; optional future pass could refresh older chatlog snippets if maintainers want
  historical copies to match current CLI ergonomics.
