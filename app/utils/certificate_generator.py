from PIL import Image, ImageDraw, ImageFont
from email.message import EmailMessage
import smtplib
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import threading

load_dotenv()
print("[OK] certificate_generator module loaded")

OUTPUT_DIR = "generated_certificates"
os.makedirs(OUTPUT_DIR, exist_ok=True)

FONT_MAP = {
    "Roboto": {"regular": "Poppins-Regular.ttf", "bold": "Poppins-Black.ttf"},
    "Arimo": {"regular": "Poppins-Regular.ttf", "bold": "Poppins-Black.ttf"},
    "Tinos": {"regular": "Poppins-Regular.ttf", "bold": "Poppins-Black.ttf"},
    "Poppins": {"regular": "Poppins-Regular.ttf", "bold": "Poppins-Black.ttf"},
}

def get_font(font_name: str, is_bold: bool, font_size: int) -> ImageFont.FreeTypeFont:
    style = "bold" if is_bold else "regular"
    font_file = FONT_MAP.get(font_name, FONT_MAP["Roboto"]).get(style, FONT_MAP["Roboto"]["regular"])
    font_path = os.path.join("fonts", font_file)
    try:
        return ImageFont.truetype(font_path, font_size)
    except IOError:
        print(f"[WARN] Font file not found at '{font_path}'. Using default font.")
        return ImageFont.load_default()

def draw_certificate(template_path: str, output_path: str, data: dict, placeholders):
    """Draw text on the certificate template using settings from the frontend."""
    cert = Image.open(template_path).convert("RGB")
    draw = ImageDraw.Draw(cert)
    img_width, img_height = cert.size
    
    for field, settings in placeholders.items():
        value = str(data.get(field, field))
        font_size = int(settings.font_size)
        font_name = settings.font
        bold = settings.bold
        x, y = settings.x, settings.y
        color = settings.color
        
        font = get_font(font_name, bold, font_size)
        
        text_bbox = draw.textbbox((0, 0), value, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        
        max_width = img_width * 0.9
        if text_width > max_width:
            scale_factor = max_width / text_width
            new_font_size = int(font_size * scale_factor)
            font = get_font(font_name, bold, new_font_size)
        
        draw.text((x, y), value, fill=color, font=font, anchor="la")

    cert.save(output_path)
    print(f"[SAVE] Certificate saved: {output_path}")

def generate_certificates_only(data_list, template_path, placeholders, is_preview: bool = False):
    """Generate certificates with manually defined font sizes from the frontend."""
    errors = []
    generated_path = None
    
    for row in data_list:
        try:
            name = row.get("Name", "Unnamed")
            file_name = f"{name}_preview.png" if is_preview else f"{name}.png"
            cert_path = os.path.join(OUTPUT_DIR, file_name)
            
            draw_certificate(template_path, cert_path, row, placeholders)

            if is_preview:
                generated_path = cert_path
                break
        except Exception as e:
            print(f"[ERROR] generating for {row.get('Name', 'Unknown')}: {e}")
            errors.append(f"{row.get('Name', 'Unknown')}: {str(e)}")
            
    return generated_path if is_preview else errors

import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# ... (Previous code remains, but send_certificates_only changes) ...

def send_single_email(smtp_host, smtp_port, sender_email, sender_password, row, email_column_name, subject, content):
    """Sends a single email and returns a status dict."""
    name = row.get("Name", "Unnamed")
    email = row.get(email_column_name)

    if not email:
        return {"success": False, "message": f"❌ Email not found for {name}"}

    try:
        cert_path = os.path.join(OUTPUT_DIR, f"{name}.png")
        if not os.path.exists(cert_path):
            return {"success": False, "message": f"❌ Certificate not found for {name}"}

        msg = EmailMessage()
        msg["From"] = sender_email
        msg["To"] = email
        msg["Subject"] = subject
        personalized_content = content.replace("{Name}", name)
        msg.set_content(personalized_content)

        with open(cert_path, "rb") as f:
            msg.add_attachment(f.read(), maintype="image", subtype="png", filename=f"{name}.png")

        # Create a fresh connection for each thread to ensure thread safety or use a shared locked connection?
        # Creating fresh connection is safer but slower. 
        # For 'ThreadPoolExecutor', sharing a connection requires locking.
        # The previous implementation passed 'server' and 'lock'.
        # Let's try to connect per-email for simplicity if volume is low, OR use the passed server if we revert to the previous pattern.
        # Actually, let's stick to the previous pattern: pass the server and lock.
        # BUT, we can't easily pass the server object if we are using 'as_completed' strategy cleanly without complex partials.
        # Let's Refactor: We will use a shared connection with a lock.
        
        # WAIT: The previous implementation defined `send_single_email` INSIDE `send_certificates_only`.
        # I should keep it inside to capture `server` and `server_lock`.
        pass 
    except Exception as e:
        return {"success": False, "message": f"❌ Failed to send to {email}: {e}"}

def send_certificates_only(data_list, email_column_name, subject, content):
    """Yields SSE events for real-time frontend updates."""
    smtp_host = os.getenv("EMAIL_HOST")
    smtp_port = int(os.getenv("EMAIL_PORT", 587))
    sender_email = os.getenv("EMAIL_ADDRESS")
    sender_password = os.getenv("EMAIL_PASSWORD")

    if not all([smtp_host, sender_email, sender_password]):
        yield json.dumps({"type": "error", "message": "Email server not configured. Please check .env file."}) + "\n"
        return

    yield json.dumps({"type": "log", "message": f"Connecting to email server..."}) + "\n"

    success_count = 0
    error_count = 0
    total = len(data_list)
    
    server_lock = threading.Lock()

    # Inner function to access server/lock
    def _send_task(server, row):
        name = row.get("Name", "Unnamed")
        email = row.get(email_column_name)
        if not email:
            return {"success": False, "message": f"No email found for {name}"}
        
        try:
            cert_path = os.path.join(OUTPUT_DIR, f"{name}.png")
            if not os.path.exists(cert_path):
                return {"success": False, "message": f"Certificate missing for {name}"}

            msg = EmailMessage()
            msg["From"] = sender_email
            msg["To"] = email
            msg["Subject"] = subject
            msg.set_content(content.replace("{Name}", name))

            with open(cert_path, "rb") as f:
                msg.add_attachment(f.read(), maintype="image", subtype="png", filename=f"{name}.png")

            with server_lock:
                server.send_message(msg)
            
            return {"success": True, "message": f"Sent to {name} ({email})"}
        except Exception as e:
            return {"success": False, "message": f"Failed to send to {name}: {str(e)}"}

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            yield json.dumps({"type": "log", "message": "Connected! Starting to send emails..."}) + "\n"

            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(_send_task, server, row): row for row in data_list}
                
                for future in as_completed(futures):
                    result = future.result()
                    if result["success"]:
                        success_count += 1
                    else:
                        error_count += 1
                    
                    # Yield progress and log
                    yield json.dumps({
                        "type": "progress",
                        "sent": success_count,
                        "failed": error_count,
                        "total": total,
                        "log": result["message"]
                    }) + "\n"

        yield json.dumps({"type": "complete", "message": f"Done! Sent {success_count} emails successfully."}) + "\n"

    except Exception as e:
        yield json.dumps({"type": "error", "message": f"Email server error: {str(e)}"}) + "\n"