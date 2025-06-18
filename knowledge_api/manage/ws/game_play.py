# app.py
from fastapi import WebSocket, WebSocketDisconnect, Depends, APIRouter
from datetime import datetime

from knowledge_api.game_play import GameFactory
from knowledge_api.game_task.bask_task import BaseTask
from knowledge_api.mapper.chat_session.base import Session
from knowledge_api.framework.database.database import get_session
from knowledge_api.utils.log_config import get_logger
from knowledge_api.model.task_game_model import TaskGameInput

logger = get_logger()
wx_manage_router = APIRouter(tags=["instant message"])


@wx_manage_router.websocket("/ws/game/{game_type}/{task_id}/{play_type}")
async def game_websocket_endpoint(
        websocket: WebSocket,
        game_type: str,
        task_id: str,
        play_type: str = "task",
        db: Session = Depends(get_session)
):
    """Game WebSocket Connect Endpoints - Turtle Soup Game

1. The front end only needs to provide session_id establish the connection
2. Automatically create a new game when the session does not exist
3. Restore historical games when the session exists
4. Users only need to send human messages, and the server automatically handles AI rounds and game flows

Args:
WebSocket: WebSocket connection
game_type: Game Type (Example: turtle_soup)
task_id: Task ID
play_type: Type of play
DB: database session"""
    logger.info(f"收到游戏WebSocket连接请求: 游戏类型={game_type}, 任务ID={task_id}")
    await websocket.accept()

    game = None
    session_id = None
    try:
        # Parsing initialization data from the client
        init_data = await websocket.receive_json()
        session_id = init_data.get("session_id")

        # If no session ID is provided, an error is returned
        if not session_id:
            await websocket.send_json({
                "error": "Missing session_id parameters",
                "status": "error"
            })
            await websocket.close()
            return
            # build task input
        task_input = TaskGameInput(
            task_id=task_id,
            session_id=session_id,
            game_type=game_type,
            user_info=init_data.get("user_data"),
            roles=init_data.get("roles")
        )
        logger.info(f"处理游戏会话: 游戏类型={game_type}, 任务ID={task_id}, 会话ID={session_id}")
        if play_type == "task":
            # Create game instances with GameFactory
            task = BaseTask(db, task_input, game_type)
            await task.init_task()
            game = task.game
            # Register WebSocket Connection
            await game.register_websocket(session_id, websocket)
            logger.info(f"WebSocket连接注册成功: 会话ID={session_id}")
            await task.play_game(websocket)
        else:
            game = await GameFactory.create_game(game_type, db, task_input)
            await game.register_websocket(session_id, websocket)
            logger.info(f"WebSocket连接注册成功:开始游戏玩法 会话ID={session_id}")
            await game.play_game(websocket)

    except WebSocketDisconnect:
        logger.info(f"WebSocket连接断开: 会话ID={session_id if session_id else '未知'}")

    except Exception as e:
        logger.error(f"游戏WebSocket处理错误: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # Attempt to send an error message
        try:
            await websocket.send_json({
                "error": str(e),
                "status": "error"
            })
        except:
            pass  # Ignore the sending error if the connection has been disconnected

    finally:
        # Make sure to log out of WebSocket when the connection is disconnected
        if game and session_id:
            try:
                await game.unregister_websocket(session_id, websocket)
                logger.info(f"WebSocket连接已注销: 会话ID={session_id}")
            except Exception as e:
                logger.error(f"注销WebSocket错误: {str(e)}")

