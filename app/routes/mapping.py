import os
import shutil
from fastapi import APIRouter, UploadFile, File
from app.utils.excel_reader import extract_excel_headers
from app.utils.ocr_parser import extract_placeholders_from_image

router = APIRouter()

@router.post("/mapping")
async def extract_mapping(
    excel_file: UploadFile = File(...),
    template_image: UploadFile = File(...)
):
    os.makedirs("temp", exist_ok=True)

    excel_path = f"temp/{excel_file.filename}"
    image_path = f"temp/{template_image.filename}"

    try:
        # Save files
        with open(excel_path, "wb") as f:
            shutil.copyfileobj(excel_file.file, f)

        with open(image_path, "wb") as f:
            shutil.copyfileobj(template_image.file, f)

        # Extract data
        headers = extract_excel_headers(excel_path)
        placeholders = extract_placeholders_from_image(image_path)

        return {
            "headers": headers,
            "placeholders": placeholders
        }

    finally:
        # Cleanup files even if an error occurs
        if os.path.exists(excel_path):
            os.remove(excel_path)
        if os.path.exists(image_path):
            os.remove(image_path)
