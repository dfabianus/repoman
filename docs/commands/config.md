# `repoman config`

Manage the declarative YAML configuration file.

## `config path`

Print the resolved configuration file path (respects `--config` when passed).

```bash
repoman config path
```

## `config init`

Create `repoman.yaml` from the bundled template at the default or given path.

```bash
repoman config init
repoman config init --config /path/to/repoman.yaml
repoman config init --force
```

On success, prints short **next steps** (edit file, optional `credentials.toml`, `validate`, `doctor`).

## `config validate`

Load YAML, merge defaults, and run schema checks.

```bash
repoman config validate
```

## `config show`

Dump configuration as YAML.

```bash
repoman config show
repoman config show --resolved
```

`--resolved` merges built-in defaults before printing.

## `config set`

Set or remove a nested key using **dot notation**. Default is **preview-only**; pass **`--write`** to persist.

```bash
# Preview
repoman config set paths.workspace_root '~/repositories'
repoman config set settings.parallelism 8

# Apply
repoman config set paths.workspace_root '~/repositories' --write

# Remove a key
repoman config set settings.changes_only --unset --write
```

List indices use numbers: `namespaces.0.name` → `"my-org"`.

Values are parsed with YAML rules (`true`, `null`, numbers, inline lists).
