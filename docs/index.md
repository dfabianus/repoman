# repoman

**Declarative multi-forge Git workspace sync** — keep clones under one layout, discover
namespaces on GitLab and GitHub, and (later) manage forge-side mirrors from a single YAML file.

## What works today

| Area | Commands |
| --- | --- |
| Configuration | `config init`, `config path`, `config validate`, `config show`, `config set` |
| Diagnostics | `doctor` |
| Local workspace | `local plan`, `local sync`, `local status` |

Status lines use a fixed vocabulary: **`OK`** · **`WOULD UPDATE`** · **`UPDATED`** · **`SKIP`** ·
**`WARN`** · **`ERROR`**.

Mutating commands are **preview-first**: `local sync` only changes disk with **`--write`**;
`config set` only writes YAML with **`--write`**.

## Quick links

- **[Getting started](getting-started.md)** — install, first config, tokens, first sync
- **[Published docs](https://dfabianus.github.io/repoman/)** — live site (enable GitHub Pages first; see [Deployment](deployment/ci-cd.md))
- **[Command reference](commands/index.md)** — all subcommands
- **[Design specification](design/repoman.md)** — architecture, schema, roadmap
- **[Examples](examples.md)** — runnable sample commands and namespace filter recipes
- **[Examples (repository)](../examples/)** — safe runnable YAML in the repo tree

## Install

```bash
git clone https://github.com/dfabianus/repoman.git
cd repoman
uv sync --all-groups
uv run repoman --version
```

Requirements: **Python ≥ 3.13**, **Git** on `PATH`, **[uv](https://docs.astral.sh/uv/)**.
