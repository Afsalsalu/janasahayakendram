import os
import smtplib

def test_smtp_connection():
    try:
        server = smtplib.SMTP(os.getenv("EMAIL_HOST"), int(os.getenv("EMAIL_PORT", "587")))
        server.ehlo()
        server.starttls()
        server.login(os.getenv("EMAIL_HOST_USER"), os.getenv("EMAIL_HOST_PASSWORD"))
        print("SMTP connection successful")
        server.quit()
    except Exception as e:
        print(f"SMTP connection error: {e}")

if __name__ == "__main__":
    test_smtp_connection()


