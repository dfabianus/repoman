# repoman

**Declarative multi-forge Git workspace sync** — preview-first CLI that plans and applies local clones
(and later forge-side mirrors) from one YAML file. Works on **Linux, macOS, and Windows**.

| Status | Meaning |
| --- | --- |
| `OK` | No action needed |
| `WOULD UPDATE` | Preview of a planned change |
| `UPDATED` | Change applied |
| `SKIP` | Left unchanged (e.g. dirty tree, non–fast-forward) |
| `WARN` | Informational issue |
| `ERROR` | Failure |

## Documentation

| Resource | Description |
| --- | --- |
| **[Getting started](docs/getting-started.md)** | Install, first config, tokens, first sync (start here) |
| **[Published docs](https://dfabianus.github.io/repoman/)** | MkDocs site (after GitHub Pages is enabled — see [Deployment](docs/deployment/ci-cd.md)) |
| **[Full docs site](docs/index.md)** | MkDocs index — build with `uv run mkdocs serve` |
| **[Design spec](docs/design/repoman.md)** | Architecture, schema, roadmap |
| **[Examples](docs/examples.md)** | Runnable sample commands and namespace `include` / `exclude` recipes |
| **[Examples (repo)](examples/)** | Safe runnable YAML under `examples/` |

## Requirements

- **Python ≥ 3.13**
- **Git** on `PATH`
- **[uv](https://docs.astral.sh/uv/)** — environments and CI

## Install

```bash
git clone <this-repo-url> repoman && cd repoman
uv sync --all-groups
uv run repoman --version
```

Optional: install the CLI into the active environment:

```bash
uv pip install .
repoman --version
```

## First-time setup (5 minutes)

### 1. Create configuration

```bash
uv run repoman config init
uv run repoman config path    # shows where repoman.yaml was created
```

| Platform | Default config directory |
| --- | --- |
| Linux / macOS | `~/.config/repoman/` |
| Windows | `%USERPROFILE%\.repoman\` |

Set **`REPOMAN_HOME`** to use a different directory on any OS, or pass **`--config PATH`** per command.

### 2. Edit `repoman.yaml`

Set `paths.workspace_root`, configure `remotes`, and add at least one `namespaces` entry (or explicit `repos`).
See [getting started](docs/getting-started.md) for a GitHub namespace example and token setup.

### 3. Tokens

Use environment variables (`token_env` in YAML) or **`credentials.toml`** beside `repoman.yaml` with
`token_credentials` — never put tokens in YAML. Details: [Getting started § Tokens](docs/getting-started.md#4-tokens).

### 4. Validate, preview, apply

```bash
uv run repoman config validate
uv run repoman doctor
uv run repoman local plan                  # preview only
uv run repoman local status                # read-only; add --json for automation
uv run repoman local sync --write          # clones / fetch / ff-only merges
```

Adjust settings without an editor:

```bash
uv run repoman config set paths.workspace_root '~/repositories' --write
```

**Safety:** `local sync` without `--write` never mutates clones; dirty trees and non–fast-forward states
produce **`SKIP`**, not silent data loss.

## What's implemented

- **`config`** — `init`, `path`, `validate`, `show`, `set`
- **`doctor`** — tokens and optional API reachability
- **`local plan` / `local sync` / `local status`** — discovery, layout, guarded git operations

Not yet shipped: **`mirrors`** — see [roadmap](docs/design/repoman.md).

## Development

```bash
uv sync --all-groups
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run mkdocs build --strict
uv run mkdocs serve    # local docs at http://127.0.0.1:8000
```

Contributor rules: **[`AGENTS.md`](AGENTS.md)** (backlog in **[`.adr.md`](.adr.md)**, chatlogs under **`docs/chatlogs/`**).

## License

Released under the **MIT License** — see [`LICENSE`](LICENSE).
