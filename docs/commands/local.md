# `repoman local`

Discover repositories from configured namespaces and keep clones under `paths.workspace_root`.

All commands are **preview-first** except where noted.

## `local plan`

Show what `local sync` would do **without** writing to disk.

```bash
uv run repoman local plan
uv run repoman local plan --namespace my-org
uv run repoman local plan --refresh-discovery
uv run repoman local plan --changes-only
```

| Flag | Effect |
| --- | --- |
| `--namespace NAME` | Limit to namespaces with this exact `name` (repeatable) |
| `--strategy ff-only\|fetch-only` | How existing clones are described (default `ff-only`) |
| `--parallel N` | Worker count (default from `settings.parallelism`) |
| `--refresh-discovery` | Ignore discovery cache TTL |
| `--changes-only` | Suppress `OK`-only lines |

## `local sync`

Clone or update repositories. **Requires `--write`** to perform clones, fetch, or `merge --ff-only`.

```bash
uv run repoman local sync              # preview only
uv run repoman local sync --write      # apply
```

Same flags as `local plan`.

**Conflict policy:** dirty worktrees, detached HEAD, and non-fast-forward merges produce **`SKIP`** with a reason — never silent overwrites.

## `local status`

Read-only report: clone presence, ahead/behind, dirty state, origin drift.

```bash
uv run repoman local status
uv run repoman local status --json
```

Does not run `git fetch`, `clone`, or `merge`.
