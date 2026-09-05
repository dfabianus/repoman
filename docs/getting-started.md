# Getting started

This guide works on **Linux, macOS, and Windows**. Command examples assume the **`repoman`** CLI is on your
`PATH` (for example after installing from PyPI). When working from a repository clone without a global install,
use **`uv run repoman …`** from the project root after **`uv sync --all-groups`** (see **Prerequisites (clone / development)** below).

## 1. Install

### Install the CLI (PyPI)

```bash
pipx install repoman-cli
# or: pip install repoman-cli
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
repoman config path
```

## 3. Create your first config

=== "Recommended (CLI)"

    ```bash
    repoman config init
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

Tokens never belong in `repoman.yaml`. Choose one approach per remote.
Precedence when several are set: `--token` > `token_env` > `token_command` >
`token_credentials`.

### Environment variables

Set the variable named in `remotes.<name>.token_env`:

```bash
export REPOMAN_GITHUB_TOKEN="ghp_..."   # Linux/macOS
```

```powershell
$env:REPOMAN_GITHUB_TOKEN = "ghp_..."   # Windows (current session)
```

### Forge CLI command (no token on disk)

If you already log in with a forge CLI, let repoman ask it for the token at
run time. `token_command` is an argv list executed without a shell; the
trimmed standard output is the token:

```yaml
remotes:
  github:
    kind: github
    base_url: "https://api.github.com"
    token_command: ["gh", "auth", "token"]
    clone_protocol: ssh
```

Nothing secret is written to disk by repoman, and a machine that can already
run `gh` needs no extra setup. A command that fails, times out (15 s), or
prints nothing is reported as `ERROR` for that remote rather than silently
falling back to a stale file. For GitLab use `["glab", "auth", "token"]`.

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

Use the real path next to your `repoman.yaml` (default layout shown):

```bash
chmod 600 ~/.config/repoman/credentials.toml
```

If you use **`REPOMAN_HOME`** or a custom **`--config`** path, apply `chmod` to that directory’s `credentials.toml` instead.

## 5. Validate and diagnose

```bash
repoman config validate
repoman config show --resolved
repoman doctor
repoman doctor --skip-network   # token resolution only
```

## 6. Preview, then sync

Always preview first:

```bash
repoman local plan
repoman local plan --refresh-discovery
repoman local status
repoman local status --json
```

Apply changes only when the plan looks correct:

```bash
repoman local sync --write
```

**Safety:** without `--write`, `local sync` does not clone or merge. Dirty worktrees and non-fast-forward
states produce **`SKIP`**, not silent data loss.

## 7. Adjust config without an editor

Preview a change:

```bash
repoman config set paths.workspace_root '~/repositories'
```

Apply it:

```bash
repoman config set paths.workspace_root '~/repositories' --write
```

Remove a key:

```bash
repoman config set settings.changes_only --unset --write
```

Keys use **dot notation**; numeric segments address list items (`namespaces.0.name`).

Values are parsed as YAML scalars (`true`, `4`, `["a","b"]`) or plain strings.

## 8. Safe dry run in the repository

Before touching live forges, use the bundled example (no discovery):

```bash
repoman config validate --config examples/local-plan/repoman.yaml
repoman local plan --config examples/local-plan/repoman.yaml
```

See [Examples](examples.md).

## Next steps

- [Command reference](commands/index.md)
- [Design specification](design/repoman.md) — full schema and roadmap
- Future: interactive **`config init`** wizard (tracked in the design doc)
