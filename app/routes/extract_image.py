from fastapi import APIRouter, UploadFile, File
from app.utils.ocr_parser import extract_placeholders_from_image
import os
import shutil

router = APIRouter()

@router.post("/extract/image-placeholders")
async def get_image_placeholders(template_image: UploadFile = File(...)):
    os.makedirs("temp", exist_ok=True)
    image_path = f"temp/{template_image.filename}"
    with open(image_path, "wb") as f:
        shutil.copyfileobj(template_image.file, f)

    placeholders = extract_placeholders_from_image(image_path)
    return {"placeholders": placeholders}
