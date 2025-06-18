from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel
from datetime import datetime
import importlib
import time

from plugIns.memory_system import MemoryManager
from plugIns.memory_system.memory_factory import MemoryLevel, MemoryFactory
from plugIns.memory_system.model import MemoryContext  # Import UserMetadata and MemoryContext
from knowledge_api.framework.redis.cache_manager import CacheManager
from knowledge_api.model.llm_token_model import LLMTokenResponse

# Create route
router = APIRouter(prefix="/memory", tags=["memory"])

# Create MemoryManager and MemoryFactory instances in memory
memory_manager = MemoryManager()
memory_factory = MemoryFactory()
memory_factory.register_default_systems()


# request model
class ConversationRequest(BaseModel):
    content: str
    role: str = "user"  # User or assistant
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    parent_message_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MemoryQueryRequest(BaseModel):
    query: str
    top_k: int = 5
    include_history: bool = True


class PluginRequest(BaseModel):
    plugin_name: Optional[str] = None  # plugin name
    plugin_level: Optional[Union[int, str]] = None  # Plugin level, can be integer or string
    custom_plugin_path: Optional[str] = None  # custom plugin path


# Composite Request Model - Allows direct submission of query parameters
class MemoryRetrieveRequest(BaseModel):
    query: Optional[str] = None
    top_k: int = 5
    include_history: bool = True
    plugin_request: Optional[PluginRequest] = None


# Chat Test Request Model
class ChatTestRequest(BaseModel):
    model_id: str
    query: str
    conversation_history: Optional[List[Dict[str, Any]]] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = 1000
    user_id: Optional[str] = None
    role_id: Optional[str] = None
    session_id: Optional[str] = None
    plugin_request: Optional[PluginRequest] = None  # Add plugin request


# response model
class MemoryResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


# Get the memory system plug-in
def get_memory_plugin(plugin_request: Optional[PluginRequest] = None) -> MemoryLevel:
    """Obtain memory system plug-ins upon request"""
    # Default dialog memory system
    default_level = MemoryLevel.LEVEL_6_CONVERSATION
    
    if not plugin_request:
        return default_level
        
    # Select by plugin level
    if plugin_request.plugin_level is not None:
        try:
            if isinstance(plugin_request.plugin_level, int):
                return MemoryLevel(plugin_request.plugin_level)
            elif isinstance(plugin_request.plugin_level, str):
                # Attempt to match the enumeration name
                for level in MemoryLevel:
                    if level.name == plugin_request.plugin_level:
                        return level
                # Try converting to integer
                return MemoryLevel(int(plugin_request.plugin_level))
        except (ValueError, TypeError):
            pass
            
    # Select by plugin name
    if plugin_request.plugin_name:
        for level in MemoryLevel:
            try:
                plugin_instance = memory_factory.get_instance(level)
                if plugin_instance and plugin_instance.name == plugin_request.plugin_name:
                    return level
            except Exception:
                continue
    
    # Try loading a custom plugin
    if plugin_request.custom_plugin_path:
        try:
            module_path, class_name = plugin_request.custom_plugin_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            plugin_class = getattr(module, class_name)
            # Register as a temporary plugin
            temp_level = MemoryLevel.LEVEL_6_CONVERSATION  # Use default level
            memory_factory.register(temp_level, plugin_class)
            return temp_level
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"加载自定义插件失败: {str(e)}")
    
    # Use default plugins
    return default_level


@router.get("/plugins", response_model=MemoryResponse)
async def get_available_plugins():
    """Get a list of available memory system plugins"""
    try:
        plugins_info = []
        
        # Get all registered memory levels
        for level in memory_factory.get_registered_levels():
            try:
                # Create a plug-in instance (if not already created)
                if not memory_factory.get_instance(level):
                    await memory_factory.create(level)
                    
                plugin_instance = memory_factory.get_instance(level)
                if plugin_instance:
                    plugins_info.append({
                        "level": level.value,
                        "level_name": level.name,
                        "name": plugin_instance.name,
                        "description": plugin_instance.description
                    })
            except Exception as e:
                plugins_info.append({
                    "level": level.value,
                    "level_name": level.name,
                    "name": f"未加载 (错误: {str(e)})",
                    "description": "Plugin loading failed"
                })
        
        return {
            "success": True,
            "message": f"获取到 {len(plugins_info)} 个可用插件",
            "data": plugins_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取插件列表时发生错误: {str(e)}")


@router.post("/chat-test", response_model=MemoryResponse)
async def chat_test(request: ChatTestRequest):
    """Test and chat with AI"""
    try:
        # Get the AI instance from the model ID
        cache_manager = CacheManager()
        ai = await cache_manager.get_ai_by_model_id(request.model_id)
        
        if not ai:
            raise HTTPException(status_code=400, detail=f"无法获取模型 {request.model_id} 的AI实例")
        
        # Prepare for conversation history
        messages = request.conversation_history or []
        messages.insert(0,{})
        # If the user provides a user ID, first retrieve the relevant memory from the memory system
        retrieved_memories = []
        if request.user_id and request.query:
            # Get the memory system plug-in
            memory_level = get_memory_plugin(request.plugin_request)
            
            # Initialize the memory system
            await memory_manager.set_memory_level(memory_level)
            
            # Creating user metadata
            user_metadata = await memory_manager.get_or_create_user_metadata(request.user_id, request.role_id or "default", request.session_id)
            
            # Make sure role_id exist
            role_id = request.role_id or "default"
            user_metadata.role_id = role_id
            
            if request.session_id:
                user_metadata.session_id = request.session_id
            
            # Set include_history as an additional parameter
            extra_params = {
                "include_history": True
            }
            
            # Check required fields in metadata
            if not user_metadata.user_id or not user_metadata.role_id:
                raise HTTPException(status_code=400, detail="Required fields missing in user metadata")
            
            # Retrieve relevant memory
            retrieved_memories = await memory_manager.retrieve(
                query=request.query,
                user_id=request.user_id,
                role_id=role_id,
                session_id=request.session_id,
                top_k=5  # Retrieve the top 5 most relevant memories
            )
            
            # If a memory is retrieved, add it to the beginning of the message as context
            if retrieved_memories:
                # Formatting retrieved memories
                memory_texts = []
                for memory in retrieved_memories:
                    role_text = "user" if memory.get("role") == "user" else "AI" 
                    memory_texts.append(f"{role_text}: {memory.get('content', '')}")
                
                memory_context = "\n\n".join(memory_texts)
                
                # Add memory context as a system message
                messages[0]={
                    "role": "system",
                    "content": f"你是一个聊天对话系统，以下是与当前对话相关的历史记忆，请参考这些信息回答用户问题：\n\n{memory_context}"
                }
            else:
                # If no memory is retrieved, set the default system message
                messages[0]={
                    "role": "system",
                    "content": "You are a chat system, please answer user questions."
                }

        # If there is no conversation history or a new user message needs to be added
        if request.query:
            messages.append({
                "role": "user",
                "content": request.query
            })
        
        # Call AI Chat
        result: LLMTokenResponse = await ai.chat_completion(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            application_scenario="memory_test"
        )
        
        # Store the conversation results in the memory system (if user information is provided).
        if request.user_id:
            try:
                # Get the memory system plug-in
                memory_level = get_memory_plugin(request.plugin_request)
                
                # Initialize the memory system
                await memory_manager.set_memory_level(memory_level)
                
                # Use the baseline of the current timestamp to ensure that the messages are in the correct order
                base_timestamp = datetime.now()
                
                # Store user issues (a bit earlier, ensure order)
                user_memory_context = MemoryContext(
                    content=request.query,
                    source="user",
                    metadata={
                        "message_id": f"user_{base_timestamp.timestamp()}",
                        "conversation_pair": True  # Tag as conversation pair
                    },
                    timestamp=base_timestamp
                )
                
                await memory_manager.store(
                    memory_context=user_memory_context,
                    user_id=request.user_id,
                    role_id=request.role_id or "default",
                    session_id=request.session_id
                )
                
                # Store AI responses (later, ensure order)
                time.sleep(0.001)  # Wait 1 ms to ensure timestamp is different
                ai_timestamp = datetime.now()
                ai_memory_context = MemoryContext(
                    content=result.content,
                    source="assistant", 
                    metadata={
                        "message_id": f"ai_{ai_timestamp.timestamp()}",
                        "model": result.model,
                        "tokens": result.total_tokens,
                        "conversation_pair": True  # Tag as conversation pair
                    },
                    timestamp=ai_timestamp
                )
                
                await memory_manager.store(
                    memory_context=ai_memory_context,
                    user_id=request.user_id,
                    role_id=request.role_id or "default",
                    session_id=request.session_id
                )
            except Exception as e:
                print(f"存储对话到记忆系统失败: {e}")
        
        return {
            "success": True,
            "message": "Chat was successful",
            "data": {
                "response": result.content,
                "model": result.model,
                "tokens": {
                    "input": result.input_tokens,
                    "output": result.output_tokens,
                    "total": result.total_tokens
                },
                "elapsed_time": result.elapsed_time,
                "retrieved_memories": retrieved_memories if retrieved_memories else None
            }
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"聊天处理失败: {str(e)}")


@router.post("/store", response_model=MemoryResponse)
async def store_conversation(
    data: Dict[str, Any] = Body(...),
    user_id: str = Query(..., description="user ID"),
    role_id: str = Query(..., description="Role ID, required parameters"),
    session_id: Optional[str] = Query(None, description="Session ID")
):
    """Store conversations to memory system"""
    try:
        # Verify required parameters
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID cannot be empty")
        if not role_id:
            raise HTTPException(status_code=400, detail="Role ID cannot be empty")
        if not data.get("content"):
            raise HTTPException(status_code=400, detail="Dialogue cannot be empty")
        
        # parse request data
        plugin_request = None
        conversation_data = data
        
        # Extract plugin_request (if present)
        if "plugin_request" in data:
            plugin_request = PluginRequest(**data.pop("plugin_request"))
        
        # Get the memory system plug-in
        memory_level = get_memory_plugin(plugin_request)
        
        # Initialize the memory system
        await memory_manager.set_memory_level(memory_level)
        
        # Build conversation data and create a MemoryContext
        memory_context = MemoryContext(
            content=data.get("content", ""),
            source=data.get("role", "user"),
            metadata={
                "conversation_id": data.get("conversation_id"),
                "message_id": data.get("message_id"),
                "parent_message_id": data.get("parent_message_id"),
                # Merge raw metadata
                **(data.get("metadata", {}) or {})
            },
            timestamp=datetime.now()
        )
        
        # Store conversation
        success = await memory_manager.store(
            memory_context=memory_context,
            user_id=user_id,
            role_id=role_id,
            session_id=session_id
        )
        
        plugin_info = f"使用插件: {memory_manager.get_current_level().name}"
        
        if success:
            return {
                "success": True,
                "message": f"对话已成功存储 ({plugin_info})",
                "data": None
            }
        else:
            return {
                "success": False,
                "message": f"存储对话失败 ({plugin_info})",
                "data": None
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"存储对话时发生错误: {str(e)}")


@router.post("/retrieve", response_model=MemoryResponse)
@router.get("/retrieve", response_model=MemoryResponse)
async def retrieve_conversations(
    data: Dict[str, Any] = Body(None),
    user_id: str = Query(..., description="user ID"),
    role_id: str = Query(..., description="Role ID, required parameters"),
    session_id: Optional[str] = Query(None, description="Session ID"),
    query: Optional[str] = Query(None, description="Query content (for GET requests)"),
    top_k: int = Query(5, description="Number of results returned (for GET requests)"),
    include_history: bool = Query(True, description="Whether to include historical sessions (for GET requests)")
):
    """Retrieve relevant conversations from memory systems"""
    try:
        # Verify required parameters
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID cannot be empty")
        if not role_id:
            raise HTTPException(status_code=400, detail="Role ID cannot be empty")
        
        plugin_request = None
        
        # Parse data from the request body
        if data:
            query_data = data.copy()
            # Extract plugin_request (if present)
            if "plugin_request" in query_data:
                plugin_request = PluginRequest(**query_data.pop("plugin_request"))
                
            # Using the query parameters in the request body
            query = query_data.get("query", query)
            top_k = query_data.get("top_k", top_k)
            include_history = query_data.get("include_history", include_history)
        
        # Verify necessary parameters
        if not query:
            raise HTTPException(status_code=400, detail="Query content cannot be empty")
        
        # Get the memory system plug-in
        memory_level = get_memory_plugin(plugin_request)
        
        # Initialize the memory system
        await memory_manager.set_memory_level(memory_level)
        
        # Search conversation
        results = await memory_manager.retrieve(
            query, 
            top_k=top_k, 
            user_id=user_id,
            role_id=role_id,
            session_id=session_id,
            include_history=include_history
        )
        
        plugin_info = f"使用插件: {memory_manager.get_current_level().name}"
        
        return {
            "success": True,
            "message": f"检索到 {len(results)} 条相关对话 ({plugin_info})",
            "data": results
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"检索对话时发生错误: {str(e)}")


@router.post("/sync", response_model=MemoryResponse)
async def sync_conversations(
    data: Dict[str, Any] = Body({}),
    user_id: str = Query(..., description="user ID"),
    role_id: str = Query(..., description="Role ID, required parameters"),
    run_in_background: bool = Query(True, description="Whether to run synchronization in the background")
):
    """Synchronize conversation data from database to memory system"""
    try:
        # Verify required parameters
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID cannot be empty")
        if not role_id:
            raise HTTPException(status_code=400, detail="Role ID cannot be empty")
        
        # Extract plugin_request (if present)
        plugin_request = None
        if "plugin_request" in data:
            plugin_request = PluginRequest(**data["plugin_request"])
        
        # Get the memory system plug-in
        memory_level = get_memory_plugin(plugin_request)
        
        # Initialize the memory system
        await memory_manager.set_memory_level(memory_level)
        
        # Synchronize conversation data
        success = await memory_manager.sync_from_database(
            user_id=user_id,
            role_id=role_id
        )
        
        plugin_info = f"使用插件: {memory_manager.get_current_level().name}"
        
        if success:
            return {
                "success": True,
                "message": f"同步任务已启动 ({plugin_info})",
                "data": None
            }
        else:
            return {
                "success": False,
                "message": f"启动同步任务失败 ({plugin_info})",
                "data": None
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"同步对话数据时发生错误: {str(e)}")


@router.get("/sync/status", response_model=MemoryResponse)
async def get_sync_status(
    user_id: str = Query(..., description="user ID"),
    role_id: str = Query(..., description="Role ID, required parameters"),
    plugin_level: Optional[Union[int, str]] = Query(None, description="plugin level"),
    plugin_name: Optional[str] = Query(None, description="plugin name"),
    custom_plugin_path: Optional[str] = Query(None, description="custom plugin path")
):
    """Get synchronization status"""
    try:
        # Verify required parameters
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID cannot be empty")
        if not role_id:
            raise HTTPException(status_code=400, detail="Role ID cannot be empty")
        
        # Build plugin_request
        plugin_request = None
        if plugin_level is not None or plugin_name or custom_plugin_path:
            plugin_request = PluginRequest(
                plugin_level=plugin_level,
                plugin_name=plugin_name,
                custom_plugin_path=custom_plugin_path
            )
        
        # Get the memory system plug-in
        memory_level = get_memory_plugin(plugin_request)
        
        # Initialize the memory system
        await memory_manager.set_memory_level(memory_level)
        
        # Get synchronization status
        status = await memory_manager.get_sync_status(user_id=user_id, role_id=role_id)
        
        plugin_info = f"使用插件: {memory_manager.get_current_level().name}"
        
        return {
            "success": True,
            "message": f"获取同步状态成功 ({plugin_info})",
            "data": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取同步状态时发生错误: {str(e)}") 