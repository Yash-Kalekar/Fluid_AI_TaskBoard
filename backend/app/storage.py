from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from .models import Task


def _utcnow() -> datetime:
    return datetime.utcnow()


def _task_from_dict(raw: dict) -> Task:
    # Pydantic will parse ISO datetime strings automatically
    return Task(**raw)


def _task_to_dict(task: Task) -> dict:
    d = task.model_dump()
    d["created_at"] = task.created_at.isoformat()
    d["updated_at"] = task.updated_at.isoformat()
    return d


@dataclass
class SaveResult:
    saved_at: datetime
    count: int


class TaskStorage:
    """Simple JSON-file-backed storage.

    - Loads tasks into memory on startup.
    - Writes the full list back to disk on each mutation.
    """

    def __init__(self, file_path: Path):
        self._file_path = file_path
        self._lock = asyncio.Lock()
        self._tasks_by_id: Dict[str, Task] = {}

    async def init(self) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._file_path.exists():
            self._file_path.write_text(json.dumps({"tasks": []}, indent=2), encoding="utf-8")

        raw = json.loads(self._file_path.read_text(encoding="utf-8") or "{}")
        tasks = raw.get("tasks", [])
        for t in tasks:
            task = _task_from_dict(t)
            self._tasks_by_id[task.id] = task

    async def list_tasks(self) -> List[Task]:
        async with self._lock:
            return sorted(
                list(self._tasks_by_id.values()),
                key=lambda x: x.created_at,
                reverse=False,
            )

    async def add_task(self, title: str) -> tuple[Task, SaveResult]:
        title = (title or "").strip()
        now = _utcnow()
        task = Task(id=str(uuid4()), title=title, completed=False, created_at=now, updated_at=now)

        async with self._lock:
            self._tasks_by_id[task.id] = task
            meta = await self._save_locked()
            return task, meta

    async def set_completed(self, task_id: str, completed: bool) -> Optional[tuple[Task, SaveResult]]:
        async with self._lock:
            task = self._tasks_by_id.get(task_id)
            if not task:
                return None
            task.completed = bool(completed)
            task.updated_at = _utcnow()
            self._tasks_by_id[task_id] = task
            meta = await self._save_locked()
            return task, meta

    async def delete_task(self, task_id: str) -> Optional[SaveResult]:
        async with self._lock:
            if task_id not in self._tasks_by_id:
                return None
            self._tasks_by_id.pop(task_id, None)
            meta = await self._save_locked()
            return meta

    async def _save_locked(self) -> SaveResult:
        saved_at = _utcnow()
        payload = {"tasks": [_task_to_dict(t) for t in self._tasks_by_id.values()], "saved_at": saved_at.isoformat()}
        self._file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return SaveResult(saved_at=saved_at, count=len(self._tasks_by_id))
