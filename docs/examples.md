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
