# Example: preview `local plan` safely

Purpose: exercise CLI wiring with **zero namespace discovery** (`namespaces: []`) so nothing
hits GitLab/GitHub unless you uncomment and edit the sample block below.

Steps (from repo root):

```bash
uv sync --all-groups
REPOMAN_CONFIG="examples/local-plan/repoman.yaml"
uv run repoman config validate --config "$REPOMAN_CONFIG"
uv run repoman local plan --config "$REPOMAN_CONFIG"
uv run pytest tests/integration/test_local_smoke.py -q
```

Optional: copy `repoman.yaml` somewhere under `/tmp`, add a real `namespaces/` entry pointing
at **your** `remotes` key, export the matching `${REPOMAN_*_TOKEN}`, then rerun `local plan`.

**Never commit** customised copies containing real forge paths or credential hints.
