from fastapi import APIRouter, status

router = APIRouter(prefix="/internal", tags=["Internal - Ranking"])

@router.post("/rank", status_code=status.HTTP_200_OK)
async def rank_stub(payload: dict):
    """
    STUB / NO-OP:
    - En el futuro aquí se decide a qué microservicios destino se envía.
    - Por ahora devolvemos el mismo payload envuelto.
    """
    return {
        "ranked": True,
        "destinations": [],  # futuro: ["search-service", "analytics-service", ...]
        "payload": payload,
    }
