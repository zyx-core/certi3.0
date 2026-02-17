from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import base64, tempfile
import pandas as pd
from app.utils.certificate_generator import generate_certificates_only, send_certificates_only
from fastapi.responses import FileResponse

router = APIRouter()

# --- UPDATED: Add 'font' and 'uppercase' properties ---
class PlaceholderProperties(BaseModel):
    x: float
    y: float
    font_size: float
    color: str
    bold: bool
    italic: Optional[bool] = False
    underline: Optional[bool] = False
    strikethrough: Optional[bool] = False
    font: str = "Poppins"  # Default font
    uppercase: Optional[bool] = False  # New: text transformation

# --- FIXED: Added missing fields ---
class CertificateData(BaseModel):
    placeholders: Dict[str, PlaceholderProperties]
    excel_data: List[Dict[str, str]]
    template_bytes: str
    email_column: Optional[str] = None  # Add this field
    subject: Optional[str] = "Your Certificate"  # Add this field
    content: Optional[str] = "Please find your certificate attached."  # Add this field

@router.post("/generate-and-send-uploaded")
async def generate_and_send_uploaded(data: CertificateData):
    try:
        # Validate required fields for sending emails
        if not data.email_column:
            raise HTTPException(status_code=400, detail="email_column is required for sending certificates")
        
        image_data = base64.b64decode(data.template_bytes)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_template:
            tmp_template.write(image_data)
            template_path = tmp_template.name

        records = data.excel_data
        
        # Generate certificates first (no streaming here)
        errors_gen = generate_certificates_only(
            data_list=records, 
            template_path=template_path, 
            placeholders=data.placeholders
        )
        
        # Stream email sending progress
        def event_stream():
            for event in send_certificates_only(
                data_list=records,
                email_column_name=data.email_column,
                subject=data.subject,
                content=data.content
            ):
                yield event
        
        from fastapi.responses import StreamingResponse
        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except Exception as e:
        import traceback
        print("Exception in /generate-and-send-uploaded:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-preview")
async def generate_live_preview(data: CertificateData):
    try:
        image_data = base64.b64decode(data.template_bytes)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_template:
            tmp_template.write(image_data)
            template_path = tmp_template.name

        preview_data_row = data.excel_data[0] if data.excel_data else {}

        preview_image_path = generate_certificates_only(
            data_list=[preview_data_row], 
            template_path=template_path, 
            placeholders=data.placeholders,
            is_preview=True
        )
        
        if not preview_image_path:
             raise HTTPException(status_code=500, detail="Preview generation failed.")

        return FileResponse(preview_image_path)

    except Exception as e:
        import traceback
        print(f"Exception in /generate-preview: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))