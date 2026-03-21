from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Query, status, HTTPException, BackgroundTasks
from services.classifier_service import ClassifierService
from services.extractor_client import ExtractorClient
from src.models.extract import ModelOutput
from src.dependencies import get_current_user
from src.jobs.pipeline_jobs import PipelineJobs

router = APIRouter(
    prefix="/extract-data",
    tags=["Extract Data"]
)
@router.post("/extract", status_code=status.HTTP_200_OK)
async def extract_data(payload:ModelOutput, background_tasks: BackgroundTasks, user: str = Depends(get_current_user)):

    try:
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
        
        extractor_service = ExtractorClient()
        # Simulación de texto de entrada, en un caso real vendría del body de la petición
        user_input_text = """Quiero una propiedad en Madrid con un precio mayor a 100000, y con dos habitaciones, ademas
        me gustaria que estuviera en un barrio seguro y con metro cercano, aunque no es imprescindible"""
        extracted_data = await extractor_service.extract(user_input_text)


        classifier_service = ClassifierService()
        classified_data = await classifier_service.classify(extracted_data)

        #AQUI IRIA YA LOS BACKGROUND TASKS PARA LLAMAR A LOS DISTINTOS ENDPOINTS DEPENDIENDO DE classified_data,
        #ESTO LO HARÍA CON BACKGROUND TASKS PARA NO BLOQUEAR LA RESPUESTA AL USUARIO
        pipeline_jobs = PipelineJobs()
        background_tasks.add_task(pipeline_jobs.execute_pipeline, classified_data)

        """ME FALTA HACER LA LLAMADAS A LOS DISTINTOS ENDPOINTS DEPENDIENDO DE classified_data,
          ESTO LO HARÍA CON BACKGROUND TASKS PARA NO BLOQUEAR LA RESPUESTA AL USUARIO
        """

        #aqui lo que haría seria un backegrund tasks que llamadas a un pipelin que dependiendo el classified_data
        #llamaría a distintos endpoints y esperaría a que todos me devuelvan un status ok para devolver la respuesta 
        #final al usuario
        return {
            "status": "processing",
            "message": "Data extraction and classification initiated", "classified_data": classified_data}
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))