from fastapi import APIRouter, HTTPException, status
from src.services.jobs_store import jobs_store

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.get("/{job_id}", status_code=status.HTTP_200_OK)
async def get_job(job_id: str):
    rec = jobs_store.get(job_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": rec.job_id,
        "status": rec.status,
        "created_at": rec.created_at,
        "updated_at": rec.updated_at,
        "result": rec.result,
        "error": rec.error,
    }
