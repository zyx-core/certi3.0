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
from fastapi.responses import HTMLResponse

@router.get("/ui", response_class=HTMLResponse)
async def test_email_ui():
    """Serves a simple HTML UI to trigger the email test"""
    return """
    <html>
        <head>
            <title>Email Diagnostic Tool</title>
            <style>
                body { font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; line-height: 1.6; }
                pre { background: #f4f4f4; padding: 1rem; overflow-x: auto; border-radius: 4px; border: 1px solid #ddd; }
                .success { color: green; font-weight: bold; }
                .error { color: red; font-weight: bold; }
                input[type="email"] { padding: 0.5rem; width: 300px; margin-bottom: 1rem; }
                button { padding: 0.5rem 1rem; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
                button:hover { background: #0056b3; }
            </style>
        </head>
        <body>
            <h1>Email Diagnostic Tool</h1>
            <p>This tool test the email connection from the Render server.</p>
            <div>
                <input type="email" id="email" placeholder="Enter recipient email" value="ershadpersonal123@gmail.com">
                <button onclick="runTest()">Run Test</button>
            </div>
            <div id="status"></div>
            <h3>Result:</h3>
            <pre id="result">Click "Run Test" to start...</pre>

            <script>
                async function runTest() {
                    const email = document.getElementById('email').value;
                    const resultPre = document.getElementById('result');
                    const statusDiv = document.getElementById('status');
                    
                    if (!email) { alert('Please enter an email'); return; }
                    
                    statusDiv.innerHTML = '<b>Running test... please wait...</b>';
                    resultPre.textContent = 'Testing connection...';
                    
                    try {
                        const response = await fetch('/test/test-email', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ recipient: email })
                        });
                        const data = await response.json();
                        
                        statusDiv.innerHTML = data.success 
                            ? '<span class="success">✅ Test Successful!</span>' 
                            : '<span class="error">❌ Test Failed!</span>';
                        
                        resultPre.textContent = JSON.stringify(data, null, 2);
                    } catch (err) {
                        statusDiv.innerHTML = '<span class="error">❌ Request Failed!</span>';
                        resultPre.textContent = err.toString();
                    }
                }
            </script>
        </body>
    </html>
    """
