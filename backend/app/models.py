from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict


class Task(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    completed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TaskCreate(BaseModel):
    title: str


class TaskPatch(BaseModel):
    completed: bool


class ErrorResponse(BaseModel):
    detail: str


class TasksList(BaseModel):
    items: list[Task]


class StorageMeta(BaseModel):
    saved_at: datetime
    count: int


class TaskResponse(BaseModel):
    task: Task
    meta: Optional[StorageMeta] = None
