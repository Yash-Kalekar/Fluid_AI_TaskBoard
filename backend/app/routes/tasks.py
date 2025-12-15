from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from ..models import ErrorResponse, Task, TaskCreate, TaskPatch, TaskResponse, StorageMeta
from ..storage import TaskStorage


def _title_is_valid(title: str) -> bool:
    return len((title or "").strip()) >= 3


def build_tasks_router(storage: TaskStorage) -> APIRouter:
    router = APIRouter(prefix="/tasks", tags=["tasks"])

    @router.get("", response_model=list[Task])
    async def list_tasks():
        return await storage.list_tasks()

    @router.post(
        "",
        response_model=TaskResponse,
        status_code=status.HTTP_201_CREATED,
        responses={
            422: {"model": ErrorResponse},
        },
    )
    async def create_task(payload: TaskCreate):
        if not _title_is_valid(payload.title):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Title must be at least 3 characters.",
            )
        task, meta = await storage.add_task(payload.title)
        return TaskResponse(task=task, meta=StorageMeta(saved_at=meta.saved_at, count=meta.count))

    @router.patch(
        "/{task_id}",
        response_model=TaskResponse,
        responses={
            404: {"model": ErrorResponse},
        },
    )
    async def patch_task(task_id: str, payload: TaskPatch):
        updated = await storage.set_completed(task_id, payload.completed)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        task, meta = updated
        return TaskResponse(task=task, meta=StorageMeta(saved_at=meta.saved_at, count=meta.count))

    @router.delete(
        "/{task_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            404: {"model": ErrorResponse},
        },
    )
    async def delete_task(task_id: str):
        meta = await storage.delete_task(task_id)
        if not meta:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
        return None

    return router
