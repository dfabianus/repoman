# Design

`repoman` keeps a YAML-declared set of Git repositories across several forges (GitLab, GitHub)
up to date on disk. It is preview-first and never destroys local work.

Shipped: `config`, `doctor`, `local plan`, `local sync`, `local status`. Planned: `mirrors`.

## Scope

In scope:

- Local sync: clone or fast-forward repositories from configured namespaces (GitLab groups,
  GitHub users/orgs) and explicit repos into a deterministic layout under `workspace_root`.
- Discovery: list a namespace on the forge and filter it with include/exclude globs.
- Diagnosis: read-only checks (`doctor`).

Out of scope:

- Creating, deleting or archiving remote repositories (use `gh`, `glab` or the web UI).
- Issue, merge-request or pull-request mirroring.
- Rendering; `repoman` emits status lines and JSON, other tools render them.
- Storing secrets; `repoman` only reads tokens.
- Bidirectional mirrors; each mirror entry is one-way.

## Principles

- Preview-first: every mutating command is a dry run unless `--write` is given.
- Idempotent: a repeated run produces no drift; matching state is `OK`.
- Deterministic output: rows are sorted by subject, whatever the parallelism.
- Pure logic separate from I/O: planners, validation, filters and status formatting do no I/O.
- One subcommand, one subpackage (`local/`, `doctor/`, later `mirrors/`).
- Platform-neutral: Linux, macOS and Windows; no daemon, no hard-coded drives.

## Architecture

- `cli.py`: thin click layer; parses options, calls runners, prints rows, sets the exit code.
- Pure: `config.py`, `config_setup.py`, `paths.py`, `status.py`, `local/planner.py`,
  `local/status_probe.py`, `local/status_report.py`, `remotes/discovery.py`.
- I/O: `local/runner.py`, `local/git_ops.py` (subprocess around system `git`),
  `remotes/*_client.py` (python-gitlab, PyGithub), `secrets.py`, `cache.py`, `doctor/`.
- Tests: unit tests on pure modules; integration tests run `local` against bare repos in
  `tmp_path` without network; CLI smoke tests via `CliRunner`.

Key decisions:

- Python, not Go or Bash: python-gitlab has native remote-mirror support; Bash is not portable
  and hard to test.
- System `git` via subprocess, not a Git library: matches what the user runs by hand.
- `ThreadPoolExecutor` for I/O-bound work: enough parallelism without async complexity.
- Plain dicts with explicit `validate` functions, no pydantic: the schema is small.
- Module API is internal; the CLI is the public surface.

## Configuration

`repoman.yaml` lives in `$REPOMAN_HOME`, else `~/.config/repoman/` (POSIX) or
`%USERPROFILE%\.repoman\` (Windows); `--config PATH` overrides. One file per machine.
The bundled template `src/repoman/templates/repoman.yaml.example` is the reference schema
(version 1).

Top-level keys: `version`, `settings` (`parallelism`, `changes_only`,
`discovery_cache_ttl`, ...), `paths` (`workspace_root`, `cache_root`, `state_root`), `layout`,
`remotes`, `namespaces`, `repos`, `mirrors`.

- `layout` placeholders: `{remote}`, `{namespace}`, `{subgroup}`, `{repo}`; default
  `{remote}/{namespace}/{repo}`.
- `remotes.<name>.kind` is `gitlab` or `github`; `clone_protocol` is `ssh` (default) or
  `https`. Default `ssh` keeps tokens out of remote URLs.
- A GitHub user or org is called a namespace too; the docs explain it as user/org.

`config validate` checks the schema version, `kind` values, that every `remote` reference
exists, layout placeholders, unique `mirrors[].id`, and that each mirror uses
`gitlab_remote_mirror` with a GitLab source.

## Secrets

Tokens are never in `repoman.yaml`, in git or in output. Resolution order, highest first:

1. A token passed in by the caller (internal API; no CLI flag yet).
2. The environment variable named by `remotes.<r>.token_env`.
3. `remotes.<r>.token_command`, an argv list run without a shell (e.g. `["gh", "auth",
   "token"]`); trimmed stdout is the token. Failure, a 15 s timeout or empty output is an
   `ERROR` for that remote, with no fallback to a possibly stale file.
4. `credentials.toml` next to `repoman.yaml`, section named by `token_credentials`. On POSIX it
   must be mode `0600`, otherwise resolution fails.

- API calls pass the token in a header, never in a URL.
- HTTPS clone and fetch use the clean URL. The token goes to each `git` call through its
  environment (`GIT_CONFIG_COUNT`/`GIT_CONFIG_KEY_n`/`GIT_CONFIG_VALUE_n`, git >= 2.31) as
  `http.<scheme>://<host>/.extraheader = Authorization: Basic base64(<user>:<token>)`, user
  `x-access-token` for GitHub and `oauth2` for GitLab. Existing `GIT_CONFIG_*` entries are
  kept. So the token never lands in `.git/config` or in argv. With `ssh` no token is used.
- Clones by repoman <= 0.5 have `https://<user>:<token>@...` as origin. When the origin is
  exactly that (forge user above, configured HTTPS URL), sync rewrites it to the clean URL:
  `WOULD UPDATE` in preview, `UPDATED` with `--write`. Other credentialed origins are left
  alone.
- Probed origin URLs are shown with credentials as `***`; git error output has the token
  replaced by `***`.
- `doctor` reports per remote which source resolved the token and probes the API; with
  `--skip-network` it only resolves tokens.

## Status lines and exit codes

Every row is `<TOKEN> <subject> <detail>` with a fixed-width token column. The tokens are fixed:
`OK`, `WOULD UPDATE`, `UPDATED`, `SKIP`, `WARN`, `ERROR`.

Exit codes: `0` success (including `WOULD UPDATE`, `SKIP`, `WARN`), `1` at least one `ERROR`,
`2` usage or config error before any I/O.

## Local sync

`local plan` / `local sync`: validate the config; list each namespace (cache or API), drop
archived repos, apply filters; add explicit `repos[]`; render local paths from `layout` under
`workspace_root`; probe each work tree, plan, and execute only with `--write`.

`local status` is read-only: clone presence, dirty state, ahead/behind, last fetch.
`--json` emits a versioned payload (`schema_version: 1`) for automation.

### Conflict policy

Sync never destroys local work; the worst case is a `SKIP` the user inspects.

- Missing path: clone.
- Path exists but is not a Git work tree: `ERROR`.
- `origin` URL differs from the configured forge URL: `WARN`, sync continues.
- Submodules present: `SKIP` (not recursed).
- Dirty working tree: `SKIP`, also with `--write`.
- Detached HEAD or no upstream branch: `SKIP`.
- Ahead and behind (non-fast-forward), or ahead only: `SKIP` with counts.
- Behind only: `git fetch` then `git merge --ff-only`; with `--strategy fetch-only`, fetch only.
  Nothing is ever rebased or merged with a merge commit.

### Parallelism

`--parallel N` (default `settings.parallelism`) runs one task per repository in a thread pool;
results are printed sorted by subject so output stays deterministic.

### Discovery cache

- Listings are cached as JSON under `<cache_root>/discovery/<remote>_<hash>.json`.
- TTL 900 s, overridable by `settings.discovery_cache_ttl`; `--refresh-discovery` bypasses it.
- With `CI` set the TTL is 0, so CI always lists fresh.
- Reason: forge listings are slow and rate-limited.

### Discovery filters

- Globs match the path relative to the namespace (`archived/foo`, not `acme-org/archived/foo`).
- `exclude` runs after `include` and wins. No lists means include everything.
- `**/*` matches every repository, including those directly under the namespace.
- `visibility: [public, private]` restricts by forge visibility.
- GitLab `include_subgroups` (default true) lists subgroups recursively.

## Mirrors (planned)

Not shipped. The config key `mirrors` is validated but not acted on.

- Backend `gitlab_remote_mirror`: diff the desired entry against the GitLab remote-mirror API
  and create or patch it; the target token is stored server-side by GitLab.
- Mirrors are an allowlist of explicit entries with stable `id`s; no mirror-all switch.
- Bidirectional sync means two one-way entries.
- Mutations go to a JSON-lines audit log under `state_root` with tokens redacted.
- Later backends without server-side mirrors: `local_push` (bare mirror cache outside
  `workspace_root`, `push --mirror`) or a generated GitHub Actions workflow.
- Whether internal repos may be mirrored to a public forge is the user's decision.

## Deliberately absent

- `local prune`: orphaned clones are never deleted automatically.
- Commands that edit `namespaces` or `mirrors` in YAML; editing by hand is enough.
- Multiple config files or profiles.
- Real namespaces in examples, tests or docs: placeholders only (`<org>`, `example.com`).
