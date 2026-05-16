---
title: Real-world smoke test and GitHub private discovery fix
topic: bugfix
date_added: 2026-05-16
tags: [chatlogs]
links:
  - docs/design/repoman.md
  - .adr.md
  - src/repoman/remotes/github_client.py
  - src/repoman/secrets.py
  - tests/unit/test_github_client_listing.py
---

## Commit helper

**SemVer / version bump:** **PATCH** → **`0.3.1`** — fixes GitHub namespace discovery for the
authenticated user (private owner repos were missing, e.g. `dfabianus/repoman`). No CLI flag changes.

**`v0.3.0`** is already tagged and pushed; this fix must **not** reuse that tag. Bump
`pyproject.toml` and `src/repoman/__init__.py` to **`0.3.1`** in the **same commit** as the code.

**Tags / GitHub Release:** **Tag after bump** — push annotated **`v0.3.1`** once the release commit
is on `main` to trigger [`.github/workflows/release.yml`](.github/workflows/release.yml).

**Suggested commit message:**

```
fix(remotes): list private GitHub repos for authenticated user namespace
```

**Copy-paste:**

```bash
git add pyproject.toml src/repoman/__init__.py src/repoman/remotes/github_client.py \
  tests/unit/test_github_client_listing.py \
  docs/chatlogs/2026-05-16_github-private-discovery-fix.md
git commit -m 'fix(remotes): list private GitHub repos for authenticated user namespace'
git push origin main
git tag -a v0.3.1 -m 'v0.3.1'
git push origin v0.3.1
```

## How to try

Operator setup (user config is **not** in the repo — use `~/.config/repoman/`):

```bash
# credentials.toml beside repoman.yaml (POSIX chmod 600)
# remotes.github.token_credentials: "github"  →  [github] token = "..." in TOML

uv run repoman doctor --config ~/.config/repoman/repoman.yaml
uv run repoman local plan --config ~/.config/repoman/repoman.yaml --refresh-discovery
# Expect private owner repos (e.g. dfabianus/repoman) when the token has repo read scope
```

From repository root (developers):

```bash
uv sync --all-groups
uv run pytest tests/unit/test_github_client_listing.py -q
```

## Session summary — what shipped

### Goal

Run a **real-world smoke test** against a live GitHub namespace (`dfabianus`) and explain why
discovery listed only **17** repositories while many more (including **`repoman`**) were missing.

### Operator workflow (validated)

- Config at `~/.config/repoman/repoman.yaml` with `namespaces[].name: dfabianus` and `remotes.github`.
- GitHub token in `~/.config/repoman/credentials.toml` (`[github]` section) referenced via
  `token_credentials: "github"`; file mode **0600**.
- `repoman doctor` — token resolved, `GET /user ok (@dfabianus)`.
- `repoman local plan` — discovery + clone preview under `~/repositories`.

### Root cause

- Private repos (e.g. **`dfabianus/repoman`**) were absent from `local plan` output.
- Listing used **`get_user(namespace).get_repos(type="owner")`** (`GET /users/{login}/repos`), which
  effectively surfaced **public** repos only (~17) for the smoke test.
- **`doctor`** still passed because it only probes `GET /user`, not full repo listing.
- Token must allow **private repository read** (classic `repo` scope or fine-grained access).

### Code fix

- **`src/repoman/remotes/github_client.py`** — when `namespace` equals the authenticated login, use
  `get_user().get_repos(affiliation="owner")` (`GET /user/repos`) so **private owner** repos are included.
- Other users and organizations keep the previous paths (`NamedUser` / org `get_repos`).

### Tests

- **`tests/unit/test_github_client_listing.py`** — asserts authenticated vs named-user listing routes.

### Product notes (not implemented this session)

- **`repoman config init`** — discussed as onboarding helper; manual copy of template remains fine for
  smoke tests.
- **Org / collaborator repos** — still require separate `namespaces` entries or future listing modes;
  not a bug in the private-repo fix.
- Optional follow-up: richer `discovery.*` status (API count vs archived vs filtered).

### Follow-ups

- Tag **`v0.3.1`** after this commit (`v0.3.0` already shipped Phase 3 only).
- Continue real-world test: `local status`, single-repo `local sync --write`, then Phase 4 mirrors.
- Document `token_credentials` + scopes in getting-started when MkDocs lands.
