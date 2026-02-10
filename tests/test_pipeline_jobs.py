import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.jobs.pipeline_jobs import PipelineJobs

@pytest.fixture
def pipeline():
    """Fixture que crea una instancia de PipelineJobs"""
    return PipelineJobs()

@pytest.fixture
def classified_data_mock():
    """Mock de datos clasificados del classifier service"""
    return {
        "type": "property",
        "to_database_service": {
            "location": "Madrid",
            "min_price": 100000,
            "bedrooms": 2,
            "safe_neighborhood": True
        },
        "to_generator_embeddings": {
            "query": "propiedad Madrid dos habitaciones",
            "min_price": 100000
        },
        "to_ranking": {
            "preference": "safety",
            "filters": ["price", "location"]
        }
    }

# ============== TESTS EXITOSOS ==============

@pytest.mark.asyncio
async def test_database_service_success(pipeline):
    """Test: Database Service devuelve 200"""
    mock_response = {
        "properties": [
            {"id": 1, "location": "Madrid", "price": 150000},
            {"id": 2, "location": "Madrid", "price": 120000}
        ]
    }
    
    mock_response_obj = AsyncMock()
    mock_response_obj.status_code = 200
    mock_response_obj.json = MagicMock(return_value=mock_response)
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_post = AsyncMock(return_value=mock_response_obj)
        mock_client.return_value.__aenter__.return_value.post = mock_post
        
        result = await pipeline._call_database_service({"to_database_service": {"test": "data"}})
        
        assert result["status_code"] == 200
        assert result["success"] == True
        assert result["data"] == mock_response
        print("Database Service test exitoso")

@pytest.mark.asyncio
async def test_embeddings_service_success(pipeline):
    """Test: Embeddings Service devuelve 200"""
    mock_response = {
        "embeddings": [0.1, 0.2, 0.3, 0.4, 0.5],
        "vector_id": "vec_123"
    }
    
    mock_response_obj = AsyncMock()
    mock_response_obj.status_code = 200
    mock_response_obj.json = MagicMock(return_value=mock_response)
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_post = AsyncMock(return_value=mock_response_obj)
        mock_client.return_value.__aenter__.return_value.post = mock_post
        
        result = await pipeline._call_embeddings_service({"to_generator_embeddings": {"test": "data"}})
        
        assert result["status_code"] == 200
        assert result["success"] == True
        assert result["data"] == mock_response
        print("Embeddings Service test exitoso")

@pytest.mark.asyncio
async def test_ranking_service_success(pipeline, classified_data_mock):
    """Test: Ranking Service devuelve 200 (con dependencias satisfechas)"""
    mock_response = {
        "ranked_results": [
            {"id": 1, "score": 0.95},
            {"id": 2, "score": 0.87}
        ]
    }
    
    # Simulamos que database y embeddings fueron exitosos
    db_result = {"success": True, "status_code": 200, "data": {"properties": []}}
    embeddings_result = {"success": True, "status_code": 200, "data": {"embeddings": []}}
    
    mock_response_obj = AsyncMock()
    mock_response_obj.status_code = 200
    mock_response_obj.json = MagicMock(return_value=mock_response)
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_post = AsyncMock(return_value=mock_response_obj)
        mock_client.return_value.__aenter__.return_value.post = mock_post
        
        result = await pipeline._call_ranking_service(
            classified_data_mock,
            db_result,
            embeddings_result
        )
        
        assert result["status_code"] == 200
        assert result["success"] == True
        assert result["data"] == mock_response
        print("Ranking Service test exitoso")

@pytest.mark.asyncio
async def test_full_pipeline_success(pipeline, classified_data_mock):
    """Test: Pipeline completo exitoso (todos los servicios devuelven 200)"""
    
    db_mock = {"properties": [{"id": 1, "price": 150000}]}
    embeddings_mock = {"embeddings": [0.1, 0.2, 0.3]}
    ranking_mock = {"ranked_results": [{"id": 1, "score": 0.95}]}
    
    with patch('httpx.AsyncClient') as mock_client:
        async def mock_post(url, **kwargs):
            response = AsyncMock()
            
            if "database" in url:
                response.status_code = 200
                response.json = AsyncMock(return_value=db_mock)
            elif "embeddings" in url:
                response.status_code = 200
                response.json = AsyncMock(return_value=embeddings_mock)
            elif "ranking" in url:
                response.status_code = 200
                response.json = AsyncMock(return_value=ranking_mock)
            
            return response
        
        mock_client.return_value.__aenter__.return_value.post = mock_post
        
        result = await pipeline.run_pipeline(classified_data_mock)
        
        assert result["status"] == "success"
        assert "Pipeline completado exitosamente" in result["message"]
        assert result["results"]["database"]["success"] == True
        assert result["results"]["embeddings"]["success"] == True
        assert result["results"]["ranking"]["success"] == True
        print("Full Pipeline test exitoso")

# ============== TESTS CON ERRORES ==============

@pytest.mark.asyncio
async def test_database_service_failure(pipeline):
    """Test: Database Service devuelve 500"""
    
    mock_response_obj = AsyncMock()
    mock_response_obj.status_code = 500
    mock_response_obj.text = "Internal Server Error"
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_post = AsyncMock(return_value=mock_response_obj)
        mock_client.return_value.__aenter__.return_value.post = mock_post
        
        result = await pipeline._call_database_service({"to_database_service": {"test": "data"}})
        
        assert result["status_code"] == 500
        assert result["success"] == False
        assert result["data"] == None
        assert result["error"] == "Internal Server Error"
        print("Database Service failure test exitoso")

@pytest.mark.asyncio
async def test_ranking_blocked_by_database_failure(pipeline, classified_data_mock):
    """Test: Ranking NO se ejecuta si Database falló"""
    
    db_result = {"success": False, "status_code": 500, "data": None, "error": "Database error"}
    embeddings_result = {"success": True, "status_code": 200, "data": {"embeddings": []}}
    
    result = await pipeline._call_ranking_service(
        classified_data_mock,
        db_result,
        embeddings_result
    )
    
    assert result["status_code"] == 400
    assert result["success"] == False
    assert "Database o Embeddings Service fallaron" in result["error"]
    print("Ranking bloqueado por Database failure test exitoso")

@pytest.mark.asyncio
async def test_ranking_blocked_by_embeddings_failure(pipeline, classified_data_mock):
    """Test: Ranking NO se ejecuta si Embeddings falló"""
    
    db_result = {"success": True, "status_code": 200, "data": {"properties": []}}
    embeddings_result = {"success": False, "status_code": 500, "data": None, "error": "Embeddings error"}
    
    result = await pipeline._call_ranking_service(
        classified_data_mock,
        db_result,
        embeddings_result
    )
    
    assert result["status_code"] == 400
    assert result["success"] == False
    print("Ranking bloqueado por Embeddings failure test exitoso")

@pytest.mark.asyncio
async def test_pipeline_partial_failure(pipeline, classified_data_mock):
    """Test: Pipeline devuelve partial_failure si algún servicio falla"""
    
    with patch('httpx.AsyncClient') as mock_client:
        async def mock_post(url, **kwargs):
            response = AsyncMock()
            
            if "database" in url:
                response.status_code = 200
                response.json = AsyncMock(return_value={"properties": []})
            elif "embeddings" in url:
                response.status_code = 500  # ← FALLA
                response.text = "Embeddings Service Error"
            elif "ranking" in url:
                response.status_code = 200
                response.json = AsyncMock(return_value={})
            
            return response
        
        mock_client.return_value.__aenter__.return_value.post = mock_post
        
        result = await pipeline.run_pipeline(classified_data_mock)
        
        assert result["status"] == "partial_failure"
        assert "embeddings" in result["message"]
        print("Pipeline partial failure test exitoso")

@pytest.mark.asyncio
async def test_pipeline_exception_handling(pipeline, classified_data_mock):
    """Test: Pipeline maneja excepciones correctamente"""
    
    with patch('httpx.AsyncClient') as mock_client:
        async def failing_post(*args, **kwargs):
            raise Exception("Connection timeout")
        
        mock_client.return_value.__aenter__.return_value.post = failing_post
        
        result = await pipeline.run_pipeline(classified_data_mock)
        
        # Cuando falla, algunos servicios devuelven error (no es "failed" porque
        # ranking devuelve 400 por dependencia)
        assert result["status"] in ["failed", "partial_failure"]
        print("Pipeline exception handling test exitoso")

@pytest.mark.asyncio
async def test_pipeline_skips_missing_keys(pipeline):
    """Test: Pipeline salta servicios si no existen en classified_data"""
    
    minimal_data = {"type": "test"}
    
    result = await pipeline._process_classified_data(minimal_data)
    
    assert result["database"]["status_code"] == 204
    assert result["embeddings"]["status_code"] == 204
    assert result["ranking"]["status_code"] == 204
    assert all(r["success"] for r in result.values())
    print("Pipeline skip missing keys test exitoso")