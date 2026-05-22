# Examples

Runnable, token-free samples live in the repository under [`examples/`](../examples/).

## `examples/local-plan/`

Safe preview with **no namespace discovery** (`namespaces: []`):

```bash
uv run repoman config validate --config examples/local-plan/repoman.yaml
uv run repoman local plan --config examples/local-plan/repoman.yaml
```

To try live discovery, copy the YAML outside Git, add your `namespaces` and remotes, set tokens, then run
`local plan` with `--config` pointing at your copy.

**Never commit** customised configs that contain real tokens or private inventory.

## Namespace include and exclude

On each `namespaces[]` entry you can set **`include`** and **`exclude`**: lists of glob patterns matched
against the repository path **relative to that namespace’s `name`** (the forge `path_with_namespace` /
`full_name` with the namespace prefix removed).

- **GitHub** user or org `acme`: project `acme/my-app` → relative path **`my-app`** (usually a single segment).
- **GitLab** with nested groups: namespace `acme`, project `acme/platform/api` → relative path **`platform/api`**.

**Order:** archived repositories are dropped first, then optional **`visibility`**, then **`include`**
(a repo is kept if any pattern matches), then **`exclude`** (any match drops the repo). If `include` is
omitted or empty, the default is `["**/*"]` (everything under the namespace that passed earlier steps).

Patterns use `fnmatch` rules (`*`, `?`, `[seq]`, `**`). The pattern `**/*` is treated specially: it matches
any non-empty relative path (including top-level repo names).

### Only specific repositories (allowlist)

```yaml
namespaces:
  - remote: github
    name: dfabianus
    include:
      - "repoman"
      - "my-dotfiles"
```

### Everything except named repositories (denylist)

```yaml
namespaces:
  - remote: github
    name: dfabianus
    include: ["**/*"]
    exclude:
      - "scratch-repo"
      - "temp-import"
```

### Only repositories under a GitLab subgroup path

```yaml
namespaces:
  - remote: gitlab
    name: acme
    include_subgroups: true
    include:
      - "platform/**"
```

### Exclude a whole subtree

```yaml
namespaces:
  - remote: gitlab
    name: acme
    include_subgroups: true
    include: ["**/*"]
    exclude:
      - "archive/**"
      - "experiments/**"
```

### Glob by prefix or suffix

```yaml
namespaces:
  - remote: github
    name: dfabianus
    include:
      - "infra-*"
    exclude:
      - "*-archive"
      - "legacy-*"
```

### Combine a broad include with a narrow exclude

```yaml
namespaces:
  - remote: github
    name: dfabianus
    include:
      - "app-*"
    exclude:
      - "app-spike-*"
```

### Explicit list plus a subtree (GitLab-style)

```yaml
namespaces:
  - remote: gitlab
    name: acme
    include_subgroups: true
    include:
      - "billing-service"
      - "auth-service"
      - "shared-libs"
      - "shared-libs/**"
```

Replace remote kind, namespace name, and slugs with your own. Avoid `exclude: ["**/*"]` together with
`include: ["**/*"]` unless you intend to match **no** repositories (exclude wins after include).

For the full design notes, see [Design specification §10 — Discovery filters](design/repoman.md#10-discovery-filter-include-exclude).
