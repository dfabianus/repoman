# Coding agent guidelines for repoman

This file defines how AI coding agents (e.g. Cursor, Copilot) collaborate on this
repository. Human reviewers should treat it as the canonical contributor guide. It is
**public**: avoid organizational trivia, internal codenames, or other repositories;
describe behaviour only in terms of this project and its published design.

**Authoritative product specification:** [`docs/design/repoman.md`](docs/design/repoman.md).
When CLI semantics, scope, or roadmap change, update that document in the same change
series as the code.

## Language

- **All content in English:** code, comments, docstrings, commit messages, user-facing
  CLI strings, `docs/chatlogs/` entries, and Markdown under `docs/`.
- Keep domain vocabulary consistent with the design doc (*dry-run*, *idempotent*,
  *forge*, *namespace*, *mirror*, *preview*).

## Platform and configuration paths

- **Targets:** Linux, macOS, and Windows. Core logic must not assume a particular host
  vendor, sync client, or shell. Use `pathlib`, normalize user paths explicitly, and
  keep path resolution testable without implicit OS globals where feasible.
- **Default config file:** if `REPOMAN_HOME` is set, configuration lives under that
  directory; otherwise use `~/.config/repoman/repoman.yaml` on POSIX and
  `%USERPROFILE%\.repoman\repoman.yaml` on Windows (exact rules in the design doc).
- **Credentials:** optional `credentials.toml` beside `repoman.yaml` when using
  `token_credentials`. On POSIX the file must be mode `0600` or token resolution
  fails fast with a clear error.

## Tooling — strictly uv

Use **uv** for every environment and dependency operation.

- `uv add <pkg>` / `uv add --dev <pkg>` to add dependencies.
- `uv remove <pkg>` to remove them.
- `uv run <cmd>` to execute commands in the project environment.
- `uv sync` / `uv sync --all-groups` to recreate the environment from the lockfile.
- **Do not** hand-edit `[project] dependencies` or `[dependency-groups]` in
  `pyproject.toml`; those sections are owned by `uv add` / `uv remove`.
- **Do** edit `[project]` metadata (including `version` for releases), `[project.scripts]`,
  and tool configuration (`[tool.ruff]`, `[tool.pytest.ini_options]`, and similar).

## Code style

| Area | Rule |
| --- | --- |
| Python | 3.13+ per `requires-python` in `pyproject.toml` |
| Linter / formatter | **ruff** (line length **100**, target **py313**) |
| Type hints | Required on every **public** function and method |
| Docstrings | Google style on public APIs; module docstring at top of each `.py` file |
| Imports | ruff isort; prefer absolute imports |

Local checks (must match CI):

```bash
uv sync --all-groups
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

## Architecture principles

### Pure logic vs. I/O separation

**Pure modules** perform validation, layout computation, planning, filtering, and
status formatting: **no** filesystem access, subprocesses, or network when avoidable.

**I/O modules** load YAML, invoke `git` via **subprocess** (no shell-script glue),
perform HTTP/API calls, and implement CLI entrypoints. Isolate forge-specific clients
under `src/repoman/remotes/`.

### One subcommand ≈ one subpackage

Place feature code under `src/repoman/<domain>/` (`local/`, `mirrors/`, `doctor/`, …).
Shared primitives stay at package root (`config.py`, `paths.py`, `status.py`,
`secrets.py`, …).

### Preview-first and safety

Mutating commands default to **preview** (no persistent writes). Applying changes
requires an explicit **`--write`** flag where the design specifies it.

**Never** discard local work implicitly: dirty trees, non-fast-forward updates, and
similar cases must produce **`SKIP`** (or **`WARN`** where appropriate) with an
actionable reason.

### Status vocabulary and exit codes

Emit only these level tokens on status lines:

`OK` · `WOULD UPDATE` · `UPDATED` · `SKIP` · `WARN` · `ERROR`

**Exit codes:**

| Code | Meaning |
| --- | --- |
| `0` | Success; no `ERROR` outcomes |
| `1` | At least one `ERROR` during execution |
| `2` | Invalid usage or configuration load failure **before** meaningful work (when applicable) |

Keep batch output **deterministic** (stable ordering) wherever machine-readable logs are
required.

### Idempotency

Repeated execution with the same configuration and `--write` must converge: avoid
duplicate mutations, unnecessary remote churn, and flaky skip behaviour.

### CLI and behaviour flags

- Prefer **long options in kebab-case** (`--skip-network`, `--changes-only`). Short
  options only when they improve ergonomics without ambiguity.
- **Boolean defaults** must match the design doc (*preview-first*; mutations opt-in).
- **Environment variables** documented in the design doc (`REPOMAN_HOME`, per-remote
  token env vars, non-secret tuning such as `CI=true` affecting cache TTL) are the
  extension surface for automation—do not introduce undocumented magic env vars.
- **Breaking CLI changes** require a SemVer **minor** bump while `major == 0`, or a
  **major** bump after `1.0.0`, plus release notes (see **Versioning and releases**).

## Scope guardrails

Ground truth is [`docs/design/repoman.md`](docs/design/repoman.md).

**In scope (summary):** declarative workspace sync, forge discovery, GitLab remote
mirror configuration for the MVP backend, diagnostics (`doctor`), structured status
output.

**Out of scope (summary):** forge-side repo lifecycle (create/delete/archive),
issue/MR/PR mirroring, storing secrets in YAML or logs, encoding bidirectional mirrors
in a single mirror entry.

If a change request conflicts with the design doc, stop and resolve via an explicit
doc update (and `.adr.md` when present)—do not silently expand scope.

## Testing

- Framework: **pytest** (`uv run pytest`).
- **Unit tests** for pure logic (planners, validators, filters, paths).
- **Integration tests** for Git/subprocess and HTTP clients (`tmp_path`, local bare
  repos, HTTP mocking).
- **CLI smoke tests** with `click.testing.CliRunner`.

## Product backlog (`.adr.md`)

When **[`.adr.md`](.adr.md)** exists in this repository:

- Before starting a non-trivial feature, bugfix, or refactor, add or refresh a
  checkbox item tracing the work.
- Use GitHub-style tasks only: `- [ ]` open, `- [x]` done; keep completed items in the
  same list for history.
- Close the checkbox in the **same** merge series as the shipping code.
- Prefer **small, reviewable slices** (focused commits or PR-sized units): one coherent
  feature slice, bugfix, or refactor per merge when practical—not one giant diff mixing
  unrelated concerns.

Until `.adr.md` exists, track intent in GitHub issues; avoid silent scope creep.

### Recommended slice workflow (maintainers & agents)

1. **Open `.adr.md`** — add or refresh checkboxes for the slice scope; defer unrelated work explicitly.
2. **Implement & test** — code and automated tests for that slice only.
3. **Verify locally** — `uv sync --all-groups`, `uv run ruff check .`, `uv run ruff format --check .`,
   `uv run pytest` (match CI).
4. **Write `docs/chatlogs/…`** when the slice materially changes behaviour or governance.
5. **Close/update `.adr.md`** (`- [x]` on shipped items, keep historical items inline).

Agents should default to this loop unless a maintainer directs otherwise.

## Documentation system

**Target stack** (align implementations when added): **MkDocs** with the **Material**
theme and **mkdocstrings** for API reference.

**Intended layout** (see design doc §4):

- `docs/index.md` — overview and navigation.
- `docs/getting-started.md` — install, first config, safety model.
- `docs/commands/*.md` — one page per command group (`config`, `local`, `mirrors`,
  `doctor`).
- `docs/design/` — architecture and decisions (`repoman.md`, mirror backends, …).
- `docs/deployment/` — CI/CD, packaging, release process summaries.

**Rules:**

- User-facing prose lives under `docs/`; deep behaviour stays accurate relative to
  `docs/design/repoman.md`.
- Do not commit real tokens, private URLs with embedded credentials, or
  organization-specific inventory lists—use placeholders (`example.com`, `<org>`).
- Once `mkdocs.yml` exists, CI **must** run `mkdocs build --strict` (uncomment the step
  in `.github/workflows/ci.yml`). Until then, design Markdown remains valid without a
  site build.

## Runnable examples (`examples/`)

- Keep **small, well-commented, copy-paste-friendly** artefacts under [`examples/`](examples/)
  (minimal YAML, short shell wrappers, numbered subfolders) so newcomers can reproduce
  behaviour **without relying only on pytest**.
- Prefer **English** comments and placeholders (`example.com`, paths under `/tmp`)—never
  real tokens or private inventory.
- When a substantive session ships **user-visible CLI or config** behaviour, it SHOULD add
  or refresh an **`examples/…`** entry in the **same merge series** as the chatlog (when feasible).
- Index assumptions and prerequisites in **`examples/README.md`**.

## Session summaries (`docs/chatlogs/`)

**Required.** After every substantive session (multi-step implementation, non-trivial
design discussion, or whenever behaviour/doc intent shifts), add a new file under
[`docs/chatlogs/`](docs/chatlogs/).

### Commit helper (mandatory placement)

Every chatlog MUST begin with a **Commit helper** section so the maintainer can ship
the session’s changes quickly and consistently with SemVer.

**Order of file contents**

1. **YAML frontmatter** (when used) MUST remain the **first bytes** of the file so
   parsers and tooling stay valid (`---` … `---`).
2. Immediately after the closing `---`, the **Commit helper** section MUST be the
   **first Markdown body content**—nothing (no title, no summary) may appear above it
   except the frontmatter block.
3. Next, a **`## How to try`** section (see below) MUST follow the Commit helper—not
   the narrative summary.
4. If frontmatter is omitted (discouraged), the Commit helper MUST be the very first
   line of the file, followed by **`## How to try`**, then the narrative.

**Commit helper MUST contain**

- **`SemVer / version bump`:** state explicitly whether this session needs **no bump**
  or a **PATCH / MINOR / MAJOR** bump (per [**Versioning, releases, and release
  notes**](#versioning-releases-and-release-notes)). Tie the bump to **what shipped**
  in the session (docs-only vs user-visible behaviour vs breaking changes). Docs-only
  chatlog edits usually need **no bump**; user-visible CLI or config behaviour
  typically needs at least **PATCH** before the next release artefact.
- **`Tags / GitHub Release`:** **always** fill this block—even when the answer is
  **none**. Recommend exactly one outcome for this session, grounded in the described
  changes, for example:
  - **None:** no new tag; stack commits on the default branch only (explain briefly,
    e.g. internal docs, CI-only, or follow-up release planned).
  - **Tag after bump:** specify the **exact tag string** to create after updating
    `pyproject.toml` and `src/repoman/__init__.py` (e.g. `v0.2.0`). Note whether it is a
    **pre-release** tag (`v0.2.0-rc.1`, …) and whether the GitHub Release should be
    marked **pre-release**.
  - **Release workflow:** when tagging should trigger [`.github/workflows/release.yml`](.github/workflows/release.yml),
    say so explicitly (push annotated tag `vX.Y.Z` to `origin`).
  Optionally add a second fenced `bash` block with **copy-paste** `git tag` /
  `git push origin …` commands **only when** a tag is recommended—omit entirely when
  **None**.
- **Suggested commit message:** one imperative subject line; optional scope in
  parentheses (e.g. `docs(chatlogs): …`, `feat(local): …`). Match the gravity of the
  change and call out breaking behaviour in the body or a `BREAKING CHANGE:` footer
  when applicable.
- **Copy-paste git commands:** a fenced `bash` block with **`git add`** listing every
  touched path from this session, then **`git commit -m '…'`** using the suggested
  message (single line). If a version bump belongs in the **same** commit, note that
  the commit MUST include updates to `pyproject.toml` and `src/repoman/__init__.py`;
  if bump is **separate**, provide a second suggested message and command block or a
  clear two-step sequence.
- **Git order when tagging a release:** you **never** attach a SemVer tag before the
  release commit exists locally. Canonical sequence:
  **`git commit` / `git push` (branch with version bump)** → **`git tag -a vX.Y.Z` on
  that commit** → **`git push origin vX.Y.Z`** (or `git push --follow-tags`). Pushing only
  a tag without integrating the commits first leaves detached tags useless for collaborators.

Use [Conventional Commits](https://www.conventionalcommits.org/) shape where helpful
(`feat`, `fix`, `docs`, `ci`, `chore`, `refactor`, `test`). Align the suggested bump
with SemVer: breaking public API → **MAJOR** (or MINOR during `0.y.z` per project
policy—still state it explicitly); new backwards-compatible behaviour → **MINOR**; fixes
→ **PATCH**.

### How to try (mandatory unless N/A)

Right after **`## Commit helper`**, include **`## How to try`** with concrete steps:

- Prefer **`uv run …`** snippets (matching local developer workflow): CLI invocations,
  minimal config paths (`--config …`), pytest selection, or `./examples/...` scripts where
  they exist for this repo.
- For **pure docs / chatlog hygiene** sessions with nothing executable new, write:
  **`N/A (docs-only).`**

### Session narrative (breadth expected)

Following **How to try**, the storyline MUST stay **English** but need not stay minimal:
summarize shipped modules/commands, noteworthy edge cases (`SKIP`, cache TTL, parallelism),
and regression risks a reviewer should skim.

**When to add a file**

- Completing or planning a meaningful change that future readers should discover
  without opening chat logs elsewhere.
- Any session where `docs/design/repoman.md` or `AGENTS.md` gains new policy.

**Naming**

- `YYYY-MM-DD_short-topic.md` (ASCII slug; one topic per file when practical).

**Frontmatter (YAML)**

Include at least:

- `title`, `topic`, `date_added` (ISO date), `tags: [chatlogs]`
- `links:` — repo-relative paths to touched specs or code (e.g. `AGENTS.md`,
  `docs/design/repoman.md`)

**Content (after How to try)**

- English only; **goal → shipped surface (bullets referencing modules/CLI/options) →
  decisions → follow-ups**; avoid one-line fluff when the merge is non-trivial.
- **No secrets**; no customer-specific identifiers.

**Not a substitute for**

- `.adr.md` checkboxes (when present).
- Tests and commit messages (those remain the technical source of truth).

## CI/CD (GitHub Actions)

Workflows live under [`.github/workflows/`](.github/workflows/).

| Workflow | Trigger | Purpose |
| --- | --- | --- |
| `ci.yml` | Push / PR to `main` or `master` | `uv sync --all-groups`, `ruff check`, `ruff format --check`, `pytest` |
| `release.yml` | Push SemVer tags `vX.Y.Z` (optional pre-release suffix) | `uv build`, upload artefacts, GitHub Release with generated notes |

**Rules**

- CI commands must stay reproducible locally (`uv run …`).
- Adding MkDocs extends **`ci.yml`** with `uv run mkdocs build --strict` once the docs
  scaffold lands.
- Publishing to **PyPI** is optional: enable **trusted publishing** (OIDC) with
  `pypa/gh-action-pypi-publish` only after the PyPI project is configured; until then,
  wheels remain GitHub Release artefacts only.

## Versioning, releases, and release notes

### Semantic versioning

Follow **[Semantic Versioning 2.0.0](https://semver.org/)** (`MAJOR.MINOR.PATCH`).

- **`0.y.z`:** early development; breaking CLI or config changes are allowed but must
  be called out in release notes.
- **`1.0.0` onward:** honour SemVer strictly for the **documented public surface**:
  CLI stable flags, config schema version field, documented env vars.

### Single source of truth for the running version

Until automated tooling ties them together, bump **both**:

- `project.version` in `pyproject.toml`
- `__version__` in [`src/repoman/__init__.py`](src/repoman/__init__.py)

Keep them identical for each release tag. Long-term, prefer reading version from
package metadata only—when that migration happens, update this section.

### Tags and GitHub Releases

- **Ordering:** Merge or push to the integration branch (`main`/`master`) the commit(s)
  that bump `pyproject.toml` and `src/repoman/__init__.py`; **then** create the **annotated**
  tag **`vX.Y.Z`** on **that** release commit; **then** push the tag (`git push origin vX.Y.Z`).
  The release workflow triggers on tag push. The leading `v` matches
  [`.github/workflows/release.yml`](.github/workflows/release.yml).
- **Release notes:** the release workflow enables GitHub **auto-generated** notes.
  Maintainers may edit the GitHub Release description for highlights.
- **Optional `CHANGELOG.md`:** if introduced, follow *[Keep a Changelog](https://keepachangelog.com/)*
  and update it in the release PR/commit series.

### Artefacts

- **`uv build`** produces `dist/*.tar.gz` and `dist/*.whl`. The release workflow uploads
  them as GitHub Release assets and as workflow artefacts for auditing.
- **Wheel tags** must match `requires-python` and dependency reality; adjust classifiers
  in `pyproject.toml` as the project matures.

### Pre-releases

Pre-release identifiers (`v1.2.3-beta.1`, PEP 440-compatible) may be used for testers.
Mark GitHub Releases as pre-release when behaviour is unstable or schema-breaking.

## Security

- Never commit secrets (tokens, passwords, private URLs with embedded credentials).
- Redact tokens in logs, audit trails, and user-visible errors (see design doc §6).
- Mirroring proprietary repositories to public forges is an **organizational**
  compliance decision; the tool must not imply consent—document risk in user-facing
  docs when adding mirror features.

## Bundled templates

[`src/repoman/templates/repoman.yaml.example`](src/repoman/templates/repoman.yaml.example)
must stay aligned with the configuration schema in [`docs/design/repoman.md`](docs/design/repoman.md).

## Commit conventions

- Imperative, concise subjects (`add mirror planner`, not `added planner`).
- Prefer one logical change per commit.
- Reference GitHub issues or `.adr.md` tasks when it aids traceability.
