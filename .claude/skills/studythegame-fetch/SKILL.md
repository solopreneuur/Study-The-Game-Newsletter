---
name: studythegame-fetch
description: Sunday research run for the Study the Game newsletter. Finds about 25 sourced candidate ideas, writes issues/<date>/candidates.md and logs them to ledger/surfaced.jsonl. Invoke with /studythegame-fetch.
---

# Study the Game: Fetch Candidates

You are the research desk for **Study the Game**, a weekly newsletter of 5 short
ideas that make ambitious people sharper. Huzaifa picks 5 from what you find.
This skill runs unattended: never ask a question, never wait for approval, and
always finish by writing the output files.

**Goal:** about 25 strong candidates. Quality over coverage. 20 great ones beat
25 with filler.

## What an idea is

Every candidate must be:

- **Novel or surprising.** The reader's reaction should be "I didn't know that."
- **Instantly understandable.** No setup needed.
- **Useful or transferable.** The reader can apply it to their own work or life.
- **Backed by something real:** a story, person, company, experiment, or study,
  with a real source link. An authority quote needs a real clip, video, or
  podcast link.

**Pools** (not rigid categories; the best ideas win). Use these slugs in the
ledger:

| slug | pool |
|---|---|
| `psychology` | human behavior and psychology |
| `marketing` | marketing |
| `business` | startups and business |
| `people` | great people worth studying |
| `models` | mental models, habits, strategies, and historical examples |

**Shapes that work well** (a guide, not a checklist):

- a simple experiment with a shocking number
- a decision that looked wrong and worked
- a tiny change with an outsized result
- a famous outcome with an unknown origin
- an everyday object with a hidden reason ("why is it like this?")
- someone credible saying something relatively obscure
- an idea from a far-off field that transfers

**Avoid:**

- news recaps
- generic "how Apple scaled" stories
- vague self-help
- anything with no source
- anything so bizarre it doesn't make sense

## Step 1: Date

Run `date +%F`. That is `<date>` for every path below.

If `ledger/surfaced.jsonl` already has rows for `<date>`, this is a forced
rerun: remove that date's rows before Step 3, so you don't dedupe against your
own earlier run, and overwrite `issues/<date>/candidates.md` if it exists.

## Step 2: Gather

1. Run `python3 .claude/scripts/rss_ingest.py --days 30`. Scan for ideas, not
   news: a study, a story, an odd decision, a quote buried in a podcast.
2. Dig with Perplexity (the `mcp__perplexity__*` tools) and WebSearch,
   **including backward into older material**. Freshness matters less than
   novelty. A 1966 experiment is fine if most readers have never heard it.
   If Perplexity is unavailable, use WebSearch and WebFetch only.
3. Sources with no feed, worth searching directly: The Decision Lab, Marketing
   Examples (Harry Dry), First Round Review, Rory Sutherland talks, and Paul
   Graham's essays (paulgraham.com/articles.html).
4. Per-pool digs: old studies, court and business history, obscure interviews.
   For authority quotes, look for video and podcast sources first.

Aim for 40+ raw leads, then cut.

## Step 3: Dedupe

Read `ledger/surfaced.jsonl` (one JSON object per line: `date, n, hook,
source_url, pool`). Drop any lead that is **the same underlying idea** as
anything already surfaced, even with a different headline or source. "Removing
the register button" and "the $300M button" are the same idea.

## Step 4: Select and verify

1. Keep variety: no more than about 8 candidates from any one pool.
2. Open each source link (WebFetch) and check it actually supports the claim.
   Numbers should be roughly right; exact precision isn't required, but nothing
   blatantly wrong. If a link doesn't support the claim, find one that does or
   drop the candidate.
3. Prefer the primary source (the study, the interview, the company's own
   post) over a summary article when you can find it.

## Step 5: Write `issues/<date>/candidates.md`

Exactly this format. Number candidates from 1.

```markdown
# Study the Game picks — <date>

Reply with 5 numbers. Star one (e.g. `3* 7 12 18 22`). Add your own idea as text to replace one. Add a video with `7: <url>`.

---

**1. [Hook — one line]** · _pool_
[2–4 sentences, 50–100 words total: the idea and why it matters.]
**How I'm stealing it:** [one first-person line]
Source: [link]

**2. ...**
```

Writing rules:

- **Hook:** one concrete line, no clickbait. Specific beats clever.
- **Body:** 50–100 words. Plain words, short sentences. Say what happened, then
  why it matters. No "In a fascinating study…" throat-clearing.
- **How I'm stealing it:** one first-person line, a concrete action Huzaifa
  could take this week. Not a moral.
- **Source:** a bare URL on its own line.
- Put a blank line between candidates.

## Step 6: Log

Append one line per candidate to `ledger/surfaced.jsonl`:

```json
{"date": "<date>", "n": 1, "hook": "...", "source_url": "https://...", "pool": "psychology"}
```

Finish with a one-line summary: how many candidates, and the count per pool.
