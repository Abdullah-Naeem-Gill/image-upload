import logging
from fastapi import FastAPI, Depends, HTTPException
from app.routers.upload import router as upload_router
from app.database import engine, init_db, SessionLocal
from app import models
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    try:
        await init_db()
        logger.info("Database initialized successfully.")
    except SQLAlchemyError as e:
        logger.error(f"Error initializing the database: {e}")
        raise HTTPException(status_code=500, detail="Error initializing the database")

async def get_db() -> AsyncSession:
    
    async with SessionLocal() as db:
        yield db

app.include_router(upload_router)

