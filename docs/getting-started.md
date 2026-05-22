# Getting started

This guide works on **Linux, macOS, and Windows**. Commands use `uv run repoman …`; omit `uv run`
if the `repoman` CLI is on your `PATH` (for example after `pip install repoman-cli` or `uv pip install .` from a clone).

## 1. Install

### Install the CLI (PyPI)

```bash
pip install repoman-cli
# or: uv pip install repoman-cli
repoman --version
```

The PyPI distribution is **`repoman-cli`**; the command remains **`repoman`**.

### Prerequisites (clone / development)

| Tool | Purpose |
| --- | --- |
| [Python 3.11+](https://www.python.org/) | Runtime |
| [Git](https://git-scm.com/) | Clone, fetch, merge (`git` on `PATH`) |
| [uv](https://docs.astral.sh/uv/) | Environments and lockfile sync |

From a clone of this repository:

```bash
git clone <repo-url> repoman
cd repoman
uv sync --all-groups
uv run repoman --version
```

## 2. Configuration location

| Platform | Default directory | Config file |
| --- | --- | --- |
| Linux / macOS | `~/.config/repoman/` | `repoman.yaml` |
| Windows | `%USERPROFILE%\.repoman\` | `repoman.yaml` |

Override the directory with **`REPOMAN_HOME`** (all platforms), or pass **`--config /path/to/repoman.yaml`**
on every command.

Show the active path:

```bash
uv run repoman config path
```

## 3. Create your first config

=== "Recommended (CLI)"

    ```bash
    uv run repoman config init
    ```

    Creates `repoman.yaml` from the bundled template. Use **`--force`** to overwrite an existing file.

=== "Manual"

    Copy the bundled template from the repository:
    [`src/repoman/templates/repoman.yaml.example`](https://github.com/dfabianus/repoman/blob/main/src/repoman/templates/repoman.yaml.example)
    into the directory from the table above.

Edit the file:

1. **`paths.workspace_root`** — where clones are stored (default `~/repositories` expands to your home).
2. **`remotes`** — GitLab/GitHub base URLs and how tokens are resolved.
3. **`namespaces`** — which groups, orgs, or users to track.

### Example namespace (GitHub)

```yaml
namespaces:
  - remote: github
    name: "<your-github-username>"
    visibility: [public, private]
    include: ["**/*"]
```

For **your own GitHub user**, the token must allow **private repository read** (classic `repo` scope
or equivalent fine-grained access). Otherwise `doctor` may succeed while `local plan` lists only public repos.

More **`include` / `exclude`** patterns (allowlists, subtrees, globs) are in **[Examples → Namespace include and exclude](examples.md#namespace-include-and-exclude)**.

## 4. Tokens

Tokens never belong in `repoman.yaml`. Choose one approach per remote:

### Environment variables

Set the variable named in `remotes.<name>.token_env`:

```bash
export REPOMAN_GITHUB_TOKEN="ghp_..."   # Linux/macOS
```

```powershell
$env:REPOMAN_GITHUB_TOKEN = "ghp_..."   # Windows (current session)
```

### credentials.toml (recommended for daily use)

Create a file **next to** `repoman.yaml`:

```toml
[github]
token = "ghp_..."

[gitlab]
token = "glpat-..."
```

Reference it in YAML:

```yaml
remotes:
  github:
    kind: github
    base_url: "https://api.github.com"
    token_credentials: "github"
    clone_protocol: ssh
```

On Linux/macOS the file must be mode **`0600`** or token resolution fails. On Windows the mode check is skipped.

## 5. Validate and diagnose

```bash
uv run repoman config validate
uv run repoman config show --resolved
uv run repoman doctor
uv run repoman doctor --skip-network   # token resolution only
```

## 6. Preview, then sync

Always preview first:

```bash
uv run repoman local plan
uv run repoman local plan --refresh-discovery
uv run repoman local status
uv run repoman local status --json
```

Apply changes only when the plan looks correct:

```bash
uv run repoman local sync --write
```

**Safety:** without `--write`, `local sync` does not clone or merge. Dirty worktrees and non-fast-forward
states produce **`SKIP`**, not silent data loss.

## 7. Adjust config without an editor

Preview a change:

```bash
uv run repoman config set paths.workspace_root '~/repositories'
```

Apply it:

```bash
uv run repoman config set paths.workspace_root '~/repositories' --write
```

Remove a key:

```bash
uv run repoman config set settings.changes_only --unset --write
```

Keys use **dot notation**; numeric segments address list items (`namespaces.0.name`).

Values are parsed as YAML scalars (`true`, `4`, `["a","b"]`) or plain strings.

## 8. Safe dry run in the repository

Before touching live forges, use the bundled example (no discovery):

```bash
uv run repoman config validate --config examples/local-plan/repoman.yaml
uv run repoman local plan --config examples/local-plan/repoman.yaml
```

See [Examples](examples.md).

## Next steps

- [Command reference](commands/index.md)
- [Design specification](design/repoman.md) — full schema and roadmap
- Future: interactive **`config init`** wizard (tracked in the design doc)
