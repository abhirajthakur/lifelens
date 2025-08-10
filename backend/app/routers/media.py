from fastapi import APIRouter, UploadFile

router = APIRouter(prefix="/api/upload")

@router.post("/")
async def upload_file(file: UploadFile):
    return {"filename": file.filename}
