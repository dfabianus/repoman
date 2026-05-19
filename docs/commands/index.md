# Commands

All subcommands accept **`--config PATH`** (default: platform config path from `repoman config path`).

Global options on the root group:

- **`--version`** — print package version
- **`-h` / `--help`**

## Groups

| Group | Purpose |
| --- | --- |
| [`config`](config.md) | Create and edit `repoman.yaml` |
| [`doctor`](doctor.md) | Tokens and API reachability |
| [`local`](local.md) | Clone layout, plan, sync, status |
| [`mirrors`](mirrors.md) | Forge-side mirrors *(planned)* |

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success; no `ERROR` lines |
| `1` | At least one `ERROR` during execution |
| `2` | Missing config, load failure, or invalid usage before work starts |
