import imaplib
import email
from email.header import decode_header
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

IMAP_SERVER = os.getenv("IMAP_SERVER")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")


def clean_text(text):
    if isinstance(text, bytes):
        return text.decode(errors="ignore")
    return text


def decode_mime_header(value):
    if not value:
        return ""

    parts = []
    for part, encoding in decode_header(value):
        if isinstance(part, bytes):
            parts.append(part.decode(encoding or "utf-8", errors="ignore"))
        else:
            parts.append(part)
    return "".join(parts)


def get_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if content_type == "text/plain" and "attachment" not in content_disposition:
                return clean_text(part.get_payload(decode=True))
    else:
        return clean_text(msg.get_payload(decode=True))

    return ""


def fetch_emails(limit=10):
    missing = [k for k, v in {
        "IMAP_SERVER": IMAP_SERVER,
        "EMAIL_USER": EMAIL_USER,
        "EMAIL_PASS": EMAIL_PASS,
    }.items() if not v]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_USER, EMAIL_PASS)

    mail.select("inbox")

    status, messages = mail.search(None, "ALL")
    email_ids = messages[0].split()

    latest_ids = email_ids[-limit:]

    results = []

    for eid in reversed(latest_ids):
        _, msg_data = mail.fetch(eid, "(RFC822)")
        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)

        subject = decode_mime_header(msg.get("Subject"))

        from_ = clean_text(msg.get("From"))
        date_ = clean_text(msg.get("Date"))
        body = get_body(msg)

        results.append({
            "sender": from_,
            "subject": subject,
            "date": date_,
            "body": body.strip()
        })

    mail.logout()
    return results


def save_emails_to_json(emails, output_dir="json"):
    base_dir = os.path.dirname(__file__)
    target_dir = os.path.join(base_dir, output_dir)
    os.makedirs(target_dir, exist_ok=True)

    filename = f"emails_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_path = os.path.join(target_dir, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(emails, f, ensure_ascii=False, indent=2)

    return output_path


if __name__ == "__main__":
    emails = fetch_emails(10)
    output_file = save_emails_to_json(emails)

    print("\nLast 10 email subjects:\n")
    for e in emails:
        print(f"- {e['subject']}")
    print(f"\nSaved {len(emails)} emails to: {output_file}")
