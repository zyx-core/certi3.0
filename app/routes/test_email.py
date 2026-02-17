from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import smtplib
import os
from email.message import EmailMessage
import traceback

router = APIRouter()

class TestEmailRequest(BaseModel):
    recipient: str

@router.post("/test-email")
async def test_email(request: TestEmailRequest):
    """Test email sending with detailed diagnostics"""
    
    smtp_host = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 465))
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SMTP_PASSWORD")
    
    diagnostics = {
        "smtp_host": smtp_host,
        "smtp_port": smtp_port,
        "sender_email": sender_email,
        "password_set": bool(sender_password),
        "password_length": len(sender_password) if sender_password else 0,
    }
    
    # Check if all credentials are set
    if not all([smtp_host, sender_email, sender_password]):
        return {
            "success": False,
            "error": "Missing environment variables",
            "diagnostics": diagnostics
        }
    
    try:
        # Create test message
        msg = EmailMessage()
        msg["From"] = sender_email
        msg["To"] = request.recipient
        msg["Subject"] = "Test Email from Render"
        msg.set_content("This is a test email sent from your deployed app on Render.")
        
        # Try to send
        with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        return {
            "success": True,
            "message": f"Test email sent successfully to {request.recipient}",
            "diagnostics": diagnostics
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc(),
            "diagnostics": diagnostics
        }
