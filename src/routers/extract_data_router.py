from fastapi import APIRouter, BackgroundTasks, status
from pydantic import BaseModel

from src.services.orchestrator_service import OrchestratorService
from src.services.jobs_store import jobs_store

router = APIRouter(prefix="/extract-data", tags=["Extract Data"])

class ExtractRequest(BaseModel):
    text: str

@router.post("/extract", status_code=status.HTTP_202_ACCEPTED)
async def extract_data_catalog(payload: ExtractRequest, background_tasks: BackgroundTasks):
    svc = OrchestratorService()
    job_id = svc.create_job_id()

    jobs_store.create(job_id)
    background_tasks.add_task(svc.run_pipeline, job_id, payload.text)

    return {"job_id": job_id, "status": "PENDING"}
