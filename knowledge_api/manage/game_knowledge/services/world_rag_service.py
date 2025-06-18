from typing import Dict, Any

from knowledge_api.manage.game_knowledge.services.rag_service import RAGService

class WorldRAGService(RAGService):
    """World Knowledge Base RAG Service"""
    
    def __init__(self, **kwargs):
        """Initialize the world RAG service"""
        super().__init__(table_name="world", **kwargs)
        
    def get_table_schema(self) -> Dict[str, Any]:
        """Get the world table structure

Returns:
Table Structure Dictionary"""
        return {
            "text": "STRING",  # Vectorized corpus required, required
            "world_id": "STRING",  # World unique identifier. Required
            "type": "STRING",  # Knowledge type
            "title": "STRING",  # Title, required
            "source": "STRING",  # source
            "metadata": "STRING",  # Other meta-information
            "tags": "STRING",  # keyword
        }
        
    def _build_filter_string(self, user_info: dict = None) -> str:
        """Build filters based on user information

Args:
user_info: User Information

Returns:
Filter condition string"""
        if not user_info:
            return None
            
        world_id = user_info.get("world_id")
        if not world_id:
            return None
            
        return f'world_id in("{world_id}","share")' 