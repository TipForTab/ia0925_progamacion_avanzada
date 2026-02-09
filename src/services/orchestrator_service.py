import uuid
from src.services.extraction_client import ExtractionClient
from src.services.califier_client import CalifierClient
from src.services.jobs_store import jobs_store

class OrchestratorService:
    def create_job_id(self) -> str:
        return str(uuid.uuid4())

    async def run_pipeline(self, job_id: str, text: str) -> None:
        """
        Pipeline:
        1) Extract -> data-extraction-service
        2) Rank -> internal ranking stub
        3) (future) dispatch to destinations
        4) store result
        """
        jobs_store.set_status(job_id, "RUNNING")

        try:
            extraction = ExtractionClient()
            extracted_data = await extraction.extract(text)

            califier = CalifierClient()
            calified = await califier.califier(extracted_data)

            # FUTURO:
            # - ranked debería traer destinations
            # - aquí llamarías a otros microservicios según destinations
            # await self.dispatch(ranked)

            jobs_store.set_result(job_id, calified)

        except Exception as e:
            jobs_store.set_error(job_id, str(e))