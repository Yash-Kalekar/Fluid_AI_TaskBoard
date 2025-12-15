from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.routes.tasks import build_tasks_router
from app.storage import TaskStorage


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

DATA_DIR = ROOT_DIR / "data"
TASKS_FILE = DATA_DIR / "tasks.json"

# App
app = FastAPI(title="Task Board API")
api_router = APIRouter(prefix="/api")

# Storage (JSON file)
storage = TaskStorage(TASKS_FILE)


@api_router.get("/")
async def root():
    return {"message": "Task Board API"}


@api_router.get("/health")
async def health():
    return {"ok": True}


api_router.include_router(build_tasks_router(storage))
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("task-board")


@app.on_event("startup")
async def _startup():
    await storage.init()
    logger.info("Task storage initialized at %s", TASKS_FILE)


@app.on_event("shutdown")
async def _shutdown():
    logger.info("Shutting down Task Board API")
