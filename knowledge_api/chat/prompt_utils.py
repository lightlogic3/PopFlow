from typing import Dict, Any, List, Optional
import json

from knowledge_api.utils.log_config import get_logger

logger = get_logger()

def prompt_pre(text: str, variables: Dict[str, Any]) -> str:
    """Replace variables in prompt word templates

Args:
Text: Cue word template
Variables: variable dictionary

Returns:
Replaced cue word"""
    if not text:
        return text
        
    if not ("{" in text):
        return text
        
    template = text
    for key, value in variables.items():
        template = template.replace("{" + key + "}", str(value))
        
    return template


def merge_contexts(contexts: List[str], user_info: Optional[Dict[str, Any]] = None) -> str:
    """Merge context and apply user information

Args:
Context: list of contexts
user_info: User Information

Returns:
merged context"""
    merged = "\n\n".join(contexts)
    
    # If there is user information, apply it to the context
    if user_info:
        merged = prompt_pre(merged, user_info)
        
    return merged

def extract_sources_from_results(results: List[Dict[str, Any]],memory:List[Dict[str,Any]], top_k: int = 3) -> Dict[str, Any]:
    """Extract context and source from search results

Args:
Results: List of search results
Memory: List of memory contexts
top_k: Maximum number of results returned

Returns:
Dictionary with context and source"""
    # Filter results with similarity below a threshold and sort them
    sorted_results = sorted(results, key=lambda result: result.get("score", 0.0))
    results = sorted_results[:top_k]
    
    # Extract context and source
    contexts = []
    sources = []
    
    for result in results:
        # contextual text
        contexts.append(result.get("text", ""))
        
        # source information
        metadata = result.get("metadata", {})
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except:
                metadata = {"text": metadata}
                
        source = {
            "id": result.get("id", ""),
            "text": result.get("text", ""),
            "title": result.get("title", "") or metadata.get("title", ""),
            "source": result.get("source", "") or metadata.get("source", ""),
            "score": result.get("score", 0.0)
        }
        sources.append(source)
        
    return {
        "contexts": contexts,
        "sources": sources,
        "memory": memory
    }

def find_closest_relationship_level(data, target):
    """Find the relationship level closest to the target

Args:
Data: relationship level data list
Target: target relationship level

Returns:
closest relationship rank item"""
    if data is None:
        return None
        
    # Filter all dictionaries relationship_level less than target
    filtered_data = [item.model_dump() for item in data if item.relationship_level <= target]
    
    # If there are no eligible values, return None.
    if not filtered_data:
        return None
        
    # Find the relationship_level closest to the target
    closest_item = min(filtered_data, key=lambda x: target - x.get("relationship_level"))
    return closest_item 