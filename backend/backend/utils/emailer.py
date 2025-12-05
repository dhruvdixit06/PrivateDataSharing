from backend.config import settings
def send_email(to_email: str, subject: str, body: str):
    print(f"MOCK EMAIL -> To: {to_email}\nSubject: {subject}\n{body}\n----")
