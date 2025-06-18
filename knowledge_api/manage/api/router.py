# api/router.py
from fastapi import APIRouter, HTTPException, Depends

from knowledge_api.manage.model.models import TextResponse, QueryInput, \
    WorldBuildingInput, RoleInput, QueryResponseRole, QueryResponseWorld
# Import a new RAG manager
from knowledge_api.manage.game_knowledge.services.rag_manager import RAGManager

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base Management"])

# Registered user blind box statistics API routing



# Dependency injection, using RAGManager to obtain services
async def get_role_service(is_init_collection: bool = False):
    rag_manager = RAGManager()
    return await rag_manager.get_service("role", is_init_collection=is_init_collection)


async def get_world_service(is_init_collection: bool = False):
    rag_manager = RAGManager()
    return await rag_manager.get_service("world", is_init_collection=is_init_collection)


# This interface is time-consuming and not public
# @router.post("/text_role", response_model=TextResponse)
async def add_text(
        input_data: RoleInput,
        role_service = Depends(lambda: get_role_service(is_init_collection=True))
):
    """Add text to the knowledge base"""
    result = await role_service.add_text(input_data.model_dump(exclude_none=True))

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])

    return {
        "code": 200,
        "success": True,
        "message": "Operation successful",
        "document_count": 10
    }


@router.post("/query_role", response_model=QueryResponseRole)
async def query_role(
        input_data: QueryInput,
        role_service = Depends(get_role_service)
):
    """Query the Role Knowledge Base"""
    result = await role_service.query(
        query=input_data.query,
        top_k=input_data.top_k,
        user_info=getUserInfo(input_data)
    )
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result


@router.post("/query_role_role")
async def query_role_role(
        input_data: QueryInput,
        role_service = Depends(get_role_service)
):
    """Query the role knowledge base (return directly to the list)"""
    # Use the query method to get results
    result = await role_service.query(
        query=input_data.query,
        top_k=input_data.top_k,
        user_info=getUserInfo(input_data)
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    
    # Extract a list of data from the results
    result_list = []
    for res in result.get("results", []):
        if (res.get("type") == "join" or res.get('role_id')=="share" ) and res.get("relations_role", ""):
            relations_role = res.get("relations_role", "").replace("，", ",")
            if relations_role == "" or relations_role == "[]" or relations_role is None:
                result_list.append(res)  # Common sense that everyone knows if there is no connection
            elif input_data.role_id in relations_role.split(","):
                result_list.append(res)  # If the relationship is matched, only find information about this character
        else:
            result_list.append(res)
    # The filtering logic here is already implemented in RoleRAGService.search (), so there is no need to repeat the filtering
    return result_list


# This interface is time-consuming and not public
# @router.post("/text_world", response_model=TextResponse)
async def add_text_world(
        input_data: WorldBuildingInput,
        world_service = Depends(lambda: get_world_service(is_init_collection=True))
):
    """Add text to the knowledge base"""
    result = await world_service.add_text(input_data.model_dump(exclude_none=True))

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])

    return {
        "code": 200,
        "success": True,
        "message": "Operation successful",
        "document_count": 10
    }


@router.post("/query_world", response_model=QueryResponseWorld)
async def query_world(
        input_data: QueryInput,
        world_service = Depends(get_world_service)
):
    """Query the World Knowledge Base"""
    result = await world_service.query(
        query=input_data.query,
        top_k=input_data.top_k,
        user_info=getUserInfo(input_data)
    )
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["message"])
    return result


@router.get("/health", response_model=dict)
async def health_check():
    """Health check interface"""
    return {
        "status": "ok",
        "message": "The service is running normally."
    }


def getUserInfo(input_data: QueryInput):
    return {
        "role_id": input_data.role_id if input_data.role_id else 'role001',
        "level": input_data.level if input_data.level else 1000,
        "user_level": input_data.user_level if input_data.user_level else 1000,
        "world_id": input_data.world_id if input_data.world_id else 'world001',
    }
