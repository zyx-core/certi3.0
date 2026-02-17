import smtplib
from email.message import EmailMessage

msg = EmailMessage()
msg["From"] = "ershadpersonal123@gmail.com"
msg["To"] = "test@example.com"
msg["Subject"] = "Test"
msg.set_content("Test email")

try:
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login("ershadpersonal123@gmail.com", "yxrj aizo rnhz xiza")
        print("SUCCESS: Login successful!")
except Exception as e:
    print(f"ERROR: {e}")
