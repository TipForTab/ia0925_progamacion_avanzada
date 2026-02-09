# src/services/jobs_store.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional
import time

@dataclass
class JobRecord:
    job_id: str
    status: str  # PENDING, RUNNING, SUCCESS, FAILURE
    created_at: float
    updated_at: float
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class JobsStore:
    def __init__(self) -> None:
        self._jobs: Dict[str, JobRecord] = {}

    def create(self, job_id: str) -> JobRecord:
        now = time.time()
        rec = JobRecord(job_id=job_id, status="PENDING", created_at=now, updated_at=now)
        self._jobs[job_id] = rec
        return rec

    def set_status(self, job_id: str, status: str) -> None:
        rec = self._jobs[job_id]
        rec.status = status
        rec.updated_at = time.time()

    def set_result(self, job_id: str, result: Dict[str, Any]) -> None:
        rec = self._jobs[job_id]
        rec.result = result
        rec.status = "SUCCESS"
        rec.updated_at = time.time()

    def set_error(self, job_id: str, error: str) -> None:
        rec = self._jobs[job_id]
        rec.error = error
        rec.status = "FAILURE"
        rec.updated_at = time.time()

    def get(self, job_id: str) -> Optional[JobRecord]:
        return self._jobs.get(job_id)

# Instancia global simple (in-memory)
jobs_store = JobsStore()
