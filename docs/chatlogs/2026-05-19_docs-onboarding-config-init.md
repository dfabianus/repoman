---
title: MkDocs scaffold and config onboarding commands
topic: feature
date_added: 2026-05-19
tags: [chatlogs]
links:
  - README.md
  - docs/getting-started.md
  - mkdocs.yml
  - src/repoman/cli.py
  - src/repoman/config_setup.py
  - src/repoman/paths.py
  - .adr.md
  - AGENTS.md
---

## Commit helper

**SemVer / version bump:** **MINOR** → **`0.4.0`** — new user-visible CLI (`config init`, `config set`);
MkDocs site and README/getting-started as onboarding entry points; `REPOMAN_HOME` honored on Windows.

**Tags / GitHub Release:** **Tag after bump** — push annotated **`v0.4.0`** once the release merge is on
`main` to trigger [`.github/workflows/release.yml`](.github/workflows/release.yml).

**Important — commit before tag**

1. **`git commit`** everything on the integration branch (`pyproject.toml` + `src/repoman/__init__.py`
   bumped to `0.4.0` in the **same commit** as the feature).
2. **`git push origin <branch>`** so remote has that commit.
3. **`git tag -a v0.4.0 -m 'v0.4.0'`** on **that pushed commit**.
4. **`git push origin v0.4.0`**.

Creating or pushing **only** a tag without merging the committing branch first publishes a dangling
tag and does **not** ship code to collaborators.

Optional one-liner after (2)-(3): `git push origin <branch> --follow-tags`.

**Suggested commit message:**

```
feat(config): add init/set commands, MkDocs site, and getting-started guide
```

**Copy-paste:**

```bash
git add .adr.md .github/workflows/ci.yml README.md mkdocs.yml pyproject.toml uv.lock \
  docs/ src/repoman/__init__.py src/repoman/cli.py src/repoman/config_setup.py \
  src/repoman/paths.py src/repoman/templates/repoman.yaml.example \
  tests/unit/test_config_setup.py tests/unit/test_secrets_precedence.py \
  tests/integration/test_cli_smoke.py examples/README.md \
  docs/chatlogs/2026-05-19_docs-onboarding-config-init.md
git commit -m 'feat(config): add init/set commands, MkDocs site, and getting-started guide'
git push origin main
git tag -a v0.4.0 -m 'v0.4.0'
git push origin v0.4.0
```

(Replace `main` with your integration branch.)

## How to try

```bash
uv sync --all-groups
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run mkdocs build --strict
uv run mkdocs serve

uv run repoman config init --config /tmp/repoman-test/repoman.yaml
uv run repoman config set paths.workspace_root '~/repositories' --config /tmp/repoman-test/repoman.yaml
uv run repoman config set paths.workspace_root '~/repositories' --write --config /tmp/repoman-test/repoman.yaml
uv run repoman config validate --config /tmp/repoman-test/repoman.yaml
```

## Session summary

### Goal

After a successful real-world Windows setup, improve onboarding: README as entry point, MkDocs
architecture, cross-platform getting-started, and CLI helpers to create and edit configuration.

### Shipped

- **`repoman config init`** — writes bundled template to default or `--config` path; `--force` overwrite;
  prints next steps (`credentials.toml`, `validate`, `doctor`).
- **`repoman config set KEY VALUE`** — dotted keys, YAML-coerced values, `--unset`, preview vs `--write`.
- **`REPOMAN_HOME`** — respected on Windows (aligned with Linux/macOS).
- **MkDocs** — `mkdocs.yml`, Material theme, `getting-started.md`, command pages, CI `mkdocs build --strict`.
- **README** — table-driven first-time setup linking to getting-started.
- **Version `0.4.0`**.

### Follow-ups

- Interactive **config init wizard** (`.adr.md` open task).
- `config set` append/list helpers for `namespaces` entries.
- Publish docs site (GitHub Pages) when repo is public.
