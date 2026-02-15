from PIL import Image, ImageDraw, ImageFont
import os, zipfile
from app.utils.email_utils import send_email

def generate_certificates(data, template_path, config):
    output_dir = "generated_certificates"
    os.makedirs(output_dir, exist_ok=True)

    template = Image.open(template_path)

    # Example font config in JSON:
    # {
    #   "name": {"x": 500, "y": 500, "font_size": 60},
    #   "score": {"x": 500, "y": 600, "font_size": 40}
    # }

    for row in data:
        cert = template.copy()
        draw = ImageDraw.Draw(cert)

        for field, settings in config.items():
            value = str(row.get(field, ""))
            x = settings.get("x", 0)
            y = settings.get("y", 0)
            font_size = settings.get("font_size", 40)
            font = ImageFont.truetype("arial.ttf", font_size)

            draw.text((x, y), value, fill="black", font=font)

        name = row.get("name", "certificate")
        cert_path = os.path.join(output_dir, f"{name}.png")
        cert.save(cert_path)

        # Optional: Emailing the certificate
        email = row.get("email")
        if email:
            subject = "Your Certificate"
            content = f"Hi {name},\n\nHere is your certificate!"
            try:
                send_email(to_email=email, subject=subject, content=content, attachment_path=cert_path)
                print(f"✔️ Sent to {email}")
            except Exception as e:
                print(f"❌ Error sending to {email}: {e}")

    # Zip all certificates
    zip_path = "certificates.zip"
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for filename in os.listdir(output_dir):
            file_path = os.path.join(output_dir, filename)
            if os.path.isfile(file_path):
                zipf.write(file_path, arcname=filename)

    return zip_path
