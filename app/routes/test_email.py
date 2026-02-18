from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import smtplib
import os
from email.message import EmailMessage
import traceback

router = APIRouter()

class TestEmailRequest(BaseModel):
    recipient: str

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

@router.post("/test-email")
async def test_email(request: TestEmailRequest):
    """Test email sending with detailed diagnostics for Brevo"""
    
    brevo_api_key = os.getenv("BREVO_API_KEY")
    sender_email = os.getenv("SENDER_EMAIL")
    
    diagnostics = {
        "api_key_set": bool(brevo_api_key),
        "api_key_length": len(brevo_api_key) if brevo_api_key else 0,
        "sender_email": sender_email,
    }
    
    if not brevo_api_key:
        return {
            "success": False,
            "error": "Missing BREVO_API_KEY environment variable",
            "diagnostics": diagnostics
        }
    
    try:
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = brevo_api_key
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
        
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": request.recipient}],
            sender={"email": sender_email, "name": "Brevo Tester"},
            subject="Brevo API Test from Render",
            html_content="<html><body><h1>Test Successful</h1><p>Brevo is working correctly from Render!</p></body></html>"
        )
        
        api_instance.send_transac_email(send_smtp_email)
        
        return {
            "success": True,
            "message": f"Brevo API test successful! Email sent to {request.recipient}",
            "diagnostics": diagnostics
        }
    
    except ApiException as e:
        return {
            "success": False,
            "error": str(e.body),
            "error_type": "BrevoApiException",
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
            <title>Brevo Diagnostic Tool</title>
            <style>
                body { font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; line-height: 1.6; }
                pre { background: #f4f4f4; padding: 1rem; overflow-x: auto; border-radius: 4px; border: 1px solid #ddd; }
                .success { color: green; font-weight: bold; }
                .error { color: red; font-weight: bold; }
                input[type="email"] { padding: 0.5rem; width: 300px; margin-bottom: 1rem; }
                button { padding: 0.5rem 1rem; background: #008b5e; color: white; border: none; border-radius: 4px; cursor: pointer; }
                button:hover { background: #006b48; }
            </style>
        </head>
        <body>
            <h1>Brevo Diagnostic Tool</h1>
            <p>This tool test the Brevo API connection from the Render server.</p>
            <div>
                <input type="email" id="email" placeholder="Enter recipient email">
                <button onclick="runTest()">Run Test Email</button>
            </div>
            <div id="status"></div>
            <h3>Diagnostic Result:</h3>
            <pre id="result">Waiting for test...</pre>

            <script>
                async function runTest() {
                    const email = document.getElementById('email').value;
                    const resultPre = document.getElementById('result');
                    const statusDiv = document.getElementById('status');
                    
                    if (!email) { alert('Please enter a recipient email'); return; }
                    
                    statusDiv.innerHTML = '<b>Testing Brevo API...</b>';
                    resultPre.textContent = 'Sending request...';
                    
                    try {
                        const response = await fetch('/test/test-email', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ recipient: email })
                        });
                        const data = await response.json();
                        
                        statusDiv.innerHTML = data.success 
                            ? '<span class="success">✅ Brevo Test Successful!</span>' 
                            : '<span class="error">❌ Brevo Test Failed!</span>';
                        
                        resultPre.textContent = JSON.stringify(data, null, 2);
                    } catch (err) {
                        statusDiv.innerHTML = '<span class="error">❌ Connection Error!</span>';
                        resultPre.textContent = err.toString();
                    }
                }
            </script>
        </body>
    </html>
    """
