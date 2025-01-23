import os
import uuid
import logging
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv
import aiofiles  
from app.database import get_db
from app import models
from app.utils.file_utils import allowed_file, create_date_folder, generate_uuid, save_file

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

load_dotenv()

ALLOWED_EXTENSIONS = os.getenv("ALLOWED_IMAGE_EXTENSIONS", "jpg,png").split(',')

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent / "Data"
BASE_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload_image/")
async def upload_image(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    
    try:
        logger.info(f"Received file: {file.filename}")
        
        if not allowed_file(file.filename, ALLOWED_EXTENSIONS):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file extension. Allowed extensions are: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        unique_filename = generate_uuid() + "." + file.filename.split('.')[-1]
        logger.info(f"Generated unique filename: {unique_filename}")

        date_folder = create_date_folder(BASE_DIR)
        logger.info(f"Created folder: {date_folder}")

        file_location = date_folder / unique_filename
        logger.info(f"Saving file to: {file_location}")

        await save_file(file, file_location)
        logger.info(f"File saved successfully: {file_location}")

        image_metadata = models.Image(
            uuid=generate_uuid(),
            name=file.filename,
            size=os.path.getsize(file_location),
            extension=file.filename.split('.')[-1],
            path=str(file_location),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        db.add(image_metadata)
        await db.commit()
        await db.refresh(image_metadata)
        logger.info(f"Image metadata saved to DB: {image_metadata}")

        image_dict = image_metadata.dict()

        return JSONResponse(
            content={
                "message": "Image uploaded successfully",
                "file_path": str(file_location),
                "metadata": image_dict
            },
            status_code=200
        )

    except HTTPException as e:
        logger.error(f"HTTP error: {str(e)}")
        raise e  
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return JSONResponse(content={"message": "Failed to upload image", "error": str(e)}, status_code=500)
