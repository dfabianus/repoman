# `repoman mirrors` *(planned)*

Forge-side mirror configuration (`gitlab_remote_mirror` backend) is on the
[roadmap](../design/repoman.md) (Phase 4+). No `mirrors` subcommands are shipped yet.

When implemented, expect:

- `mirrors plan` / `mirrors sync --write`
- `mirrors list --json`
- `mirrors lock --write`

See the design doc §9 for behaviour and safety notes.
