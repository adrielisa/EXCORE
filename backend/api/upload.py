# backend/api/upload.py
from fastapi import APIRouter, UploadFile, File
from services.data_loader import load_excel_data
import shutil
import os

router = APIRouter()

@router.post("/upload-xlsx")
async def upload_xlsx(file: UploadFile = File(...)):
    """
    Endpoint to receive an Excel file, save it temporarily, and parse it.
    """
    os.makedirs("temp", exist_ok=True)
    file_path = f"temp/{file.filename}"

    # Save the uploaded file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Load and parse the Excel file
    try:
        data = load_excel_data(file_path)
        sheet_names = list(data.keys())
        return {"message": "File uploaded and parsed successfully", "sheets": sheet_names}
    except Exception as e:
        return {"error": str(e)}
