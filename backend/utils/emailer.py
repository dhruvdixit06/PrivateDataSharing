from backend.config import settings

def send_email(to_email: str, subject: str, body: str):
    print(f"""
=== MOCK EMAIL SENT ===
From: {settings.EMAIL_FROM}
To: {to_email}
Subject: {subject}
Body:
{body}
========================
""")
