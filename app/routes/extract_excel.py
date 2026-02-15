from fastapi import APIRouter, UploadFile, File
from app.utils.excel_reader import extract_excel_headers
import os, shutil

router = APIRouter()

@router.post("/extract/excel-headers")
async def extract_excel_headers_route(excel_file: UploadFile = File(...)):
    os.makedirs("temp", exist_ok=True)
    file_path = f"temp/{excel_file.filename}"
    with open(file_path, "wb") as f:
        shutil.copyfileobj(excel_file.file, f)

    headers = extract_excel_headers(file_path)
    return {"headers": headers}
