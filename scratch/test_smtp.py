import smtplib
import os
import sys
from dotenv import load_dotenv

def test_smtp():
    load_dotenv()
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT", 587)
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")

    print(f"Server: {smtp_server}:{smtp_port}")
    print(f"Username: {smtp_username}")
    print(f"Password length: {len(smtp_password) if smtp_password else 0}")

    if not all([smtp_server, smtp_username, smtp_password]):
        print("Missing credentials.")
        return

    try:
        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.quit()
        print("SMTP Connection Successful!")
    except Exception as e:
        print(f"SMTP Error: {type(e).__name__} - {str(e)}")

if __name__ == "__main__":
    test_smtp()
