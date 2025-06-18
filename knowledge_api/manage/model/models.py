# api/models.py
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, HttpUrl, Field

class RoleInput(BaseModel):
    """Role Input Model"""
    text: str = Field(..., description="Corpus that requires vectorization")
    role_id: str = Field(..., description="role unique identifier")
    type: str = Field(..., description="Type [Basic Experience, Role Experience, Shared Experience]")
    title: str = Field(..., description="title")
    grade: float = Field(..., description="character level")
    source: Optional[str] = Field(None, description="source")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Other meta-information")
    tags: Optional[List[str]] = Field(None, description="keyword tag")
    relations: Optional[str] = Field(None, description="Relational Storage Knowledge Network")
    relations_role: Optional[str] = Field(None, description="shared role experience")

class TextInput(BaseModel):
    """Text Input Model"""
    content: str = Field(..., description="text content")
    title: Optional[str] = Field(None, description="Text title")
    source: Optional[str] = Field(None, description="Text Source")
    tags: Optional[List[str]] = Field(None, description="tag list")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Extra metadata")


class UrlInput(BaseModel):
    """URL input model"""
    url: HttpUrl = Field(..., description="URL to crawl")
    depth: Optional[int] = Field(0, description="crawl depth, 0 current page only, 1 contains links to current page")
    title: Optional[str] = Field(None, description="custom title")
    tags: Optional[List[str]] = Field(None, description="tag list")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Extra metadata")


class QueryInput(BaseModel):
    """query input model"""
    query: str = Field(None, description="query text")
    top_k: Optional[int] = Field(5, description="Number of results returned")
    source: Optional[str] = Field(None, description="source")
    role_id: str = Field(None, description="role unique identifier")
    level: float = Field(None, description="character level")
    user_level: float = Field(None, description="user level")
    world_id: Optional[str] = Field(None, description="Unique World Identity")


class DocumentRole(BaseModel):
    """Document Model"""
    doc_id: str = Field(None, description="Document ID")
    text: str = Field(..., description="Corpus that requires vectorization")
    role_id: str = Field(..., description="role unique identifier")
    type: str = Field(..., description="Type [Basic Experience, Role Experience, Shared Experience]")
    title: str = Field(..., description="title")
    grade: float = Field(..., description="character level")
    source: Optional[str] = Field(None, description="source")
    metadata: Optional[str] = Field(None, description="Other meta-information")
    tags: Optional[str] = Field(None, description="keyword tag")
    relations: Optional[str] = Field(None, description="Relational Storage Knowledge Network")
    relations_role: Optional[str] = Field(None, description="shared role experience")
    score: Optional[float] = Field(None, description="similarity score")


class DocumentWorld(BaseModel):
    """Document Model"""
    id: str = Field(None, description="Document ID")
    text: str = Field(..., description="Corpus that requires vectorization")
    type: str = Field(..., description="Type [Scene, Worldview]")
    title: str = Field(..., description="title")
    grade: float = Field(..., description="worldview level")
    source: Optional[str] = Field(None, description="source")
    metadata: Optional[str] = Field(None, description="Other meta-information")
    tags: Optional[str] = Field(None, description="keyword tag")
    relations: Optional[str] = Field(None, description="Relational Storage Knowledge Network")
    relations_role: Optional[str] = Field(None, description="Associated Role ID")
    score: Optional[float] = Field(None, description="similarity score")

class TextResponse(BaseModel):
    """Text processing response"""
    success: bool = Field(..., description="Is the processing successful?")
    message: str = Field(..., description="Processing result message")
    document_count: int = Field(..., description="Number of documents processed")


class QueryResponseRole(BaseModel):
    """query response"""
    success: bool = Field(..., description="Is the query successful?")
    message: str = Field(..., description="query result message")
    results: List[DocumentRole] = Field(..., description="query result list")

class QueryResponseWorld(BaseModel):
    """query response"""
    success: bool = Field(..., description="Is the query successful?")
    message: str = Field(..., description="query result message")
    results: List[DocumentWorld] = Field(..., description="query result list")

class StatsResponse(BaseModel):
    """Statistical information response"""
    success: bool = Field(..., description="Was the acquisition of statistics successful?")
    message: str = Field(..., description="statistics message")
    total_documents: int = Field(..., description="Total number of documents")
    collection_name: str = Field(..., description="collection name")
    embedding_model: str = Field(..., description="Embedded model name")
    additional_info: Optional[Dict[str, Any]] = Field(None, description="Additional statistics")



class WorldBuildingInput(BaseModel):
    """Scenario and Worldview Input Model"""
    text: str = Field(..., description="Corpus that requires vectorization")
    type: str = Field(..., description="Type [Scene, Worldview]")
    title: str = Field(..., description="title")
    grade: float = Field(..., description="worldview level")
    source: Optional[str] = Field(None, description="source")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Other meta-information")
    tags: Optional[List[str]] = Field(None, description="keyword tag")
    relations: Optional[str] = Field(None, description="Relational Storage Knowledge Network")
    relations_role: Optional[str] = Field(None, description="Associated Role ID")