import httpx
from src.conf import settings

class ExtractionClient:
    async def extract(self, text: str) -> dict:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"{settings.data_extraction_url}/extract",
                json={"text": text},
            )
            r.raise_for_status()
            return r.json()