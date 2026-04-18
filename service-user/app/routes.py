from fastapi import APIRouter, UploadFile, File
from app.config import STORAGE_TYPE
from app.storage.minio_client import MinioClient
from app.storage.gcs_client import GCSClient

router = APIRouter()

def get_storage():
    return MinioClient() if STORAGE_TYPE == "minio" else GCSClient()

@router.post("/submit")
async def submit_assignment(file: UploadFile = File(...)):
    data = await file.read()
    storage = get_storage()
    storage.upload_file(file.filename, data)
    return {"message": "File uploaded"}