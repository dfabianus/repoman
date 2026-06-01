---
title: repoman design specification
audience: contributors
status: active
see_also:
  - https://python-gitlab.readthedocs.io/
  - https://pygithub.readthedocs.io/
  - https://docs.gitlab.com/ee/api/remote_mirrors.html
  - https://github.com/gabrie30/ghorg
  - https://github.com/cooperspencer/gickup
  - https://github.com/your-tools/tsrc
---

# Projekt-Design: `repoman`

> **Status:** MVP Phase 0–2 (Kern): `config`, `doctor`, `local plan` / `local sync`; `local status` und `mirrors` folgen laut Roadmap.
> **Kontext:** `repoman` ist ein **eigenständiges, plattformneutrales** CLI-Werkzeug für Forge-Discovery,
> lokale Workspaces und Mirror-Konfiguration. Es kann neben anderen Automatisierungs- oder
> Dokumentations-Tools eingesetzt werden; getrennte Projekte behalten jeweils eigene Konfiguration.

## 1. Mission und Scope

### 1.1 Mission (ein Satz)

> `repoman` hält eine YAML-deklarierte Menge an Git-Repositories über mehrere
> Forges hinweg lokal aktuell und konfiguriert deren Mirror-Beziehungen
> idempotent — preview-first, ohne lokale Änderungen zu zerstören.

### 1.2 Was `repoman` macht (in scope)

- **Lokale Synchronisation**: Repositories aus konfigurierten Namespaces (GitLab
  Groups, GitHub Users/Orgs) klonen oder aktualisieren, in einem deterministischen
  Layout unter einem `workspace_root`.
- **Mirror-Verwaltung**: Server-seitige Push-/Pull-Mirrors (primär in GitLab via
  Remote-Mirror-API) deklarativ aus der YAML heraus konfigurieren — die Config
  ist die SSOT für „wer spiegelt wohin“.
- **Discovery**: Namespaces auf der Remote-Seite scannen (alle Repos in einer
  Group/Org) und mit Include-/Exclude-Filtern an einen lokalen Baum anbinden.
- **Diagnose**: Read-only Konsistenz-Checks (`doctor`).

### 1.3 Was `repoman` **nicht** macht (out of scope)

- Keine Repo-CRUD-Operationen auf Remote-Seite (kein Create/Delete/Archive — das
  bleibt `gh`/`glab`/Web-UI).
- Keine Issue-/MR-/PR-Spiegel (eigenständige „Cockpit“- oder Ticket-Spiegel-Tools).
- Keine eingebaute Markdown-/Wiki-Renderer-Schicht — `repoman` kann später **strukturierte Daten** (JSON-Status)
  exportieren, die andere Tools rendern; keine eigene Renderer-Schicht.
- Kein anbieterspezifisches Cloud-Sync- oder Laufwerks-Setup (bleibt außerhalb des Scopes).
- Keine Frontmatter-/Notiz-Normalisierung (bleibt außerhalb des Scopes).
- Kein Secret-Storage als Feature — `repoman` **liest** nur Tokens (siehe §6).
- Kein bidirektionaler Mirror — ausdrücklich nur einseitige Datenflüsse pro
  Mirror-Eintrag.

### 1.4 Primary Use Case (Default-Verhalten)

> *„Tracke per Default **alle** Repositories in einem Namespace; erlaube
> Include/Exclude für Sonderfälle.“*

Konkret: ein YAML-Eintrag `namespaces: [{ remote: gitlab, name: acme-org, include_subgroups: true }]`
genügt, um die ganze Gruppe in `~/repositories/gitlab/acme-org/<repo>` zu halten.
Filter werden additiv darauf gelegt (`include`, `exclude` mit Glob-Pattern).

## 2. Verwandte Tools und Abgrenzung

Vor der Implementierung wurde der Markt gesichtet. Wichtigste Findings:

| Tool | Modell | Was es löst | Warum es **nicht** reicht |
|---|---|---|---|
| `tsrc` (Python) | Manifest in einem Repo, Gruppen, parallel | Multi-Repo-Sync GitLab-zentrisch | Manifest sitzt im Mono-Repo; kein Mirror-Feature |
| `vcstool` (Python) | YAML-Import-Liste | Klon-/Pull-Klassiker (ROS) | Kein Namespace-Scan, kein Mirror |
| `ghorg` (Go) | Org/Group-Discovery, klont alles | Genau das Discovery-Pattern | Kein Mirror, kein State-/Lock-Konzept |
| `gickup` (Go) | YAML-Backup zwischen Forges | Genau das Mirror-Pattern | Tut nur Mirror (clientseitig), kein Workspace |
| `gita` (Python) | Lokale Repo-Registry, Status-Cockpit | Hübsche Übersicht | Klont nichts, kein Mirror |
| `Google repo`, `west` | XML-/YAML-Manifest | Monorepo-Workspaces (AOSP, Zephyr) | Branch-Modell zu opinionated |
| `mr` (Perl) | `.mrconfig`-Liste | Klassiker, dünn | Keine Forge-Awareness |
| `python-gitlab`, `PyGithub` | API-Libraries | Bausteine | Keine End-User-CLI |

**Folgerung:** `repoman` = `tsrc`-artiges Manifest + `ghorg`-artige Discovery +
`gickup`-artiges Mirror-Modell + `gita`-artiger Status — aber als **eine** CLI mit
einheitlichem Status-Vokabular, einer YAML als SSOT und einem ausdrücklichen
Preview-First-Anspruch.

Beide Vorbild-Tools (`ghorg`, `gickup`) sind in **Go**. `repoman` wird
trotzdem in **Python** implementiert (siehe §3); optional können in Phase 2 einzelne dieser Tools
als alternative Backends angebunden werden.

## 3. Technologie-Entscheidungen

### 3.1 Sprache: Python 3.11+

Begründet, weil:

- Ein Python-CLI-Ökosystem profitiert von identischen Idiomen für Tests, Linting und
  Dokumentation — kein Kontextwechsel.
- `python-gitlab` ist die reichhaltigste, typgepflegteste GitLab-Library und
  hat **direkte Unterstützung für `project.remote_mirrors`** — genau der
  Mirror-Kern.
- `PyGithub` bzw. `gh` als Subprozess decken die GitHub-Seite ab.
- Parallelität für I/O-bound Operationen erledigt
  `concurrent.futures.ThreadPoolExecutor` ohne Komplexität.
- Distribution: `uv tool install repoman-cli` / `pip install repoman-cli` reicht. Falls später ein Single-Binary
  gewünscht ist, lässt sich `repoman` mit `pex`/`shiv` packen.

Bewusst **kein** Bash: Skripte sind nicht Windows-tauglich, testarm und passen
nicht zu Preview-First / Idempotenz-Disziplin. Alle Git-Aufrufe sind
`subprocess`-Wrapper mit strukturierter Rückgabe.

### 3.2 Toolchain (verbindlich)

| Bereich | Werkzeug |
|---|---|
| Paket-/Env-Manager | **uv** (siehe `AGENTS.md`) |
| CLI-Framework | `click` |
| Konfig-Format | YAML (`pyyaml`) |
| HTTP | `httpx` (für direkte API-Calls, falls Lib fehlt) |
| GitLab-API | `python-gitlab` |
| GitHub-API | `PyGithub` (oder `gh` als Subprozess) |
| Git-Operationen | `subprocess` gegen System-`git` |
| TOML-Lesen | `tomllib` (stdlib) |
| Linter/Formatter | `ruff` |
| Tests | `pytest`, `click.testing.CliRunner`, `tmp_path` |
| Doku | `mkdocs-material` mit `mkdocstrings` |

Dependencies werden **ausschließlich** über `uv add` gepflegt — `pyproject.toml`
`[dependencies]`-Sektion ist nicht manuell zu editieren (wie in `AGENTS.md` beschrieben).

### 3.3 Designprinzipien (übernommen aus bewährten Python-CLI-Mustern)

| Prinzip | Konkret bei `repoman` |
|---|---|
| **Filesystem-first** | Direkter Lese-/Schreibzugriff auf `~/repositories`; kein Daemon. |
| **Preview-first** | Default `--dry-run`; persistente Aktionen brauchen `--write`. |
| **Idempotent** | Wiederholter Lauf erzeugt keinen Drift; Skip wenn Zustand passt. |
| **Statusvokabular** | `OK` · `WOULD UPDATE` · `UPDATED` · `SKIP` · `ERROR` · `WARN` |
| **Pure logic vs. I/O** | `planner.py` rein, `runner.py`/`api.py` I/O. |
| **Modular** | Ein Subkommando ⇒ ein Subpackage. |
| **Plattformneutral** | Linux, macOS, Windows; keine OneDrive-/`M:\`-Annahmen. |

## 4. Architektur und Repo-Layout

```text
repoman/
  pyproject.toml             # uv-managed
  uv.lock
  README.md
  AGENTS.md                  # Contributor- und Agenten-Richtlinien
  .adr.md                    # Living backlog (Checkboxen)
  src/repoman/
    __init__.py
    __main__.py
    cli.py                   # click-Group: config, local, mirrors, doctor
    config.py                # YAML-Loader + Schema-Validierung (pure)
    paths.py                 # Layout-Templating {remote}/{namespace}/{repo}
    status.py                # Status-Token + Format (pure)
    secrets.py               # Token-Resolver (mehrstufige Quellen)
    cache.py                 # Discovery-Cache (JSON, TTL)
    local/
      __init__.py
      planner.py             # pure: Zielzustand pro Repo berechnen
      runner.py              # I/O: clone / fetch / pull --ff-only
      git_ops.py             # subprocess-Kapsel um git
      status_probe.py        # pure: parse `git status` Output
    remotes/
      __init__.py
      base.py                # ForgeClient Protocol
      gitlab_client.py       # python-gitlab Wrapper
      github_client.py       # PyGithub Wrapper
      discovery.py           # pure: include/exclude filtern
    mirrors/
      __init__.py
      planner.py             # pure: Diff Wunsch-/Server-Zustand
      runner.py              # I/O: API-Calls oder local push
      local_backend.py       # subprocess git clone --mirror + push --mirror
      audit.py               # Audit-Log schreiben
    doctor/
      __init__.py
      runner.py
      checks.py              # Token, Namespace-Erreichbarkeit, Waisen-Klone
    templates/
      repoman.yaml.example
  tests/
    unit/
      test_planner_local.py
      test_planner_mirror.py
      test_discovery_filter.py
      test_paths_layout.py
      test_secrets_precedence.py
      test_config_validate.py
    integration/
      test_local_sync_against_bare_repos.py
      test_mirrors_sync_with_mocked_gitlab.py
      test_cli_smoke.py
  docs/
    index.md
    getting-started.md
    commands/
      config.md
      local.md
      mirrors.md
      doctor.md
    design/
      repoman.md             # Mirror dieses Designdokuments (entfeintert für Repo)
      mirror-backends.md
    deployment/
      ci-cd.md
```

### 4.1 Schichten

- **Pure** (`config.py`, `paths.py`, `status.py`, `*/planner.py`,
  `remotes/discovery.py`, `local/status_probe.py`): keine I/O, voll
  unit-testbar.
- **Runner / I/O** (`*/runner.py`, `*/git_ops.py`, `remotes/*_client.py`):
  führen Git, HTTP und API aus; per Integration-Tests mit `tmp_path` und
  Bare-Repo-Fixtures gegen lokale Bare-Repos testbar.
- **CLI** (`cli.py`): dünne Schicht, validiert Optionen, ruft Runner auf.

## 5. Konfiguration

Die YAML lebt unter `${REPOMAN_HOME:-~/.config/repoman}/repoman.yaml` (POSIX)
bzw. `%USERPROFILE%\.repoman\repoman.yaml` (Windows). `--config PATH` überschreibt
das.

### 5.1 Schema (Schemaversion 1)

```yaml
version: 1

settings:
  default_action: preview          # preview | write
  log_level: info                  # debug | info | warning | error
  parallelism: 4                   # Worker für Git/HTTP
  changes_only: false              # nur != OK ausgeben

paths:
  workspace_root: "~/repositories" # ~/repositories/<remote>/<namespace>/<repo>
  cache_root:     "~/.cache/repoman"
  state_root:     "~/.local/state/repoman"   # Audit-Logs, Lock-File

# Layout-Template, in dem Repos abgelegt werden.
# Verfügbare Platzhalter: {remote} {namespace} {subgroup} {repo}
# Default: {remote}/{namespace}/{repo} (Subgroups werden mit '/' eingebettet)
layout: "{remote}/{namespace}/{repo}"

remotes:
  gitlab:
    kind: gitlab
    base_url: "https://gitlab.example.com"
    token_env: "REPOMAN_GITLAB_TOKEN"
    # alternativ:
    # token_credentials: "gitlab"   # Sektion in credentials.toml
    # token_keyring:    { service: repoman, account: gitlab }   # Phase 2
    clone_protocol: "https"        # https | ssh
  github:
    kind: github
    base_url: "https://api.github.com"
    token_env: "REPOMAN_GITHUB_TOKEN"
    clone_protocol: "ssh"

# Default-Use-Case: ganze Namespaces tracken.
namespaces:
  - remote: gitlab
    name: "acme-org"                 # Group-Pfad in GitLab
    include_subgroups: true
    # optionale Filter, additiv:
    include: ["**/*"]              # Glob gegen den vollen Pfad ohne Group-Prefix
    exclude:
      - "archived/**"
      - "*.wiki"
    # Optional: Visibility-Filter (nur für GitHub-Orgs/Users sinnvoll)
    visibility: [public, private]

  - remote: github
    name: "example-user"           # GitHub user/org
    visibility: [public, private]
    include: ["**/*"]
    exclude: ["**/*-archive"]

# Explizite Einzel-Repos (z. B. Drittprojekte, Forks ausserhalb der Namespaces)
repos:
  - source: { remote: github, path: "third-party/upstream-tool" }
    local:  "third-party/upstream-tool"          # relativ zu workspace_root
    pin_branch: "main"                            # optional: nur diesen Branch tracken

# Mirror-Beziehungen (orthogonal zu lokalem Klon)
mirrors:
  - id: "widget-sync"             # stabiler Identifier, nicht generierter Slug
    source: { remote: gitlab, path: "acme-org/widget" }
    target: { remote: github, path: "example-user/widget" }
    direction: push                # push | pull
    backend: gitlab_remote_mirror  # MVP: nur dieser Wert
    enabled: true
    only_protected_branches: false
    keep_divergent_refs: false
    auth_method: token             # token | ssh_deploy_key (Phase 2)
```

### 5.2 Mehrere Config-Dateien (Phase 2)

Variante B (analog getrenntem „Sets“-Konzept): `repoman.yaml` enthält nur `version`, `settings`,
`paths`, `remotes`. Namespaces, Repos und Mirrors liegen in
`~/.config/repoman/sets/*.yaml` und werden per `includes:` referenziert. Im MVP
genügt eine Datei.

**Hinweis (MVP):** Eine zentrale `repoman.yaml` pro Maschine; mehrere Dateien / `includes:` bleiben Phase 2.

### 5.3 Schema-Validierung

`repoman config validate` lädt YAML, prüft:

- Top-Level-Keys gegen Schema (typed dict / pydantic in Phase 2).
- `remote`-Verweise in `namespaces`/`repos`/`mirrors` zeigen auf einen Eintrag
  unter `remotes`.
- `kind` ist `gitlab` oder `github`.
- `backend` in Mirrors ist erlaubt für die jeweilige `source.remote.kind`
  (z. B. `gitlab_remote_mirror` nur wenn source.kind == gitlab).
- Layout-Platzhalter sind bekannt.
- `mirror.id` ist global eindeutig.

Ergebnis: Status-Zeilen wie

```text
OK            config.version            1
OK            remotes.gitlab            base_url=https://gitlab.example.com
ERROR         mirrors[2].backend        local_push not supported for source.kind=github (Phase 2)
```

## 6. Secrets / Token-Management

Tokens stehen **nie** in `repoman.yaml` und nicht im Git. Resolver-Reihenfolge,
**höchste Priorität zuerst**:

1. `--token` CLI-Flag (ephemer, nur für laufendes Kommando, nicht persistiert).
2. **Env-Variable**, benannt in `remotes.<r>.token_env`.
3. **Credentials-Datei** `~/.config/repoman/credentials.toml`, referenziert über
   `remotes.<r>.token_credentials: "<section>"`. Beim Lesen prüft `repoman` die
   Dateirechte (POSIX: muss `0600` sein, sonst `ERROR` und Abbruch).
4. **OS-Keyring** über `keyring` (Phase 2), Eintrag aus
   `remotes.<r>.token_keyring: { service, account }`.
5. **Forge-CLI** als Fallback (Phase 2): `gh auth token` für GitHub, `glab auth status`
   für GitLab — nur wenn keine der oberen Quellen konfiguriert ist.

Format `credentials.toml`:

```toml
# ~/.config/repoman/credentials.toml  (chmod 600)
[gitlab]
token = "glpat-..."

[github]
token = "ghp_..."
```

### 6.1 Verwendung von Tokens

- **API-Calls** (`python-gitlab`, `PyGithub`): Token wird per HTTP-Header
  übergeben, niemals in der URL.
- **Git-Clone/Push** über HTTPS: Token wird zur **Laufzeit** in die URL injiziert
  (`https://oauth2:${TOKEN}@gitlab.example.com/...`) und vor dem Logging
  **redacted**. Alternative bei `clone_protocol: ssh`: kein Token nötig,
  SSH-Schlüssel des Users wird verwendet.
- **Audit-Log und Status-Zeilen**: Token-Strings werden mit Regex-Filter
  maskiert (`***REDACTED***`).

### 6.2 Secret-Doctor-Check

`repoman doctor` prüft pro `remotes.<r>`:

- Quelle aufgelöst? (welche der 1–5)
- Token präsent und nicht leer?
- API-Probe `GET /version` (GitLab) bzw. `GET /user` (GitHub) erfolgreich? Wenn
  `--skip-network` gesetzt, nur Auflösung prüfen.
- Permissions des Tokens — wird nur als `WARN` ausgegeben („insufficient scope
  for remote_mirror“ etc.), nicht als hartes `ERROR`.

## 7. Command-Surface

```text
repoman --version
repoman --help

repoman config init     [--config PATH] [--force]          # Template → Zieldatei
repoman config validate [--config PATH]
repoman config show     [--config PATH] [--resolved]      # mit Defaults aufgelöst
repoman config path                                       # gibt aktiven Config-Pfad aus
repoman config set KEY VALUE [--write] [--unset]          # dotted keys; Preview ohne --write

repoman doctor [--skip-network] [--config PATH]

# --- LOCAL ---
repoman local plan     [--namespace NAME]... [--changes-only]
                       # äquivalent zu `local sync --dry-run`
repoman local sync     [--namespace NAME]... [--write] [--changes-only]
                       [--parallel N] [--strategy ff-only|fetch-only]
repoman local status   [--namespace NAME]... [--json]
                       # read-only: ahead/behind, dirty, last-fetch
repoman local clone    SOURCE_PATH [--remote NAME] [--into PATH]

# --- MIRRORS ---
repoman mirrors plan   [--id ID]... [--changes-only]
repoman mirrors sync   [--id ID]... [--write]
repoman mirrors list   [--json]
repoman mirrors lock   [--write]                # schreibt repoman.lock
                       # erfasst aktuellen Server-Zustand aller Mirrors
```
**Onboarding:** `repoman config init` erzeugt `repoman.yaml` aus dem Bundled-Template;
`repoman config set` ändert dotted Keys (Preview ohne `--write`). Ein interaktiver Setup-Wizard
ist für eine spätere Phase vorgesehen (siehe `.adr.md`).

Bewusst **nicht** im MVP:

- `mirrors add` / `mirrors remove` (CLI ändert YAML) — kommt frühestens Phase 3,
  weil YAML-Edit per Hand fürs MVP ausreicht und Edit-Code bessere Validierung
  braucht.
- `local remove` / `local prune` — räumt verwaiste Klone weg. Erst, wenn das
  Doctor-Tooling stabil ist.

### 7.1 Status-Vokabular und Exit-Codes (verbindlich)

```text
OK            <subject>   <detail>
WOULD UPDATE  <subject>   <plan>
UPDATED       <subject>   <result>
SKIP          <subject>   <reason>
WARN          <subject>   <hint>
ERROR         <subject>   <message>
```

Exit-Codes:

- `0` – alles `OK` oder nur `WOULD …`/`SKIP`/`WARN`.
- `1` – mindestens ein `ERROR` während Ausführung.
- `2` – Konfigurations- oder Argumentfehler (vor jedem I/O).

### 7.2 Beispiel-Output

```text
$ repoman local sync --namespace acme-org
OK            workspace_root             ~/repositories exists
OK            remotes.gitlab.api         200 https://gitlab.example.com/api/v4
OK            discovery.acme-org         42 repos (cache age 14m)
WOULD UPDATE  acme-org/widget            clone https → ./gitlab/acme-org/widget
WOULD UPDATE  acme-org/service-a         pull --ff-only (4 commits behind)
SKIP          acme-org/legacy-app       non-ff: 2 ahead, 3 behind
OK            acme-org/utils            up-to-date
ERROR         acme-org/private-proj     403 from GitLab (token lacks read scope)
```

## 8. Feature-Detail: `local sync`

### 8.1 Algorithmus

Pseudo-Pipeline:

```text
1. Konfig laden + validieren
2. Pro namespaces[i]:
     repos_remote = discovery(remote, name, include_subgroups, visibility)
     repos_remote = filter(repos_remote, include, exclude)
3. Vereinige mit explizit aufgelisteten repos[]
4. Pro repo:
     local_path = layout({remote},{namespace},{repo})  (unter workspace_root)
     plan = decide(repo, local_path, fs_state)
       - fehlt local_path  → CLONE
       - existiert, .git missing → ERROR ("not a git repo")
       - existiert, origin.url != expected → WARN ("remote drift") oder UPDATE (mit --write)
       - existiert, normal → FETCH + PULL --ff-only
       - existiert, dirty → SKIP ("working tree dirty")
       - existiert, ff nicht möglich → SKIP ("non-ff: N ahead, M behind")
5. Bei --write: ausführen, sonst nur Plan ausgeben.
```

### 8.2 Konflikt-Politik (kompromisslos sicher)

- **Default-Pull-Strategie:** `git fetch -p` + `git merge --ff-only @{u}` —
  nichts wird rebased, nichts wird gerebased, nichts wird vermerged. Wenn `ff`
  nicht möglich, wird das Repo geskippt mit klarem Grund.
- **Working-Tree-Dirty:** wird unangetastet gelassen — `SKIP`. Das gilt explizit
  auch im `--write`-Modus.
- **Detached HEAD oder Branch != Tracking-Branch:** `SKIP` mit Hinweis.
- **`origin.url`-Drift:** Default nur `WARN`. Wer das auto-fixen will, muss
  `--fix-remotes` setzen (Phase 2).
- **Submodules:** im MVP **nicht** rekursiv. `SKIP` bei Submodul-Vorhandensein
  mit `WARN: contains submodules — skipped`. Phase 2: `--submodules`.

Diese Politik garantiert, dass `local sync` **niemals** lokale Arbeit zerstört —
worst case sieht der User ein `SKIP` und schaut selbst nach.

### 8.3 Parallelität

`--parallel N` (Default aus `settings.parallelism`) nutzt einen
`ThreadPoolExecutor`. Pro Repo eine Task. Ergebnisse landen in einer
Queue, der Hauptthread schreibt Status-Zeilen geordnet (nach `namespace/repo`),
sodass Output deterministisch und parsbar bleibt.

### 8.4 Discovery-Cache

- Listing einer Group/Org wird unter
  `${cache_root}/discovery/{remote}_{namespace_hash}.json` gespeichert.
- TTL: 15 Minuten Default, `settings.discovery_cache_ttl` überschreibbar.
- `--refresh-discovery` ignoriert den Cache.

Begründung: GitLab/GitHub-Listings sind langsam und Rate-Limit-anfällig; ein
typischer Sync-Lauf will nicht jedesmal die Group-API durchpaginieren.

## 9. Feature-Detail: `mirrors sync`

### 9.1 Backend: `gitlab_remote_mirror` (MVP)

Für jeden Mirror-Eintrag mit `backend: gitlab_remote_mirror`:

```text
1. Resolve source.path → GitLab project id (cached).
2. GET /projects/:id/remote_mirrors → server_state.
3. Plan = diff(desired_state, server_state) für (target_url, enabled,
            only_protected_branches, keep_divergent_refs).
4. Wenn target_url nicht existiert:           POST /remote_mirrors  → WOULD UPDATE / UPDATED
   Wenn Drift in Feldern:                     PATCH .../:mirror_id → WOULD UPDATE / UPDATED
   Wenn alles passt:                          OK / SKIP
5. Token-URL: https://oauth2:${TARGET_TOKEN}@<target.host>/<target.path>.git
   Token im Server-Mirror ist GitLab-seitig gespeichert; die API-Anfrage übergibt ihn beim POST.
6. Audit-Log: jede schreibende Operation mit Zeitstempel, mirror.id, Aktion.
```

Wichtig: GitLab speichert den Token im Mirror-Objekt **server-seitig**.
`repoman` selbst behält keinen Token persistent — er fließt nur durch die
API-Aufrufe und wird in der lokalen URL nie auf Platte geschrieben.

### 9.2 Lock-File `repoman.lock`

Optional generiert via `repoman mirrors lock --write`. Format YAML/JSON:

```yaml
version: 1
generated_at: 2026-05-12T20:35:00Z
mirrors:
  - id: widget-sync
    source: { remote: gitlab, project_id: 1234, path: acme-org/widget }
    target: { remote: github, path: example-user/widget }
    server_state:
      mirror_id: 87
      enabled: true
      only_protected_branches: false
      keep_divergent_refs: false
      last_successful_update_at: 2026-05-12T20:00:11Z
      last_error: null
```

Zweck: reproduzierbarer Server-Zustand, gut für Diffs in Reviews. Lock-File ist
**nicht** SSOT — das bleibt die YAML — aber sehr nützlich für Audits.

### 9.3 Audit-Log

`${state_root}/audit/YYYY-MM/repoman.log` (POSIX) bzw. unter
`%LOCALAPPDATA%\repoman\audit\` (Windows). Eine Zeile pro mutierender Aktion,
JSON-Lines:

```json
{"ts":"2026-05-12T20:35:01Z","action":"mirror.create","mirror_id":"widget-sync","source":"gitlab:acme-org/widget","target":"github:example-user/widget","result":"ok","http_status":201}
```

Tokens **werden vor dem Loggen redacted**.

### 9.4 Backend: `local_push` (Phase 2)

Für Konstellationen, in denen kein server-seitiger Mirror möglich ist (z. B.
GitLab CE Pull-Mirror nicht verfügbar, oder Quelle ist GitHub und Ziel ein **selbst gehostetes GitLab**):

```text
cache_dir = ${cache_root}/mirror-cache/<mirror.id>.git
1. wenn nicht existiert:   git clone --mirror <source_url> cache_dir
2. git -C cache_dir remote update --prune
3. git -C cache_dir remote set-url --push origin <target_url>
4. git -C cache_dir push --mirror
```

Dieser Pfad mutiert lokal: `--write` Pflicht. Bare-Caches liegen **außerhalb**
des `workspace_root` und werden nie als Working-Tree benutzt.

### 9.5 Backend: `github_actions_mirror` (Optional, Phase 3)

Idee: `repoman` generiert eine GitHub-Action `.github/workflows/mirror.yml`
samt nötigem Secret-Set via `gh secret set`. Diese Action pusht periodisch an
ein Ziel. Sinnvoll für Open-Source-Repos, deren SSOT auf GitHub liegt und die
zusätzlich in ein **internes GitLab** gespiegelt werden sollen. Im MVP nicht enthalten,
weil es Schreibrechte auf das Source-Repo erfordert (Workflow-Datei) — das ist
ein anderer Bedrohungsbereich als reine Konfiguration.

## 10. Discovery-Filter (include / exclude)

Filter wirken **nach** dem API-Listing, **bevor** geplant wird.

```yaml
namespaces:
  - remote: gitlab
    name: acme-org
    include_subgroups: true
    include:
      - "**/*"
    exclude:
      - "archived/**"
      - "**/sandbox-*"
      - "team-x/private-experiment"
```

Regeln:

- `include` ist eine Liste von Globs gegen den **relativen Pfad** unterhalb
  `namespace.name` (also `archived/foo`, nicht `acme-org/archived/foo`).
- `exclude` läuft **nach** `include` und entfernt Treffer.
- Default ohne beide Listen: `include: ["**/*"]`, kein Exclude — also alles.
- Glob-Engine: `pathlib.PurePosixPath.match` (`**`-tauglich via `fnmatch`).
- Visibility-Filter (`visibility: [public, private]`) wirkt **vor** Glob — auf
  Listing-Ebene, um API-Rauschen zu vermeiden.

Konsequenz für Audits: `repoman doctor` listet pro Namespace, was nach Filter
übrig bleibt und welche Repos rausgeflogen sind (`SKIP` mit Begründung).

## 11. Tests und Qualität

### 11.1 Test-Pyramide

- **Unit** (≥ 80 % Coverage Ziel):
  - `paths.layout(...)` Permutationen.
  - `planner.decide(...)` mit synthetischen FS-/Server-Zuständen.
  - `discovery.filter(...)` mit Glob-Edge-Cases.
  - `secrets.resolve(...)` mit allen Quellen + Präzedenz.
  - `config.validate(...)` mit Bad-Inputs.
  - `status.format(...)` und Status-Aggregation.
- **Integration**:
  - **Lokale Bare-Repos als Fake-Remote**: `tmp_path/origin.git`,
    `tmp_path/local/...` → `local sync` durchspielen ohne Netz.
  - Gemockte GitLab-API (`responses`/`pytest-httpx`) für `mirrors sync`.
  - `gh`-Subprocess wird per Fake-CLI auf `$PATH` (Dummy-Skript) gemockt.
- **CLI-Smoke** mit `click.testing.CliRunner`.

### 11.2 Lint, Format, Type-Check

`uv run ruff check . && uv run ruff format . && uv run pytest` vor jedem
Commit. `mypy` (oder `pyright`) erst in Phase 2, sobald die API stabilisiert
ist.

### 11.3 CI

GitHub Actions (Spiegel zu GitLab CI, falls Repo dort liegt):

- `ruff check`, `ruff format --check`
- `pytest --cov`
- `mkdocs build --strict`
- (optional) Build & Publish auf TestPyPI bei Tags.

## 12. Roadmap

| Phase | Inhalt | Abnahmekriterium |
|---|---|---|
| 0 | Repo aufsetzen, `uv init`, leeres CLI mit `--version` | `repoman --version` |
| 1 | `config validate`, `doctor`, Loader, Secrets-Resolver, Token-Doctor | YAML laden + Tokens auflösen + Remote-Probe |
| 2 | `local plan` / `local sync` (gitlab+github), Filter, Cache | 1 Group mit 5 Repos auf Festplatte; Konflikte werden geskippt |
| 3 | `local status` (ahead/behind/dirty), `--json`-Output | Tabellen-/JSON-Output für Automation |
| 4 | `mirrors plan` / `mirrors sync` mit `gitlab_remote_mirror` | Test-Repo-Paar wird idempotent konfiguriert; Audit-Log geschrieben |
| 5 | `mirrors lock`, Drift-Erkennung, bessere Doctor-Checks | Lock-File reproduziert Server-Zustand |
| 6 | `local_push`-Backend, `--submodules`, `--fix-remotes` | Fallback-Mirror lauffähig |
| 7 | mkdocs-Doku, `uv tool install`-fähiger Release | `pipx`/`uv tool install repoman-cli` aus PyPI |

Pro Phase: kleiner MR, Tests, `.adr.md`-Häkchen, Doku-Update.

## 13. Integration mit anderen Werkzeugen

- Externe **Workspace- oder Setup-Orchestrierer** können `repoman` als **Python-Dependency**
  importieren oder per **Subprozess** aufrufen (z. B. „Klone die Repos dieses Projekts in einen
  vorgegebenen Baum“).
- **Konfiguration bleibt getrennt:** `repoman` liest nur `repoman.yaml` (und referenzierte Includes
  in späteren Phasen). Fremde Tools übergeben bei Bedarf eine kleine, `repoman`-konforme
  Repo-/Namespace-Liste per **CLI-Argumenten oder Stdin** — keine implizite Kopplung an fremde
  YAML-Schemata.
- Koordination mit anderen Projekten (Roadmaps, Backlog-Dateien) erfolgt **außerhalb** dieses
  Repos; dieses Dokument beschreibt ausschließlich die öffentliche `repoman`-Oberfläche.

## 14. Open Design Decisions

- **Pydantic vs. plain dict + Validation**: zunächst plain dicts mit manuellen `validate_*`-Funktionen;
  Pydantic in Phase 2, wenn das Schema wächst.
- **`clone_protocol` Default**: `https` (mit Token) oder `ssh`? Vorschlag: pro Remote konfigurierbar;
  Default `https` für GitLab (Tokens vorhanden), `ssh` für GitHub (SSH-Keys verbreitet).
  **Entscheidung / Hinweis:** pro Remote frei wählbar; Default **`ssh`** für alle Remotes, sofern
  nicht anders gesetzt (vereinfacht lokale Agent-Setups ohne Token in der Remote-URL).
- **`namespace` als Konzept für GitHub**: ein GitHub-User ist eigentlich kein Namespace, sondern
  „repos owned by user/org“. Absichtlich verallgemeinert als `namespace`; in der Doku klar als
  **user/org** erklären.
- **`repoman.lock`-Format**: YAML (gut lesbar) oder TOML (typisierter)? Vorschlag YAML, weil Diffs
  mit `repoman.yaml` vergleichbar bleiben. **Hinweis:** TOML ist möglich, sobald Lesbarkeit vs.
  Tooling klar zugunsten von TOML spricht (ähnlich wie bei Lockfiles in anderen Ökosystemen).
- **Soft-Delete / Prune**: lokale Klone, die nicht mehr in der Konfig stehen, **nie automatisch**
  löschen — nur per `repoman local prune --write` (Phase 3+).
- **Bidirektionale Mirrors**: bewusst nicht; wer bidirektionale Flüsse braucht, definiert **zwei**
  einseitige Einträge und akzeptiert Konflikt-Risiko. Typische Muster: eine Forge als SSOT mit
  einseitigem Push-Spiegel; wenn **GitLab-Push-Mirrors** ungeeignet sind (Policy, Edition, Quelle
  auf GitHub), greifen spätere Backends (`local_push`, GitHub Actions, manuelle Git-Läufe) — siehe
  Roadmap und §9.
- **Multi-Tenant-Configs**: Eine Datei pro Maschine, oder Profil-Dateien mit `--profile work`?
  MVP: ein `repoman.yaml`; Profile in Phase 2 via `${REPOMAN_PROFILE}`. **MVP-Entscheidung:**
  eine Datei pro Maschine reicht zunächst; getrennte Profile sind optional.
- **Erst CLI, später Library**: API-Surface der Python-Module absichtlich **intern** halten
  (`repoman._internal` oder eingeschränktes `__all__`), um API-Brüche während Phase 2 zu vermeiden.
- **Discovery-Caching im CI**: in CI deaktivieren (`CI=true` → TTL 0). Doku-Hinweis.

## 15. Sicherheits- und IP-Hinweise

- **Allowlist statt Wildcard** für `mirrors`: nur explizit benannte Mirrors
  werden konfiguriert. Es gibt keinen `mirror_all`-Schalter.
- **Pre-write-Bestätigung** (`--write` ohne `--yes`) für Mirror-Mutationen:
  Liste der geplanten Aktionen, dann interaktive Bestätigung; in CI durch
  `--yes` oder `REPOMAN_ASSUME_YES=1` umgehbar.
- **Tokens niemals in YAML / Logs / Audit**. Regex-Redaction beim Logger.
- **Pfade abstrahieren** in versionierten Beispielen (`<user>`, `<org>`).
  Konkrete Firmen- oder Kunden-Identifier nur in der user-lokalen `repoman.yaml`.
- **Vertragliche Abklärung**: Spiegeln von firmen-internen Repos auf öffentlich
  zugängliche GitHub-Repos bleibt eine **organisatorische** Entscheidung — das
  Tool macht es technisch möglich, erzwingt aber keine Compliance-Entscheidung.
  **Hinweis:** Private Ziel-Repos reduzieren das Offenlegungsrisiko.

## 16. Konkrete erste Schritte (Phase 0/1)

1. Repo `repoman` auf GitHub anlegen, `uv init`.
2. `pyproject.toml` mit einem typischen Python-CLI-Stack: `click`, `pyyaml`, `python-gitlab`,
   `PyGithub`, `httpx`; `dev`-Gruppe `ruff`, `pytest`, `pytest-cov`,
   `pytest-httpx`, `mkdocs-material`, `mkdocstrings`.
3. CLI-Skelett (`__main__.py`, `cli.py` mit `--version`, `config validate`,
   `doctor` als No-Op).
4. `config.py` + `secrets.py` + Tests gegen synthetische YAMLs.
5. `remotes/gitlab_client.py` + `remotes/github_client.py` minimal (nur
   `whoami` + `list_namespace`).
6. `doctor` ruft Resolver + Whoami auf und gibt Status-Zeilen aus.
7. CI-Pipeline (ruff, pytest, mkdocs build).
8. Erst danach `local sync` gegen einen kleinen Pilot-Namespace unter eigener Kontrolle testen.

## 17. Referenzen

- Öffentliche Dritt-Anleitungen und APIs (siehe YAML-`see_also`-Liste im Kopf dieses Dokuments).
- `python-gitlab`: <https://python-gitlab.readthedocs.io/>
- GitLab Remote Mirror API:
  <https://docs.gitlab.com/ee/api/remote_mirrors.html>
- `PyGithub`: <https://pygithub.readthedocs.io/>
- `ghorg` (Inspiration Discovery): <https://github.com/gabrie30/ghorg>
- `gickup` (Inspiration Mirror-Modell): <https://github.com/cooperspencer/gickup>
- `tsrc` (Manifest-Stil): <https://github.com/your-tools/tsrc>

## 18. Naechste Schritte

- [x] Entscheidung bestätigen: `repoman` als eigenständiges Python-Tool; begleitende
      Workspace-Roadmaps extern koordinieren.
- [ ] Repo `repoman` auf GitHub veröffentlichen (MIT-Lizenz — Datei [`LICENSE`](../../LICENSE)).
- [x] Erste `repoman.yaml.example` (unter `src/repoman/templates/`) und CLI (`config`/`doctor`).
- [x] Phase 0 abschließen (`uv init`, CLI `--version`, Basis-Paket).
- [x] Phase 1 Kern (`config validate`/`show`/`path`, YAML-Loader, Secrets, Doctor + Tests).
- [x] Phase 2 Kern — `local plan` / `local sync` (Discovery-Cache, GitLab/GitHub-Listing, Layout, ff-only / fetch-only, Tests).
- [ ] Pilot-Sync gegen einen kleinen Namespace unter eigener Kontrolle ausprobieren (z. B. `<org>/sandbox-*`).
