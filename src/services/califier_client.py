import httpx
from src.conf import settings

class CalifierClient:
    async def califier(self, extracted_data: dict) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                f"{settings.califier_url}/internal/califier",
                json=extracted_data,
            )
            r.raise_for_status()
            return r.json()