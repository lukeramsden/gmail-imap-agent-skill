# Gmail IMAP Agent Skill

Give coding agents read-only access to a Gmail inbox — with instant full-text search across the entire archive — through Gmail's IMAP server.

The skill ships `gmmail`, a zero-dependency Python CLI (stdlib only) that talks IMAP to `imap.gmail.com:993` over verified TLS, maintains a local SQLite+FTS5 cache of the whole mailbox, and serves bm25-ranked keyword search with snippets in well under a second.

## Requirements

- macOS or Linux
- A personal Gmail account with 2-Step Verification enabled and an [app password](https://myaccount.google.com/apppasswords)
- Python 3.9+ (no packages to install — stdlib only)

Note: Google Workspace accounts can have app passwords and IMAP disabled by admin policy — this skill targets personal @gmail.com accounts.

## Install

Install with the Skills CLI:

```bash
npx skills add lukeramsden/gmail-imap-agent-skill@gmail-imap
```

Install globally for all supported agents:

```bash
npx skills add lukeramsden/gmail-imap-agent-skill@gmail-imap -g -a '*' -y
```

List the skills available in this repository without installing:

```bash
npx skills add lukeramsden/gmail-imap-agent-skill --list
```

## Quick start

```bash
./doctor                              # verify all runtime dependencies
./gmmail setup                        # Gmail address + app password -> secure credential store
./gmmail sync --all --full            # backfill the whole archive (resumable)
./gmmail search "invoice"             # ranked full-text search, sub-second
./gmmail search --gmail 'from:bob has:attachment newer_than:7d'
./gmmail list INBOX --unseen
./gmmail read 34655
./gmmail save-attach 34655 1
```

All commands print JSON on stdout; progress and errors go to stderr.

## What the skill provides

- **Full-archive FTS search** — SQLite FTS5 with bm25 ranking and match snippets; phrases, `OR`/`NOT`, and filters (`--from`, `--since`, `--unseen`, `--mailbox`)
- **Raw Gmail search syntax** — `--gmail` passes the query to Gmail's own server-side search (X-GM-RAW): `from:`, `label:`, `has:attachment`, `newer_than:`, `{...}` OR groups
- **Label-aware** — Gmail labels appear as IMAP mailboxes; system mailboxes are localised by account language (UK accounts get `[Gmail]/Bin`) and resolved automatically from LIST special-use attributes, with friendly aliases (`All Mail`, `Sent`, `Bin`, ...)
- **Resumable backfill** — cursor-persisted batches; interrupt and resume freely; automatic wipe/resync if the server's UIDVALIDITY changes
- **Cache-first reads** — `list`, `read`, and `search` serve from the local cache with an implicit incremental sync at most once per minute; `--live` and `--no-sync` escape hatches; cached reads keep working offline
- **Attachment download** — `save-attach` extracts parts to the cache's attachments directory
- **Gmail web links** — every message carries Google's account-wide `X-GM-MSGID`/`X-GM-THRID`; `read` output includes a `web_url` that opens the thread on mail.google.com
- **Self-diagnostics** — `doctor` checks python/sqlite, credentials, network + TLS + login, cache health, and disk space, printing an actionable fix per failure
- **Read-only by construction** — only `BODY.PEEK` and `EXAMINE` on the wire; no STORE/COPY/EXPUNGE/APPEND anywhere, so reading mail never sets `\Seen`

## Privacy and security

- Direct TLS connection to `imap.gmail.com:993` with full certificate verification; nothing else is ever contacted
- On macOS, the app password lives in Keychain (service `gmmail-gmail`). On Linux, it is stored in `~/.config/gmmail/credentials.json` with owner-only permissions (mode 600).
- The cache (`~/.local/share/gmmail/`) is fully rebuildable — delete it anytime and re-run `gmmail sync --all --full`
- The app password can be revoked anytime at myaccount.google.com/apppasswords

## Repository layout

```text
skills/
└── gmail-imap/
    ├── SKILL.md    # agent-facing instructions and command reference
    ├── gmmail      # the CLI (Python stdlib only, executable)
    └── doctor      # runtime dependency checker
```

## License

This repository is available under the MIT License. See [NOTICE](NOTICE) for trademark attribution.

## Install as a pi package

```bash
pi install npm:gmail-imap-agent-skill
```

## Releasing

```bash
npm version patch|minor|major && git push --follow-tags
```

The `v*` tag triggers `.github/workflows/publish.yml`, which publishes to npm
with OIDC trusted publishing and provenance.
