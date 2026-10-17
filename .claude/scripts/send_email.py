#!/usr/bin/env python3
"""Send a markdown file as an HTML email via Gmail.
Usage: python3 send_email.py "Subject line" path/to/file.md
       python3 send_email.py "Subject line" path/to/file.md --preview out.html
If the file has an "If you read nothing else" summary blockquote, the subject
becomes "World Intel · <Day Mon D> · <first label>" and the summary labels
become the inbox preview text. Otherwise the subject passed in is used as is.
--preview writes the HTML to a file and prints the subject instead of sending.
"""
import os, re, smtplib, sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
from pathlib import Path

import markdown

STYLE = "font-family:-apple-system,Helvetica,sans-serif;font-size:15px;line-height:1.5;max-width:680px"


def summary_labels(text):
    """Bold labels from the 'If you read nothing else' blockquote, if present."""
    block = re.search(r"^>.*If you read nothing else.*?(?=^(?!>)|\Z)", text, re.M | re.S | re.I)
    if not block:
        return []
    return re.findall(r"^>\s*\d+\.\s+\*\*(.+?)\*\*", block.group(0), re.M)[:3]


def to_html(body, labels):
    html = markdown.markdown(body, extensions=["nl2br", "sane_lists"])
    preheader = ""
    if labels:
        padding = "&#847;&zwnj;&nbsp;" * 100  # keeps body text out of the inbox preview
        preheader = (
            '<div style="display:none;font-size:1px;line-height:1px;max-height:0;max-width:0;'
            'opacity:0;overflow:hidden;mso-hide:all;color:transparent">'
            f'{escape(" · ".join(labels))}{padding}</div>'
        )
    return f'{preheader}<div style="{STYLE}">{html}</div>'


env = dict(os.environ)  # GitHub Actions secrets arrive here
env_file = Path(__file__).parent / ".env"  # optional, local testing only
for line in (env_file.read_text().splitlines() if env_file.exists() else []):
    if "=" in line and not line.strip().startswith("#"):
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()

subject, path = sys.argv[1], Path(sys.argv[2])
preview = sys.argv[4] if len(sys.argv) > 4 and sys.argv[3] == "--preview" else None
body = path.read_text(errors="replace")[-200000:]

labels = summary_labels(body)
if labels:
    now = datetime.now()
    subject = f"World Intel · {now:%a %b} {now.day} · {labels[0]}"
html = to_html(body, labels)

if preview:
    Path(preview).write_text(html)
    print(f"subject: {subject}")
    print(f"preheader: {' · '.join(labels) or '(none)'}")
    print(f"wrote: {preview}")
    sys.exit()

msg = MIMEMultipart("alternative")
msg["Subject"] = subject
msg["From"] = env["GMAIL_USER"]
msg["To"] = env["EMAIL_TO"]
msg.attach(MIMEText(body, "plain"))
msg.attach(MIMEText(html, "html"))

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login(env["GMAIL_USER"], env["GMAIL_APP_PASSWORD"])
    server.send_message(msg)
print(f"sent: {subject}")
