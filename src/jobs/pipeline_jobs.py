from typing import Dict, Any, Optional
import httpx

class PipelineJobs:
    def __init__(self):
        # URLs de los endpoints (imaginarias pero realistas)
        self.DATABASE_SERVICE_URL = "http://localhost:8001/api/database/store"
        self.EMBEDDINGS_SERVICE_URL = "http://localhost:8002/api/embeddings/generate"
        self.RANKING_SERVICE_URL = "http://localhost:8003/api/ranking/process"

    async def _call_database_service(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Llama al servicio de base de datos"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.DATABASE_SERVICE_URL,
                    json=data.get("to_database_service"),
                    timeout=30.0
                )
                
                result = {
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "data": response.json() if response.status_code == 200 else None,
                    "error": response.text if response.status_code != 200 else None
                }
                
                print(f"Database Service - Status: {response.status_code}")
                return result
                
        except Exception as e:
            print(f"Error en Database Service: {str(e)}")
            return {
                "status_code": 500,
                "success": False,
                "data": None,
                "error": str(e)
            }

    async def _call_embeddings_service(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Llama al servicio de generación de embeddings"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.EMBEDDINGS_SERVICE_URL,
                    json=data.get("to_generator_embeddings"),
                    timeout=30.0
                )
                
                result = {
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "data": response.json() if response.status_code == 200 else None,
                    "error": response.text if response.status_code != 200 else None
                }
                
                print(f"Embeddings Service - Status: {response.status_code}")
                return result
                
        except Exception as e:
            print(f"Error en Embeddings Service: {str(e)}")
            return {
                "status_code": 500,
                "success": False,
                "data": None,
                "error": str(e)
            }

    async def _call_ranking_service(self, data: Dict[str, Any], 
                                    db_result: Dict[str, Any],
                                    embeddings_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Llama al servicio de ranking SOLO si database y embeddings devolvieron 200
        """
        # Valido que los dos anteriores fuero exitosos
        if not db_result["success"] or not embeddings_result["success"]:
            print("Ranking Service no se ejecutará - Falló un servicio anterior")
            return {
                "status_code": 400,
                "success": False,
                "data": None,
                "error": "Database o Embeddings Service fallaron. Ranking no puede ejecutarse."
            }
        
        try:
            # Combino los datos de entrada para el service de ranking
            ranking_payload = {
                **data.get("to_ranking"),
                "database_results": db_result.get("data"),
                "embeddings_results": embeddings_result.get("data")
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.RANKING_SERVICE_URL,
                    json=ranking_payload,
                    timeout=30.0
                )
                
                result = {
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "data": response.json() if response.status_code == 200 else None,
                    "error": response.text if response.status_code != 200 else None
                }
                
                print(f"Ranking Service - Status: {response.status_code}")
                return result
                
        except Exception as e:
            print(f"Error en Ranking Service: {str(e)}")
            return {
                "status_code": 500,
                "success": False,
                "data": None,
                "error": str(e)
            }

    async def _process_classified_data(self, classified_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa la data clasificada llamando a los servicios en orden
        y validando dependencias
        """
        results = {}
        
        # Database Service (si existe en classified_data)
        if "to_database_service" in classified_data:
            results["database"] = await self._call_database_service(classified_data)
        else:
            results["database"] = {"status_code": 204, "success": True, "data": None}
        
        # Embeddings Service (si existe en classified_data)
        if "to_generator_embeddings" in classified_data:
            results["embeddings"] = await self._call_embeddings_service(classified_data)
        else:
            results["embeddings"] = {"status_code": 204, "success": True, "data": None}
        
        # Ranking Service SOLO si los anteriores fueron exitosos
        if "to_ranking" in classified_data:
            results["ranking"] = await self._call_ranking_service(
                classified_data,
                results["database"],
                results["embeddings"]
            )
        else:
            results["ranking"] = {"status_code": 204, "success": True, "data": None}
        
        return results

    async def run_pipeline(self, classified_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta el pipeline completo y retorna un resumen del resultado
        """
        try:
            print(f"\nIniciando Pipeline con data: {classified_data.keys()}")
            
            # proceso la entrada
            results = await self._process_classified_data(classified_data)
            
            # valido que todos hayan salido bien para devolver un status final
            all_success = all(result["success"] for result in results.values())
            
            if all_success:
                return {
                    "status": "success",
                    "message": "Pipeline completado exitosamente",
                    "results": results
                }
            else:
                failed_services = [
                    service for service, result in results.items() 
                    if not result["success"]
                ]
                return {
                    "status": "partial_failure",
                    "message": f"Pipeline completado con errores en: {', '.join(failed_services)}",
                    "results": results
                }
                
        except Exception as e:
            print(f"Error crítico en pipeline: {str(e)}")
            return {
                "status": "failed",
                "message": f"Error en pipeline: {str(e)}",
                "results": None
            }