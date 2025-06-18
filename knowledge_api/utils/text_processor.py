# utils/text_processor.py
from typing import List, Dict, Any, Optional
import re
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter

from knowledge_api.config import MAX_CHUNK_SIZE, CHUNK_OVERLAP


def split_text(text: str, metadata: Optional[Dict[str, Any]] = None,
               chunk_size: int = MAX_CHUNK_SIZE,
               chunk_overlap: int = CHUNK_OVERLAP) -> List[Dict[str, Any]]:
    """Split text into blocks suitable for embedding

Args:
Text: The text to be split
Metadata: metadata
chunk_size: Text block size
chunk_overlap: Text block overlap size

Returns:
List of documents containing text blocks and metadata"""
    # Create a text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", ";", "；", "，", ",", " ", ""]
    )

    # Split text
    chunks = text_splitter.split_text(text)

    # Prepare metadata
    metadata = metadata or {}

    # Create document list
    documents = []
    for i, chunk in enumerate(chunks):
        # Generate a unique ID
        doc_id = metadata.get("doc_id", f"doc-{i}")
        if len(chunks) > 1:
            doc_id = f"{doc_id}-chunk-{i}"
        document=metadata
        # Create document
        document.update({"id": doc_id})
        document.update({"text": chunk})
        documents.append(json.loads(convert_objects_to_str(document)))
    return documents


def convert_objects_to_str(data):
    """Recursively converts the object type in the dictionary to string.

@Param data The input data can be a dictionary, list, or other type
@Return processed data, all complex objects are converted to strings"""
    # If it is a dictionary type, recursively process each key-value pair
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            result[key] = convert_objects_to_str(value)
        return json.dumps(result, ensure_ascii=False)

    # If it is a list type, recursively process each element
    elif isinstance(data, list):
        return json.dumps(data,ensure_ascii=False)

    # If it is a basic type, return it directly
    elif isinstance(data, (int, float, str, bool, type(None))):
        return data

    # Other types of objects, converted to strings
    else:
        return str(data)

def clean_text(text: str) -> str:
    """Clean up text to remove excess whitespace and special characters

Args:
Text: The text to be cleaned

Returns:
Cleaned text"""
    # Replace multiple consecutive changes with double line wrapping
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Replace consecutive spaces with a single space
    text = re.sub(r' {2,}', ' ', text)

    # Remove control character
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    # Correct spaces between Chinese, English, and numbers
    text = re.sub(r'([a-zA-Z0-9])([，。！？；：""''【】（）])([a-zA-Z0-9])', r'\1\2 \3', text)

    return text.strip()


def tags_to_string(tags: List[str]) -> str:
    """Convert a list of labels to a string"""
    if not tags:
        return ""
    return json.dumps(tags, ensure_ascii=False)


def metadata_to_string(metadata: Dict[str, Any]) -> str:
    """Convert metadata dictionary to string"""
    if not metadata:
        return "{}"
    return json.dumps(metadata, ensure_ascii=False)