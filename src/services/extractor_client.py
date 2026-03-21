import httpx
from src.conf import settings
from src.models.extract import ModelOutput

class ExtractorClient:
    async def extract(self, text: str) -> ModelOutput:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(f"{settings.data_extraction_url}/extract", json={"text": text})
            r.raise_for_status()

            data = r.json()
            # Validación fuerte: asegura que lo recibido cumple ModelOutput
            return ModelOutput.model_validate(data)