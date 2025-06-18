from typing import Dict, Any, List, Optional

from knowledge_api.manage.game_knowledge.services.rag_service import RAGService
from knowledge_api.utils.log_config import get_logger

logger = get_logger()

class RoleRAGService(RAGService):
    """Role Knowledge Base RAG Service"""
    
    def __init__(self, **kwargs):
        """Initialize Role RAG Service"""
        super().__init__(table_name="role", **kwargs)
        
    def get_table_schema(self) -> Dict[str, Any]:
        """Get role table structure

Returns:
Table Structure Dictionary"""
        return {
            "text": "STRING",  # Vectorized corpus required, required
            "role_id": "STRING",  # Role unique identifier. Required
            "type": "STRING",  # Type [Basic Experience, Role Experience, Shared Experience] Required
            "title": "STRING",  # Title, required
            "source": "STRING",  # source
            "metadata": "STRING",  # Other meta-information
            "tags": "STRING",  # keyword
            "grade": "FLOAT",  # Character level, required
            "relations": "STRING",  # Relational Storage Knowledge Network
            "relations_role": "STRING"  # shared role experience
        }
        
    def _build_filter_string(self, user_info: dict = None) -> Optional[str]:
        """Build filters based on user information

Args:
user_info: User Information

Returns:
Filter condition string"""
        if not user_info:
            return None
            
        role_id = user_info.get("role_id")
        level = user_info.get("level")
        
        if not role_id:
            return None
            
        # First layer of filtering: Role IDs
        filters = [f'role_id in("{role_id}","share")']
        
        # Second layer of filtering: character hierarchy
        if level is not None:
            filters.append(f"grade<={level}")
            
        return " and ".join(filters)
        
    async def search(self, query_embedding: List[float], top_k: int = 5, user_info: dict = None) -> List[Dict[str, Any]]:
        """Search for similar documents using embedding vectors and apply role-specific filtering logic

Args:
query_embedding: Query Embedding Vector
top_k: Number of results returned
user_info: User Information

Returns:
List of similar documents"""
        # Build filters and perform searches
        filter_str = self._build_filter_string(user_info)
        results = await self.vector_store.search(query_embedding, top_k=top_k, filter_str=filter_str)
        
        # If there is no user information, return the result directly
        if not user_info:
            return results
            
        # The third layer of filtering: shared experiences and associated roles
        role_id = user_info.get("role_id")
        if not role_id:
            return results
            
        filtered_results = []
        for res in results:
            # If it is a shared experience type, check the associated roles
            if res.get("type") == "join":
                relations_role = res.get("relations_role", "")
                if not relations_role:
                    # If there is no relationship, it is regarded as common knowledge and added directly
                    filtered_results.append(res)
                else:
                    # Processing associated role lists
                    relations_role = relations_role.replace("，", ",")
                    if relations_role == "" or relations_role == "[]" or relations_role is None:
                        filtered_results.append(res)  # Empty correlation can be seen
                    elif role_id in relations_role.split(","):
                        filtered_results.append(res)  # Role in association list
            else:
                # Non-shared experience types, add directly
                filtered_results.append(res)
                
        return filtered_results 