# `repoman doctor`

Read-only checks for configuration, token resolution, and optional remote API probes.

```bash
uv run repoman doctor
uv run repoman doctor --skip-network
```

| Flag | Effect |
| --- | --- |
| `--skip-network` | Resolve tokens only; skip HTTP `whoami` / version probes |
| `--config PATH` | Use a non-default `repoman.yaml` |

Per remote you should see which token source was used (`env:…`, `credentials.toml:…`, or `unresolved`)
and whether the API probe succeeded.

Insufficient token scopes for future mirror features may appear as **`WARN`**, not **`ERROR`**.
