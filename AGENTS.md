# repoman

- Preview-first CLI that syncs a declarative multi-forge git workspace. Spec: docs/design/repoman.md; change it together with the behaviour.
- Mutations need `--write`. Never discard local work: dirty tree or non-fast-forward means SKIP with a reason.
- Status tokens are fixed: OK, WOULD UPDATE, UPDATED, SKIP, WARN, ERROR. Exit codes: 0 success, 1 any ERROR, 2 usage/config failure. Output is deterministic (stable order).
- Public repo: no tokens, real namespaces, employer names or private paths anywhere (code, tests, docs, examples); use placeholders.
- Pushing a tag vX.Y.Z publishes `repoman-cli` to PyPI via OIDC and cannot be undone. Version lives in pyproject.toml and src/repoman/__init__.py; keep both equal.
- Keep src/repoman/templates/repoman.yaml.example in step with the config schema.
- Pure planning/validation modules stay free of I/O; git subprocess and HTTP live in runners and src/repoman/remotes/.
- Secrets never in YAML or logs; credentials.toml must be mode 0600 on POSIX or token resolution fails.
- CI also runs `uv run mkdocs build --strict`.
