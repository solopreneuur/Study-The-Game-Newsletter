# Study the Game

A weekly Sunday newsletter: 5 short ideas that make ambitious people sharper.
Full spec: [STUDY-THE-GAME-SPEC.md](STUDY-THE-GAME-SPEC.md).

## How a Sunday works

1. cron-job.org dispatches **Study the Game Fetch** at 6:20am ET. It runs
   `/studythegame-fetch`, commits `issues/<date>/candidates.md`, and opens a
   `picks` issue, which GitHub emails to the owner.
2. Reply to that email with picks, e.g. `3* 7 12 18 22`. Optional: one idea of
   your own as text (then pick 4 numbers), edits like `12: change hook to ...`,
   and video links like `7: https://instagram.com/reel/...`.
3. **Study the Game Picks** runs `/studythegame-draft`, sends the issue through
   MailerLite, and comments back with exactly what went out. The issue closes
   on a successful send.

## Secrets (Settings → Secrets and variables → Actions)

| Secret | What |
|---|---|
| `CLAUDE_CODE_OAUTH_TOKEN` | from `claude setup-token` |
| `PERPLEXITY_API_KEY` | Perplexity API |
| `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `EMAIL_TO` | failure alerts only |
| `MAILERLITE_API_KEY` | MailerLite → Integrations → API |
| `MAILERLITE_GROUP_ID` | Study the Game group |
| `MAILERLITE_TEST_GROUP_ID` | Test group (only you) |
| `MAILERLITE_FROM` | verified sender address |

**Variable** `TEST_MODE` = `true` sends to the Test group instead of the real one.
Keep it on for every test and dry run; delete it (or set `false`) to launch.

## Local

`.env` (git-ignored) holds the four `MAILERLITE_*` values.

```bash
python3 .claude/scripts/mailerlite_send.py --test                 # tiny test to the Test group
python3 .claude/scripts/mailerlite_send.py --preview issue.md out # render out.html / out.txt, no send
```

## Site

`site/` is a static Vercel project (root directory `site/`). `/` shows the
latest issue with a signup popup; `/latest` shows it with no popup. Paste the
MailerLite embedded form's action URL into `ML_FORM_ACTION` in
`site/index.html`.
