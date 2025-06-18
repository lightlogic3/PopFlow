"""Workflow WebSocket Interface Module
Provides a WebSocket interface to interact with the workflow engine"""

import os
import json
import uuid
import asyncio
import logging
import random
from datetime import datetime
from typing import Dict, Any, Set, List, Optional
from functools import partial

from fastapi import WebSocket, WebSocketDisconnect, Depends, APIRouter

from knowledge_api.framework.workflow.nodes.message import MessageNode
from knowledge_api.framework.workflow.nodes.player_turn import PlayerTurnNode
from knowledge_api.mapper.chat_session.base import Session
from knowledge_api.mapper.roles.crud import RoleCRUD
from knowledge_api.framework.database.database import get_session
from knowledge_api.framework.workflow import WorkflowEngine, NodeFactory, Node, WorkflowContext
from knowledge_api.utils.log_config import get_logger

# Initialize the logger
logger = get_logger()

# Create a router
workflow_router = APIRouter(tags=["Workflow Engine"])

# Session management (temporary memory storage, you should actually use persistent storage)
sessions: Dict[str, Dict[str, Any]] = {}
websockets: Dict[str, Set[WebSocket]] = {}
workflow_engines: Dict[str, WorkflowEngine] = {}
node_factories: Dict[str, NodeFactory] = {}

# load template directory
TEMPLATE_DIR = "knowledge_api/framework/workflow/templates"


async def load_workflow_template(game_type: str) -> Dict[str, Any]:
    """Load workflow template

Args:
game_type: Game Type

Returns:
workflow definition"""
    # build template file path
    template_path = os.path.join(TEMPLATE_DIR, f"{game_type}.json")
    
    # Check if the file exists
    if not os.path.exists(template_path):
        logger.error(f"工作流模板不存在: {template_path}")
        raise FileNotFoundError(f"找不到游戏类型 {game_type} 的工作流模板")
    
    try:
        # Read workflow definition
        with open(template_path, 'r', encoding='utf-8') as f:
            workflow_definition = json.load(f)
        
        logger.info(f"成功加载工作流模板: {game_type}")
        return workflow_definition
    except Exception as e:
        logger.error(f"加载工作流模板失败: {str(e)}")
        raise


async def register_websocket(session_id: str, websocket: WebSocket) -> None:
    """Register WebSocket Connection

Args:
session_id: Session ID
WebSocket: WebSocket connection"""
    if session_id not in websockets:
        websockets[session_id] = set()
    
    # Remove the old same connection first (if any).
    if websocket in websockets[session_id]:
        websockets[session_id].remove(websocket)
        logger.info(f"移除会话 {session_id} 的旧WebSocket连接: {id(websocket)}")
    
    # Add new connection
    websockets[session_id].add(websocket)
    logger.info(f"WebSocket连接已注册: 会话ID={session_id}, 连接ID={id(websocket)}, 当前连接数={len(websockets[session_id])}")
    
    # Send a connection success confirmation message
    try:
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "message": "WebSocket connection established",
            "session_id": session_id,
            "connection_id": id(websocket),
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"已发送连接确认消息到客户端: {session_id}, 连接ID={id(websocket)}")
    except Exception as e:
        logger.error(f"发送连接确认消息失败: {str(e)}")


async def unregister_websocket(session_id: str, websocket: WebSocket) -> None:
    """Log out of WebSocket connection

Args:
session_id: Session ID
WebSocket: WebSocket connection"""
    if session_id in websockets and websocket in websockets[session_id]:
        websockets[session_id].remove(websocket)
        logger.info(f"WebSocket连接已注销: 会话ID={session_id}")


async def broadcast_message(session_id: str, message: Dict[str, Any]) -> None:
    """Broadcast messages to all WebSocket connections of the session

Args:
session_id: Session ID
Message: Message Content"""
    if session_id not in websockets:
        logger.warning(f"广播消息失败: 找不到会话ID {session_id} 的WebSocket连接")
        return
    
    logger.info(f"准备广播消息到会话 {session_id}, 连接数: {len(websockets[session_id])}")
    logger.info(f"消息内容: {message}")
    
    # Add message timestamp
    if isinstance(message, dict) and "timestamp" not in message:
        message["timestamp"] = datetime.now().isoformat()
    
    # Add Session ID
    if isinstance(message, dict) and "session_id" not in message:
        message["session_id"] = session_id
    
    # broadcast message
    disconnected_websockets = set()
    success_count = 0
    
    for ws in websockets[session_id]:
        try:
            await ws.send_json(message)
            success_count += 1
            logger.info(f"消息成功发送到WebSocket连接: {id(ws)}")
        except Exception as e:
            # Log error
            logger.error(f"发送消息到WebSocket连接失败: {id(ws)}, 错误: {str(e)}")
            # Mark broken connections
            disconnected_websockets.add(ws)
    
    # Remove broken connections
    for ws in disconnected_websockets:
        if session_id in websockets and ws in websockets[session_id]:
            websockets[session_id].remove(ws)
            logger.info(f"已移除断开的WebSocket连接: {id(ws)}")
    
    logger.info(f"消息广播完成: 成功 {success_count}/{len(websockets[session_id])} 个连接, 移除 {len(disconnected_websockets)} 个断开连接")


def create_node_factory_for_game_type(game_type: str) -> NodeFactory:
    """Create a node factory for the specified game type

Args:
game_type: Game Type

Returns:
Node Factory instance"""
    # Check if there is a node factory for this game type
    if game_type in node_factories:
        return node_factories[game_type]
    
    # Create a new node factory
    factory = NodeFactory()
    
    # Register base node type
    factory.register_node_type("message", MessageNode)
    factory.register_node_type("player_turn", PlayerTurnNode)
    
    # TODO: Register the corresponding node type according to the game type
    # Here we need to introduce node implementations for different game types
    
    # Storage Node Factory
    node_factories[game_type] = factory
    
    return factory


async def create_or_get_workflow_engine(game_type: str, workflow_definition: Dict[str, Any]) -> WorkflowEngine:
    """Create or acquire a workflow engine

Args:
game_type: Game Type
workflow_definition: Workflow Definition

Returns:
workflow engine instance"""
    # Check if there is a workflow engine for this game type
    if game_type in workflow_engines:
        engine = workflow_engines[game_type]
    else:
        # Create a new workflow engine
        node_factory = create_node_factory_for_game_type(game_type)
        engine = WorkflowEngine(node_factory=node_factory)
        workflow_engines[game_type] = engine
    
    # Make sure start_node is set
    start_node = workflow_definition.get("start_node")
    logger.info(f"工作流定义中的起始节点: {start_node}")
    
    # Load workflow definition
    engine.load_workflow(workflow_definition)
    
    # If start_node_id is not set, set it
    if not engine.start_node and start_node:
        engine.start_node = start_node
        logger.info(f"显式设置工作流起始节点: {start_node}")
    
    return engine


async def create_session(game_type: str, initial_context: Dict[str, Any]) -> str:
    """Create a new session

Args:
game_type: Game Type
initial_context: Initial Context

Returns:
Session ID"""
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Load workflow definition
    workflow_definition = await load_workflow_template(game_type)
    
    # Create a workflow engine
    engine = await create_or_get_workflow_engine(game_type, workflow_definition)
    
    # Create a session
    sessions[session_id] = {
        "game_type": game_type,
        "workflow_id": workflow_definition.get("id", ""),
        "context": initial_context,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "status": "created",
        "engine": engine
    }
    
    # Initializing the WebSocket Collection
    websockets[session_id] = set()
    
    logger.info(f"创建新会话: ID={session_id}, 游戏类型={game_type}")
    return session_id


async def get_random_roles(db: Session, count: int = 1) -> List[Dict[str, Any]]:
    """Randomly retrieve the specified number of roles from the database

Args:
DB: database session
Count: Number of characters to acquire

Returns:
role list"""
    try:
        # Create a character CRUD object
        role_db = RoleCRUD(db)
        
        # Acquire all roles
        all_roles = await role_db.get_all()
        
        if not all_roles:
            logger.warning("There are no roles available in the database, the default role is used")
            # Create default role
            return [
                {
                    "id": f"default_role_{i}",
                    "name": f"默认角色 {i}",
                    "model_id": "doubao-pro-32k-241215",
                    "setting": "I am a default character",
                    "system": "You are a friendly assistant",
                    "voice": "",
                    "role_info": {}
                }
                for i in range(count)
            ]
        
        # If the number of available roles is less than the required number, all are returned
        if len(all_roles) <= count:
            logger.info(f"可用角色数量({len(all_roles)})小于需要的数量({count})，返回所有可用角色")
            return all_roles
        
        # Randomly select a specified number of characters
        selected_roles = random.sample(all_roles, count)
        logger.info(f"从数据库中随机选择了 {count} 个角色")
        
        return selected_roles
    except Exception as e:
        logger.error(f"获取随机角色失败: {str(e)}")
        # Return to the default role when an error occurs
        return [
            {
                "id": f"default_role_{i}",
                "name": f"默认角色 {i}",
                "model_id": "doubao-pro-32k-241215",
                "setting": "I am a default character",
                "system": "You are a friendly assistant",
                "voice": "",
                "role_info": {}
            }
            for i in range(count)
        ]


@workflow_router.websocket("/ws/framework/workflow/{game_type}")
async def workflow_websocket_endpoint(
        websocket: WebSocket,
        game_type: str,
        db: Session = Depends(get_session)
):
    """Workflow Framework WebSocket Connection Endpoint

1. client side connection can provide session_id
2. If session_id does not exist, create a new workflow session
3. If session_id exists, restore the existing session
4. The message sent by the client side will be automatically passed to the workflow processing

Args:
WebSocket: WebSocket connection
game_type: Game Type
DB: database session"""
    logger.info(f"收到工作流框架WebSocket连接请求: 游戏类型={game_type}")
    
    # connection start time
    start_time = datetime.now()
    
    # Accept WebSocket connections
    try:
        await websocket.accept()
        logger.info(f"WebSocket连接已接受: 连接ID={id(websocket)}")
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connection",
            "status": "accepted",
            "message": "WebSocket connection accepted, waiting to be initialized",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"接受WebSocket连接失败: {str(e)}")
        return
    
    session_id = None
    try:
        # Parsing initialization data from the client
        init_data = await websocket.receive_json()
        logger.info(f"收到初始化数据: {init_data}")
        
        session_id = init_data.get("session_id")
        
        # Get the number of players
        player_count = init_data.get("player_count", 1)
        
        # Get a random list of roles from the database
        character_list = await get_random_roles(db, player_count)
        logger.info(f"为会话 {session_id} 获取了 {len(character_list)} 个角色")
        
        # Create initial context
        initial_context = {
            "game_type": game_type,
            "players": init_data.get("players", []),
            "user_data": init_data.get("user_data", {}),
            "roles": init_data.get("roles", []),
            "character_list": character_list,  # Add a list of roles to the context
            "session_id": session_id,
            # Add broadcast message function
            "broadcast_message": broadcast_message,
            # Add websockets dictionary
            "websockets": websockets
        }
        
        # Check if there is an existing session
        if not session_id or session_id not in sessions:
            # Create a new session
            new_session_id = await create_session(game_type, initial_context)
            if not session_id:
                session_id = new_session_id
                logger.info(f"创建新会话: ID={session_id}")
            else:
                logger.info(f"使用用户提供的会话ID: {session_id}")
                
            # Notify the client side that a session has been created
            await websocket.send_json({
                "type": "session_created",
                "session_id": session_id,
                "message": "Session created",
                "timestamp": datetime.now().isoformat()
            })
                
            # Register WebSocket Connection
            await register_websocket(session_id, websocket)
            
            # Get workflow engine
            engine = sessions[session_id]["engine"]
            
            # Add session ID to context
            initial_context["session_id"] = session_id
            
            # execution workflow
            try:
                logger.info(f"开始执行工作流: 会话ID={session_id}")
                result_data = await engine.execute_workflow(initial_context)
                logger.info(f"工作流初始执行完成: 会话ID={session_id}")
                
                # Update session context
                sessions[session_id]["context"].update(initial_context)
                sessions[session_id]["updated_at"] = datetime.now().isoformat()
                sessions[session_id]["status"] = "running"
            except Exception as e:
                logger.error(f"工作流执行失败: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                
                # Notify client side workflow execution failed
                await websocket.send_json({
                    "type": "workflow_error",
                    "message": f"工作流执行失败: {str(e)}",
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                })
        else:
            # Use an existing session
            logger.info(f"使用现有会话: ID={session_id}")
            
            # Notify the client side that the session is connected
            await websocket.send_json({
                "type": "session_connected",
                "session_id": session_id,
                "message": "Connected to an existing session",
                "timestamp": datetime.now().isoformat()
            })
            
            # Register WebSocket Connection
            await register_websocket(session_id, websocket)
            
            # Update session state
            sessions[session_id]["updated_at"] = datetime.now().isoformat()
            
            # Notify the workflow framework of new client side connections
            if "broadcast_message" in sessions[session_id]["context"]:
                await broadcast_message(session_id, {
                    "type": "client_connected",
                    "message": "New client side connected",
                    "timestamp": datetime.now().isoformat()
                })
        
        # Keep receiving messages
        try:
            while True:
                # Receive client side messages
                try:
                    # First try to receive a JSON message
                    data = await websocket.receive_json()
                    logger.info(f"接收到WebSocket JSON消息: {data}")
                except Exception as e:
                    # If that fails, try to receive a Text message
                    logger.info(f"JSON接收失败，尝试接收文本: {str(e)}")
                    raw_message = await websocket.receive_text()
                    logger.info(f"接收到WebSocket TEXT消息: {raw_message}")
                    
                    # Try to parse to JSON.
                    try:
                        data = json.loads(raw_message)
                    except json.JSONDecodeError:
                        # If it is not JSON, it is treated as a plain text message
                        data = {
                            "type": "user_message",
                            "content": raw_message.strip()
                        }
                
                try:
                    # View and record original data source structure
                    logger.info(f"收到消息数据结构: {data}")
                    
                    # Get the message content, note that it may be in multiple formats
                    message_content = ""
                    if "content" in data:
                        message_content = data.get("content")
                        logger.info(f"从content字段获取消息内容: {message_content}")
                    elif "message" in data:
                        message_content = data.get("message")
                        logger.info(f"从message字段获取消息内容: {message_content}")
                    
                    logger.info(f"最终提取的用户消息: '{message_content}'")
                    
                    # Prepare the context for the recovery workflow
                    resume_context = {
                        "user_message": message_content,  # Set up user messages
                        "session_id": session_id,
                        "broadcast_message": broadcast_message,
                        "websockets": websockets
                    }
                    
                    logger.info(f"创建恢复上下文: user_message='{resume_context.get('user_message')}'")
                    
                    try:
                        # Get workflow engine
                        engine = sessions[session_id]["engine"]
                        
                        # Send message processing acknowledgment
                        await websocket.send_json({
                            "type": "message_processing",
                            "message": "Your message is being processed.",
                            "content": message_content,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        # Resume workflow execution
                        logger.info(f"恢复会话 {session_id} 的工作流执行")
                        await resume_workflow(session_id, engine, resume_context)
                    except Exception as e:
                        logger.error(f"恢复工作流执行失败: {str(e)}")
                        import traceback
                        logger.error(traceback.format_exc())
                        
                        # Notify client side workflow execution failed
                        await websocket.send_json({
                            "type": "workflow_error",
                            "message": f"处理消息失败: {str(e)}",
                            "session_id": session_id,
                            "timestamp": datetime.now().isoformat()
                        })
                except Exception as e:
                    logger.error(f"处理消息失败: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    
                    # Notify client side message processing failed
                    try:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"处理消息失败: {str(e)}",
                            "timestamp": datetime.now().isoformat()
                        })
                    except Exception:
                        # If sending fails, the connection may be lost
                        logger.error("Failed to send error message, connection may have been lost")
                        break
        except Exception as e:
            # connection broken
            logger.warning(f"WebSocket连接中断: {str(e)}")
    except Exception as e:
        logger.error(f"WebSocket处理失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Log out of WebSocket connection
        if session_id:
            await unregister_websocket(session_id, websocket)
        
        # log connection time
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"WebSocket连接关闭: 持续时间={duration}秒")


async def resume_workflow(session_id: str, engine: WorkflowEngine, context: Dict[str, Any]) -> Dict[str, Any]:
    """Restore execution workflow

Args:
session_id: Session ID
Engine: Workflow Engine
Context: Context data

Returns:
Updated context data"""
    user_message = context.get("user_message", "")
    logger.info(f"恢复执行工作流：{session_id}, 用户消息: '{user_message}'")
    
    # Make sure the session ID and broadcast function are included in the context
    context["session_id"] = session_id
    context["broadcast_message"] = broadcast_message
    context["websockets"] = websockets
    
    # First confirm that the user message has been received.
    if user_message:
        try:
            await broadcast_message(session_id, {
                "type": "message_received",
                "message": f"服务器已收到消息: {user_message}",
                "status": "success"
            })
            logger.info(f"已向客户端确认收到消息: '{user_message}'")
        except Exception as e:
            logger.error(f"确认消息发送失败: {str(e)}")
    
    # Restore execution workflow
    try:
        # Resume workflow execution
        logger.info(f"恢复工作流执行，用户消息: {user_message}")
        result_data = await engine.resume_workflow(context)
        logger.info(f"工作流恢复执行完成: {session_id}")
        
        # Check if the workflow has been completed
        # Get the current node ID
        current_node_id = result_data.get("current_node_id")
        workflow_completed = False
        
        # If there is no current_node_id, the workflow may have ended
        if not current_node_id:
            workflow_completed = True
            logger.info(f"工作流 {session_id} 已执行完成 (没有current_node_id)")
        else:
            # Check if the current node has downstream connections
            has_downstream = (current_node_id in engine.connections and len(engine.connections[current_node_id]) > 0) or \
                            (current_node_id in engine.conditional_edges and len(engine.conditional_edges[current_node_id]) > 0)
            
            if not has_downstream:
                workflow_completed = True
                logger.info(f"工作流 {session_id} 已执行完成 (当前节点没有下游连接)")
        
        # If the workflow has completed, send an end message and update the session status
        if workflow_completed:
            try:
                # Notify the client side that the workflow is complete
                await broadcast_message(session_id, {
                    "type": "workflow_completed",
                    "message": "Workflow completed",
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"已向客户端发送工作流完成消息: {session_id}")
                
                # Update session state
                if session_id in sessions:
                    sessions[session_id]["status"] = "completed"
                    sessions[session_id]["completed_at"] = datetime.now().isoformat()
                    logger.info(f"会话 {session_id} 状态已更新为已完成")
            except Exception as e:
                logger.error(f"发送工作流完成消息失败: {str(e)}")
        
        # Update session context - preserves workflow state, but clears processed user messages
        if session_id in sessions:
            # Update all fields, but make sure to clear user_message
            sessions[session_id]["context"].update(result_data)
            sessions[session_id]["updated_at"] = datetime.now().isoformat()
            
            # Clear user messages to ensure that the next execution will not be repeated
            if "user_message" in sessions[session_id]["context"]:
                del sessions[session_id]["context"]["user_message"]
        
        # Return result
        return result_data
    except Exception as e:
        logger.error(f"恢复工作流执行失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise 