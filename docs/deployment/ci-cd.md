# CI/CD

GitHub Actions workflows under [`.github/workflows/`](https://github.com/dfabianus/repoman/tree/main/.github/workflows):

| Workflow | Trigger | Steps |
| --- | --- | --- |
| `ci.yml` | Push / PR to `main` | `uv sync --all-groups`, `ruff check`, `ruff format --check`, `pytest`, `mkdocs build --strict` |
| `docs.yml` | Push to `main` / `master`, or manual | `uv sync --all-groups`, `mkdocs build --strict`, deploy to **GitHub Pages** |
| `release.yml` | Tag `v*.*.*` | `uv build`, GitHub Release assets, **publish to PyPI** ([`repoman-cli`](https://pypi.org/project/repoman-cli/)) |

## GitHub Pages (documentation site)

The site is built by [`.github/workflows/docs.yml`](https://github.com/dfabianus/repoman/blob/main/.github/workflows/docs.yml) and published with
**GitHub Actions** (not the legacy `gh-pages` branch).

1. In the GitHub repo, open **Settings → Pages**.
2. Under **Build and deployment**, set **Source** to **GitHub Actions** (not “Deploy from a branch”).
3. Merge `main` (or run **Actions → Docs → Run workflow**) so `docs.yml` completes once.
4. After the first successful deploy, the site is available at **`https://dfabianus.github.io/repoman/`**
   (forks should change `site_url` in `mkdocs.yml` to match *their* `https://<user>.github.io/<repo>/` URL).

`site_url` in `mkdocs.yml` must stay in sync with that public URL so search, `sitemap.xml`, and absolute links behave correctly.

Reproduce CI locally:

```bash
uv sync --all-groups
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run mkdocs build --strict
```

Publishing to **PyPI** happens automatically when you push a matching SemVer tag (see below).

## PyPI (`repoman-cli`)

The **distribution** on PyPI is [`repoman-cli`](https://pypi.org/project/repoman-cli/) (the unqualified
name `repoman` was already taken). Install with:

```bash
pip install repoman-cli
# or: uv pip install repoman-cli
```

The **console command** remains `repoman` (see `[project.scripts]` in `pyproject.toml`).

### Trusted publishing (OIDC)

[`release.yml`](https://github.com/dfabianus/repoman/blob/main/.github/workflows/release.yml) uses
[`pypa/gh-action-pypi-publish`](https://github.com/pypa/gh-action-pypi-publish) with **`id-token: write`**
and a GitHub **environment** named **`pypi`**.

1. On PyPI → your project → **Publishing** → the pending publisher should reference:
   - **Repository:** `dfabianus/repoman` (or your fork if you publish from a fork),
   - **Workflow:** `release.yml`,
   - **Environment name:** `pypi` (must match the workflow job).
2. On GitHub → **Settings → Environments** → create **`pypi`** (no protection rules required for a
   solo maintainer; add reviewers if you want a manual gate).
3. Bump `version` in `pyproject.toml` and `__version__` in `src/repoman/__init__.py`, merge to `main`,
   then tag and push **`vX.Y.Z`** on that commit. The workflow uploads **`repoman-cli==X.Y.Z`**.

If your PyPI publisher was created **without** an environment name, remove the `environment:` block
from `release.yml` (or add `pypi` to the PyPI publisher configuration) so OIDC subjects match.

### Reproduce release build locally

```bash
uv sync --all-groups
uv build
ls dist/
```
