# CI/CD

GitHub Actions workflows under [`.github/workflows/`](../../.github/workflows/):

| Workflow | Trigger | Steps |
| --- | --- | --- |
| `ci.yml` | Push / PR to `main` | `uv sync --all-groups`, `ruff check`, `ruff format --check`, `pytest`, `mkdocs build --strict` |
| `docs.yml` | Push to `main` / `master`, or manual | `uv sync --all-groups`, `mkdocs build --strict`, deploy to **GitHub Pages** |
| `release.yml` | Tag `v*.*.*` | `uv build`, GitHub Release assets |

## GitHub Pages (documentation site)

The site is built by [`.github/workflows/docs.yml`](../../.github/workflows/docs.yml) and published with
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

Publishing to PyPI is optional; release wheels are attached to GitHub Releases when tags are pushed.
