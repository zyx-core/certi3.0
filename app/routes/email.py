from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
import tempfile
import shutil
import json

from app.utils.certificate_generator import generate_certificates_only, send_certificates_only

router = APIRouter()

# 🔧 Generate Only
@router.post("/generate-certificates")
async def generate_only(
    excel_file: UploadFile = File(...),
    template_file: UploadFile = File(...),
    placeholders: str = Form(...)
):
    try:
        placeholder_dict = json.loads(placeholders)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_excel:
            shutil.copyfileobj(excel_file.file, tmp_excel)
            excel_path = tmp_excel.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_template:
            shutil.copyfileobj(template_file.file, tmp_template)
            template_path = tmp_template.name

        df = pd.read_excel(excel_path)
        data = df.to_dict(orient="records")

        errors = generate_certificates_only(data, template_path, placeholder_dict)

        if errors:
            return JSONResponse(status_code=207, content={"message": "Some certificates failed", "errors": errors})
        return {"message": "Certificates generated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from app.utils.certificate_generator import send_certificates_only

@router.post("/send-certificates")
async def send_emails(
    excel_file: UploadFile = File(...)
):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_excel:
            shutil.copyfileobj(excel_file.file, tmp_excel)
            excel_path = tmp_excel.name

        df = pd.read_excel(excel_path)
        data = df.to_dict(orient="records")

        errors = send_certificates_only(data)

        if errors:
            return JSONResponse(status_code=207, content={"message": "Some emails failed", "errors": errors})
        return {"message": "All certificates sent successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-preview")
async def generate_preview(
    template_file: UploadFile = File(...),
    placeholders: str = Form(...)
):
    try:
        placeholder_dict = json.loads(placeholders)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_template:
            shutil.copyfileobj(template_file.file, tmp_template)
            template_path = tmp_template.name

        preview_path = generate_preview_image(template_path, placeholder_dict)

        return {"preview_path": preview_path}  # You can use FileResponse if you want to send the image file
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
