# CI/CD

GitHub Actions workflows under [`.github/workflows/`](../../.github/workflows/):

| Workflow | Trigger | Steps |
| --- | --- | --- |
| `ci.yml` | Push / PR to `main` | `uv sync --all-groups`, `ruff check`, `ruff format --check`, `pytest`, `mkdocs build --strict` |
| `release.yml` | Tag `v*.*.*` | `uv build`, GitHub Release assets |

Reproduce CI locally:

```bash
uv sync --all-groups
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run mkdocs build --strict
```

Publishing to PyPI is optional; release wheels are attached to GitHub Releases when tags are pushed.
