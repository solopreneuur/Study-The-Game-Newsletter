#!/usr/bin/env python3
"""Send a Study the Game issue through MailerLite.

Usage:
  python3 .claude/scripts/mailerlite_send.py issues/YYYY-MM-DD/issue.md
  python3 .claude/scripts/mailerlite_send.py --test                  # one-off "API TEST" to the test group
  python3 .claude/scripts/mailerlite_send.py --sample ISSUE.md       # design check: render + send to test group
  python3 .claude/scripts/mailerlite_send.py --preview ISSUE.md OUT  # render to OUT.html / OUT.txt, no send

Env (from the environment, else from .env in the repo root):
  MAILERLITE_API_KEY        API token
  MAILERLITE_GROUP_ID       "Study the Game" group
  MAILERLITE_TEST_GROUP_ID  group containing only Huzaifa
  MAILERLITE_FROM           verified sender address
  TEST_MODE=true            send to the test group instead of the real one

The issue markdown is rendered into templates/email.html (never sent as bare
converted markdown). The API rejects a custom plain_text, so MailerLite
generates the plain-text version; --preview still writes ours for reference.

Safety: never sends without content, never sends the same
date twice (checked against ledger/sent.jsonl, per mode). Any failure sends nothing.
"""
import datetime
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request

API = "https://connect.mailerlite.com/api/campaigns"
RESULT = "_run/draft-result.md"
LEDGER = "ledger/sent.jsonl"
TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "templates", "email.html")
FROM_NAME = "Huzaifa"
LINK_STYLE = "color:#000; text-decoration:underline;"


def load_env(path=".env"):
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip("'\"")
        if v and not os.environ.get(k):
            os.environ[k] = v


# ---------- markdown -> email ----------
# The issue template uses a tiny subset: a title line, a subtitle, ideas as
# blocks of lines with **bold**, _italic_ and URLs. The sign-off lives in
# email.html, so a trailing "See you Sunday" block in the markdown is dropped.

URL = r"https?://[^\s<>()\x00]+[^\s<>()\x00.,;:!?]"


def blocks(md):
    out = []
    for block in re.split(r"\n\s*\n", md.strip()):
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        lines = [l for l in lines if not re.fullmatch(r"-{3,}|\*{3,}", l)]
        if lines:
            out.append(lines)
    if out and re.match(r"see you sunday", out[-1][0], re.I):
        out.pop()
    return out


def video_line(line):
    """'_I made a video on this →_ URL' -> (label, url) or None."""
    m = re.fullmatch(r"_?(I made a video on this[^_]*?)_?\s*(" + URL + r")", line, re.I)
    return (m.group(1).strip(), m.group(2)) if m else None


def inline_html(text):
    text = html.escape(text, quote=False)
    links = []

    def stash(label, url):
        links.append(f'<a href="{url}" style="{LINK_STYLE}">{label}</a>')
        return f"\x00{len(links) - 1}\x00"

    text = re.sub(r"\[([^\]]+)\]\((" + URL + r")\)", lambda m: stash(m.group(1), m.group(2)), text)
    text = re.sub(URL, lambda m: stash(m.group(0), m.group(0)), text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\w)_(?!\s)(.+?)(?<!\s)_(?!\w)", r"\1", text)  # no italics in this design
    text = text.replace("`", "")
    return re.sub(r"\x00(\d+)\x00", lambda m: links[int(m.group(1))], text)


def inline_text(text):
    text = re.sub(r"\[([^\]]+)\]\((" + URL + r")\)", r"\1 (\2)", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?<!\w)_(?!\s)(.+?)(?<!\s)_(?!\w)", r"\1", text)
    return text.replace("`", "")


def render_line_html(line):
    h = re.match(r"#{1,3}\s+(.*)", line)
    if h:
        return f"<b>{inline_html(h.group(1))}</b>"
    v = video_line(line)
    if v:
        return f'<a href="{v[1]}" style="{LINK_STYLE}">{html.escape(v[0])}</a>'
    return inline_html(line)


def render_line_text(line):
    h = re.match(r"#{1,3}\s+(.*)", line)
    if h:
        return inline_text(h.group(1))
    v = video_line(line)
    if v:
        return f"{v[0]} {v[1]}"
    return inline_text(line)


def render(md, subject, preview):
    """Returns (html, plain_text)."""
    bs = blocks(md)
    body = "\n<br><br>\n".join("<br>\n".join(render_line_html(l) for l in b) for b in bs)
    page = open(TEMPLATE, encoding="utf-8").read()
    for k, v in {"SUBJECT": html.escape(subject), "PREHEADER": html.escape(preview),
                 "BODY": body}.items():
        page = page.replace("{{" + k + "}}", v)
    text = "\n\n".join("\n".join(render_line_text(l) for l in b) for b in bs)
    text += "\n\nsee you sunday\nHuzaifa\n\n--\nUnsubscribe: {$unsubscribe}\n"
    return page, text


# ---------- API ----------

def call(method, url, payload=None):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode() if payload is not None else None, method=method,
        headers={"Authorization": f"Bearer {os.environ['MAILERLITE_API_KEY']}",
                 "Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(body)
        except ValueError:
            return e.code, {"message": body[:500]}
    except urllib.error.URLError as e:
        return 0, {"message": str(e.reason)}


def send(name, subject, content_html, test_mode):
    """Create a campaign with content and send it instantly.
    Returns (campaign_id, error). error is None on success."""
    group_var = "MAILERLITE_TEST_GROUP_ID" if test_mode else "MAILERLITE_GROUP_ID"
    missing = [k for k in ("MAILERLITE_API_KEY", group_var, "MAILERLITE_FROM") if not os.environ.get(k)]
    if missing:
        return None, "missing env: " + ", ".join(missing)
    if not content_html.strip() or "{$unsubscribe}" not in content_html:
        return None, "content empty or missing unsubscribe link, refusing to send"

    payload = {"name": name, "type": "regular", "groups": [os.environ[group_var]],
               "emails": [{"subject": subject, "from_name": FROM_NAME,
                           "from": os.environ["MAILERLITE_FROM"],
                           "content": content_html}]}
    status, data = call("POST", API, payload)
    if not 200 <= status < 300:
        # Covers the plan restriction on content. No retry without content: never send empty.
        return None, f"create failed, HTTP {status}: {json.dumps(data)[:800]}"
    cid = (data.get("data") or {}).get("id")
    if not cid:
        return None, f"create returned no campaign id: {json.dumps(data)[:800]}"

    status, sched = call("POST", f"{API}/{cid}/schedule", {"delivery": "instant"})
    if not 200 <= status < 300:
        return cid, (f"campaign {cid} created but schedule failed (left as draft, not sent), "
                     f"HTTP {status}: {json.dumps(sched)[:800]}")
    return cid, None


# ---------- ledger ----------

def already_sent(date, test_mode):
    if not os.path.exists(LEDGER):
        return None
    for line in open(LEDGER, encoding="utf-8"):
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if (row.get("date") == date and row.get("sent") and row.get("campaign_id")
                and bool(row.get("test")) == test_mode):
            return row["campaign_id"]
    return None


def mark_sent(date, issue_no, cid, test_mode):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    row = {"date": date, "issue_no": issue_no, "sent": True, "campaign_id": cid, "test": test_mode,
           "sent_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


# ---------- modes ----------

def run_test():
    page, text = render("If you can read this line, **content via the API works** "
                        "and auto-send is good to go.", "API TEST", "API test")
    cid, err = send("API TEST", "API TEST", page, test_mode=True)
    print(f"NOT SENT — {err}" if err else f"SENT ✓ to test group — campaign {cid}")
    return 1 if err else 0


def run_sample(path):
    md = open(path, encoding="utf-8").read()
    subject = "Study the Game: The Brown M&Ms [DESIGN TEST]"
    page, text = render(md, subject, "Why Van Halen banned one color of candy, and 4 more ideas.")
    cid, err = send("DESIGN TEST — delete me", subject, page, test_mode=True)
    print(f"NOT SENT — {err}" if err else f"SENT ✓ to test group — campaign {cid}")
    return 1 if err else 0


def run_preview(path, out):
    page, text = render(open(path, encoding="utf-8").read(), "Preview", "Preview text")
    open(out + ".html", "w", encoding="utf-8").write(page)
    open(out + ".txt", "w", encoding="utf-8").write(text)
    print(f"wrote {out}.html and {out}.txt")
    return 0


def field(text, label):
    m = re.search(rf"^{label}:\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else ""


def append_result(line):
    os.makedirs(os.path.dirname(RESULT), exist_ok=True)
    with open(RESULT, "a", encoding="utf-8") as f:
        f.write(f"\n---\n{line}\n")
    print(line)


def run_issue(path):
    test_mode = os.environ.get("TEST_MODE", "").lower() == "true"
    label = "Test group (TEST MODE)" if test_mode else "Study the Game group"
    m = re.search(r"(\d{4}-\d{2}-\d{2})", path)
    if not m:
        append_result(f"NOT SENT — can't read a date from {path}")
        return 1
    date = m.group(1)

    prior = already_sent(date, test_mode)
    if prior:
        append_result(f"NOT SENT — {date} already sent to {label} (campaign {prior}). Skipped duplicate.")
        return 0

    md = open(path, encoding="utf-8").read()
    result = open(RESULT, encoding="utf-8").read() if os.path.exists(RESULT) else ""
    subject, preview = field(result, "Subject"), field(result, "Preview")
    if not subject:
        append_result("NOT SENT — no Subject line in _run/draft-result.md")
        return 1
    n = re.search(r"#(\d+)", md.splitlines()[0] if md.strip() else "")
    issue_no = n.group(1) if n else ""
    name = f"Study the Game #{issue_no}" if issue_no else f"Study the Game {date}"
    if test_mode:
        name += " [TEST]"

    page, text = render(md, subject, preview)
    cid, err = send(name, subject, page, test_mode)
    if err:
        append_result(f"NOT SENT — {err}")
        return 1
    mark_sent(date, issue_no, cid, test_mode)
    append_result(f"SENT ✓ to {label} — campaign {cid}")
    return 0


if __name__ == "__main__":
    load_env()
    args = sys.argv[1:]
    if args == ["--test"]:
        sys.exit(run_test())
    if len(args) == 2 and args[0] == "--sample":
        sys.exit(run_sample(args[1]))
    if len(args) == 3 and args[0] == "--preview":
        sys.exit(run_preview(args[1], args[2]))
    if len(args) == 1 and not args[0].startswith("--"):
        sys.exit(run_issue(args[0]))
    print(__doc__)
    sys.exit(2)
