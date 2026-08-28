---
name: gmail-imap
description: Read, list, and full-text search email from a personal Gmail account via Gmail's IMAP server and a fast local SQLite cache. Use for checking the inbox, reading messages, searching the entire mailbox by keyword/sender, or downloading attachments. Read-only; cannot send or modify mail. Requires a Google app password stored via `gmmail setup`.
---

# Gmail IMAP (`gmmail`)

Read-only email access to a personal Gmail account through Gmail's IMAP
server (`imap.gmail.com:993`, verified TLS + Google app password) with a
local SQLite+FTS5 cache for instant full-text search across the whole
mailbox. Sister tool to the `protonmail-bridge` skill's `pmail` — same
commands, same cache design.

The CLI is `gmmail` in this skill's directory. Run commands from the skill
directory as `./gmmail <command> ...` (or invoke it by its absolute path).

All data commands print **JSON on stdout**; progress and errors go to stderr.
Pipe through `jq` when you need to reshape output.

**If gmmail fails or behaves unexpectedly, run the doctor script first:**

```bash
./doctor
```

It checks every runtime dependency (python/sqlite, account configuration,
Keychain credentials, network + TLS + login to imap.gmail.com, cache
database, disk space) and prints an actionable fix for each failure.

## First-time setup

Run `./doctor` — it reports anything missing. On a fresh machine it will ask
you to run `./gmmail setup`, which prompts for the Gmail address and a
**Google app password** (create one at myaccount.google.com/apppasswords —
requires 2FA; paste it with or without spaces), verifies them against Gmail,
stores the password in macOS Keychain, discovers the account's system
mailbox names, and writes config to `~/.local/share/gmmail/config.json`.

Gmail IMAP never accepts the normal Google account password — only app
passwords.

## Commands

```bash
gmmail mailboxes                        # folders + labels, message counts, cached counts
gmmail list [mailbox] [--limit N] [--unseen] [--live]
gmmail read <uid> [--mailbox M] [--max-chars N] [--raw]
gmmail search <words...> [--mailbox M] [--from X] [--since YYYY-MM-DD] [--unseen] [--limit N] [--live]
gmmail search --gmail 'from:bob has:attachment newer_than:7d'   # raw Gmail syntax, server-side
gmmail sync [--mailbox M | --all] [--full] [--skip-all-mail]
gmmail status                           # cache state per mailbox, db size
gmmail save-attach <uid> <index> [--mailbox M]   # index comes from `read` output
```

## Behavior notes

- **Mailboxes**: Gmail labels appear as IMAP mailboxes. System ones live
  under `[Gmail]/` and are **localised by account language** (UK accounts
  get `[Gmail]/Bin` instead of `[Gmail]/Trash`). You can use friendly
  aliases — `All Mail`, `Sent`, `Drafts`, `Starred`, `Spam`, `Trash`/`Bin`,
  `Important` — gmmail resolves them to the account's real names
  (discovered at `setup`/`mailboxes` time from LIST special-use
  attributes). User labels are used as-is, e.g. `--mailbox Receipts`.
  `search` defaults to `All Mail`; `list`/`read` default to `INBOX`.
- **Cache-first**: `list`, `read`, and `search` run an implicit incremental
  sync (at most once per minute) and then serve from the local cache. Use
  `--live` to force a server query or `--no-sync` to skip the implicit sync.
- **Backfill**: `gmmail sync --mailbox "All Mail" --full` caches the entire
  mailbox (resumable if interrupted; over the internet, so slower than a
  local bridge — leave it running). Until it has run, `search` only covers
  what has been synced so far; use `--live` for an uncached server-side
  search. Gmail's IMAP bandwidth allowance (~2.5 GB/day) is generous enough
  for normal archives.
- **Search syntax**: cached search is SQLite FTS5 — plain words are AND-ed,
  `"quoted phrases"` and `OR`/`NOT` work. Results are bm25-ranked with
  snippets. `--gmail` passes the query to Gmail's own search (X-GM-RAW) with
  full Gmail syntax (`from:`, `label:`, `has:attachment`, `newer_than:`,
  `{...}` OR groups) and implies `--live`.
- **Bodies**: most real-world mail is HTML-only; gmmail indexes the stripped
  text of the HTML part so search covers those messages too.
- **Read-only guarantee**: bodies are fetched with BODY.PEEK and mailboxes
  are opened read-only (EXAMINE), so reading mail here never marks it
  `\Seen` and never modifies anything.
- **UIDs are per-mailbox**: a UID from a `search` on `All Mail` must be read
  back with `--mailbox "All Mail"`.
- **Gmail ids**: every message also carries Google's account-wide
  `X-GM-MSGID`/`X-GM-THRID` (stored as `gm_msgid`/`thrid` in output). `read`
  output includes `web_url` — a mail.google.com link that opens the thread
  in a browser.

## Credentials

The app password is read from macOS Keychain (service `gmmail-gmail`) or
`$GMMAIL_PASSWORD`; the account email comes from `$GMMAIL_ACCOUNT` or the
config written by `gmmail setup`. To store or rotate credentials:

```bash
gmmail setup        # prompts for Gmail address + app password, verifies login
```

If logins start failing, revoke the old app password at
myaccount.google.com/apppasswords, create a new one, and re-run setup.

## Data and configuration

- Cache: `~/.local/share/gmmail/mail.db` (SQLite, WAL mode) +
  `~/.local/share/gmmail/attachments/`. Fully rebuildable from Gmail — safe
  to delete; the next `gmmail sync --all --full` repopulates it. A
  UIDVALIDITY change on the server triggers an automatic per-mailbox wipe
  and resync.
- The full-archive cache can grow to several GB (raw bodies incl. HTML are
  stored).
- Env overrides: `GMMAIL_HOST` (imap.gmail.com), `GMMAIL_PORT` (993),
  `GMMAIL_ACCOUNT`, `GMMAIL_PASSWORD`, `GMMAIL_DATA` (cache directory).
- The first command after a minute of quiet runs a fast incremental sync;
  subsequent commands within the minute are instant. `--no-sync` skips
  this; `--live` bypasses the cache entirely.
- Offline behaviour: if Gmail is unreachable, cache-backed commands still
  work (they serve stale data); live commands fail with a clear error.
