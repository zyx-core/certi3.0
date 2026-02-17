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
    "Poppins": {
        "regular": "Poppins-Regular.ttf",
        "bold": "Poppins-Bold.ttf",
        "italic": "Poppins-Italic.ttf",
        "bold_italic": "Poppins-BoldItalic.ttf",
        "light": "Poppins-Light.ttf",
        "medium": "Poppins-Medium.ttf",
        "semibold": "Poppins-SemiBold.ttf",
        "extrabold": "Poppins-ExtraBold.ttf"
    },
    "Roboto": {
        "regular": "Roboto-VariableFont_wdth,wght.ttf",
        "bold": "Roboto-VariableFont_wdth,wght.ttf",
        "italic": "Roboto-Italic-VariableFont_wdth,wght.ttf",
        "bold_italic": "Roboto-Italic-VariableFont_wdth,wght.ttf"
    },
    "Tinos": {
        "regular": "Tinos-Regular.ttf",
        "bold": "Tinos-Bold.ttf",
        "italic": "Tinos-Italic.ttf",
        "bold_italic": "Tinos-BoldItalic.ttf"
    },
    "Arimo": {
        "regular": "Arimo-VariableFont_wght.ttf",
        "bold": "Arimo-VariableFont_wght.ttf",
        "italic": "Arimo-Italic-VariableFont_wght.ttf",
        "bold_italic": "Arimo-Italic-VariableFont_wght.ttf"
    },
    "Manrope": {
        "regular": "Manrope-VariableFont_wght.ttf",
        "bold": "Manrope-VariableFont_wght.ttf",
        "italic": "Manrope-VariableFont_wght.ttf",
        "bold_italic": "Manrope-VariableFont_wght.ttf"
    }
}

def get_font(font_name: str, is_bold: bool, is_italic: bool, font_size: int) -> ImageFont.FreeTypeFont:
    if is_bold and is_italic:
        style = "bold_italic"
    elif is_bold:
        style = "bold"
    elif is_italic:
        style = "italic"
    else:
        style = "regular"
        
    font_file = FONT_MAP.get(font_name, FONT_MAP["Poppins"]).get(style, FONT_MAP["Poppins"]["regular"])
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
        
        # Apply uppercase transformation if enabled
        if getattr(settings, 'uppercase', False):
            value = value.upper()
        
        font_size = int(settings.font_size)
        font_name = settings.font
        bold = settings.bold
        is_italic = getattr(settings, 'italic', False)
        underline = getattr(settings, 'underline', False)
        strikethrough = getattr(settings, 'strikethrough', False)
        
        x, y = settings.x, settings.y
        color = settings.color
        
        # Convert hex color to RGB tuple if needed
        if isinstance(color, str) and color.startswith('#'):
            try:
                color = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
            except:
                color = "black"  # Fallback to black if conversion fails
        
        font = get_font(font_name, bold, is_italic, font_size)
        
        text_bbox = draw.textbbox((0, 0), value, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        
        max_width = img_width * 0.9
        if text_width > max_width:
            scale_factor = max_width / text_width
            new_font_size = int(font_size * scale_factor)
            font = get_font(font_name, bold, is_italic, new_font_size)
        
        draw.text((x, y), value, fill=color, font=font, anchor="la")
        
        # Draw Underline
        if underline:
            real_bbox = draw.textbbox((x, y), value, font=font, anchor="la")
            # Draw line at bottom (a bit loose heuristic)
            line_y = real_bbox[3] + (font_size * 0.05)
            line_width = max(1, int(font_size/15))
            draw.line([(real_bbox[0], line_y), (real_bbox[2], line_y)], fill=color, width=line_width)

        # Draw Strikethrough
        if strikethrough:
            real_bbox = draw.textbbox((x, y), value, font=font, anchor="la")
            # Middle of the text height
            line_y = (real_bbox[1] + real_bbox[3]) / 2
            line_width = max(1, int(font_size/15))
            draw.line([(real_bbox[0], line_y), (real_bbox[2], line_y)], fill=color, width=line_width)

    cert.save(output_path)
    print(f"[SAVE] Certificate saved: {output_path}")

def generate_certificates_only(data_list, template_path, placeholders, is_preview: bool = False):
    """Generate certificates with manually defined font sizes from the frontend."""
    errors = []
    generated_path = None
    
    for row in data_list:
        try:
            # Try to find name column (case-insensitive)
            name = None
            for key in row.keys():
                if key.lower() == 'name':
                    name = row[key]
                    break
            
            # If no name column found, use first column value
            if not name:
                name = str(list(row.values())[0]) if row else "Unnamed"
            
            if not name:
                name = "Unnamed"
                
            file_name = f"{name}_preview.png" if is_preview else f"{name}.png"
            cert_path = os.path.join(OUTPUT_DIR, file_name)
            
            draw_certificate(template_path, cert_path, row, placeholders)

            if is_preview:
                generated_path = cert_path
                break
        except Exception as e:
            # Get name for error message
            error_name = "Unknown"
            for key in row.keys():
                if key.lower() == 'name':
                    error_name = row[key]
                    break
            print(f"[ERROR] generating for {error_name}: {e}")
            errors.append(f"{error_name}: {str(e)}")
            
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
    smtp_host = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SMTP_PASSWORD")

    if not all([smtp_host, sender_email, sender_password]):
        yield json.dumps({"type": "error", "message": "Email server not configured. Please check .env file."}) + "\n"
        return

    yield json.dumps({"type": "log", "message": f"Connecting to email server..."}) + "\n"

    success_count = 0
    error_count = 0
    total = len(data_list)
    
    server_lock = threading.Lock()

    # Inner function to send email with its own SMTP connection
    def _send_task(row):
        # Try to find name column (case-insensitive)
        name = None
        for key in row.keys():
            if key.lower() == 'name':
                name = row[key]
                break
        
        # If no name column found, use first non-email column
        if not name:
            for key, value in row.items():
                if key != email_column_name and value:
                    name = str(value)
                    break
        
        if not name:
            name = "Unnamed"
        
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

            # Create a new SMTP_SSL connection for this thread (port 465)
            with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            return {"success": True, "message": f"Sent to {name} ({email})"}
        except Exception as e:
            return {"success": False, "message": f"Failed to send to {name}: {str(e)}"}

    try:
        yield json.dumps({"type": "log", "message": "Starting email sending process..."}) + "\n"

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(_send_task, row): row for row in data_list}
            
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
        yield json.dumps({"type": "error", "message": f"Email server error: {str(e)}"}) + "\n" + "\n"