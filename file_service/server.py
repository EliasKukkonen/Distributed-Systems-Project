import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from pymongo import MongoClient
from datetime import datetime
import config
import uuid

app = FastAPI()

client = MongoClient(config.MONGO_URI)
db = client[config.DB_NAME]
files_collection = db[config.COLLECTION_NAME]

if not os.path.exists(config.UPLOAD_DIR):
    os.makedirs(config.UPLOAD_DIR)

@app.post("/files/upload")
async def upload_file(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{file_id}{file_extension}"
    file_path = os.path.join(config.UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    file_metadata = {
        "_id": file_id,
        "filename": file.filename,
        "filepath": file_path,
        "upload_time": datetime.utcnow()
    }
    files_collection.insert_one(file_metadata)

    return {"file_id": file_id, "filename": file.filename}

@app.get("/files/{file_id}/download")
async def download_file(file_id: str):
    file_metadata = files_collection.find_one({"_id": file_id})
    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = file_metadata["filepath"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(
        path=file_path,
        filename=file_metadata["filename"],
        media_type="application/octet-stream"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=50053)