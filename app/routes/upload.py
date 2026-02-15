from fastapi import APIRouter, UploadFile, File
import os
import shutil

router = APIRouter()

# Absolute path to the "templates" folder inside the backend directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "..", "templates")
UPLOAD_DIR = os.path.abspath(UPLOAD_DIR)
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/excel")
async def upload_excel(file: UploadFile = File(...)):
    file_location = os.path.join(UPLOAD_DIR, "data.xlsx")
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"message": "Excel uploaded", "path": file_location}

@router.post("/template")
async def upload_template(file: UploadFile = File(...)):
    file_location = os.path.join(UPLOAD_DIR, "template.png")
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"message": "Template uploaded", "path": file_location}
