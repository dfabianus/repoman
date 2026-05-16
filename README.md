# repoman
**Declarative multi-forge Git workspace sync and mirror tooling** — preview-first CLI that
plans and applies local clones and (later) forge-side mirrors from one YAML layout.
Designed for [**Linux, macOS, and Windows**](docs/design/repoman.md). Status and exit codes follow
the vocabulary **`OK`** · **`WOULD UPDATE`** · **`UPDATED`** · **`SKIP`** · **`WARN`** · **`ERROR`**.
## What's implemented today
- **`repoman config path|validate|show`** — resolve config location, validate schema, dump YAML.
- **`repoman doctor`** — tokens and optional API reachability (GitLab/GitHub).
- **`repoman local plan`** / **`repoman local sync`** — namespace discovery with cache, layout
  under `workspace_root`, guarded `fetch` / `merge --ff-only` (writes only with **`--write`**).
- **`repoman local status`** — read-only ahead/behind, dirty, and clone presence; optional **`--json`**.
See the product spec:
- **[`docs/design/repoman.md`](docs/design/repoman.md)** — scope, roadmap, behaviour.
- **`examples/`** — minimal, commented configs and copy-paste commands.
Not yet shipped: `mirrors` subcommands — see roadmap in the design doc.
## Requirements
- **Python ≥ 3.13**
- **Git** on `PATH`
- **[uv](https://docs.astral.sh/uv/)** — used for installs and CI (`AGENTS.md`).
## Install (from source)
```bash
git clone <this-repo-url> repoman && cd repoman
uv sync --all-groups
uv run repoman --version
```
To install into an environment explicitly:
```bash
uv pip install .
repoman --version
```
(Publishing to PyPI is optional per project policy; release artefacts attach to tagged GitHub
Releases.)

## Quick start

1. Copy **[`src/repoman/templates/repoman.yaml.example`](src/repoman/templates/repoman.yaml.example)**
   or start from **[`examples/local-plan/repoman.yaml`](examples/local-plan/repoman.yaml)**.
2. Adjust `paths.workspace_root`, `remotes.*`, then `namespaces:` (or explicit `repos:`).
3. Set token env vars as referenced in `token_env` (or use `credentials.toml` beside `repoman.yaml`;
   POSIX file mode **0600** required).
```bash
# Default config path follows docs/design/repoman.md (override with REPOMAN_HOME / --config)
uv run repoman config validate
uv run repoman doctor                      # probes APIs unless --skip-network
uv run repoman local plan                  # preview; no clones
uv run repoman local status                # read-only; add --json for automation
uv run repoman local sync --write          # clones / fetch / ff-only merges
```
Safety: **`local sync` without `--write` is preview-only**; dirty trees and non-fast-forward states
produce **`SKIP`**, not silent data loss (`docs/design/repoman.md` §8).
## Development
```bash
uv sync --all-groups
uv run ruff check .
uv run ruff format --check .
uv run pytest
```
Contributor rules: **[`AGENTS.md`](AGENTS.md)** (tooling, tests, backlog in **`.adr.md`**, chatlogs under
 **`docs/chatlogs/`**).
## License

Released under the **MIT License** — see [`LICENSE`](LICENSE) in this repository.

