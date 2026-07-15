import os
import shutil
import zipfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

WORKSPACE_DIR = "/Users/lilnhan/Documents/GitHub/god-3000/workspace/source"

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Endpoint to receive a single file or a zip file.
    It will extract it into the workspace/source directory.
    """
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    
    file_path = os.path.join(WORKSPACE_DIR, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        if file.filename.endswith(".zip"):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(WORKSPACE_DIR)
            os.remove(file_path)  # Clean up the zip file
            message = "Zip file extracted successfully."
        else:
            message = "File uploaded successfully."
            
        return JSONResponse(status_code=200, content={"message": message, "filename": file.filename})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
