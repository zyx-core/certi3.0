from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import smtplib
import os
from email.message import EmailMessage
import traceback

router = APIRouter()

class TestEmailRequest(BaseModel):
    recipient: str

import resend

@router.post("/test-email")
async def test_email(request: TestEmailRequest):
    """Test email sending with detailed diagnostics for Resend"""
    
    resend_api_key = os.getenv("RESEND_API_KEY")
    sender_email = os.getenv("SENDER_EMAIL", "onboarding@resend.dev")
    
    diagnostics = {
        "api_key_set": bool(resend_api_key),
        "api_key_length": len(resend_api_key) if resend_api_key else 0,
        "sender_email": sender_email,
    }
    
    if not resend_api_key:
        return {
            "success": False,
            "error": "Missing RESEND_API_KEY environment variable",
            "diagnostics": diagnostics
        }
    
    try:
        resend.api_key = resend_api_key
        
        params = {
            "from": sender_email,
            "to": [request.recipient],
            "subject": "Resend API Test from Render",
            "text": "This is a test email sent using the Resend API from your deployed app on Render."
        }
        
        resend.Emails.send(params)
        
        return {
            "success": True,
            "message": f"Resend API test successful! Email queued for {request.recipient}",
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
