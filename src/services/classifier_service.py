from src.models.extract import ModelOutput

class ClassifierService:

    def _extract_data_clasify(self, extracted: ModelOutput) -> dict:
        soft_filters = [f.model_dump() for f in extracted.filters if f.strength == 1]
        #Esto en duda
        mid_filters = [f.model_dump() for f in extracted.filters if f.strength == 2]
        hard_filters = [f.model_dump() for f in extracted.filters if f.strength == 3]

        return {
            "soft": soft_filters,
            "mid": mid_filters,
            "hard": hard_filters,
            "extra_info": extracted.extra_info
        }
    
    async def classify(self, extracted: ModelOutput) -> dict:

        data = self._extract_data_clasify(extracted)

        to_database_service = data.get("hard", []) + data.get("mid", [])
        to_generator_embeddings = data.get("extra_info", "")
        to_ranking = data.get("soft", [])

        return {
            "to_database_service": to_database_service,
            "to_generator_embeddings": to_generator_embeddings,
            "to_ranking": to_ranking
        }
