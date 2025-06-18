from knowledge_api.framework.workflow.nodes.function_tool import FunctionToolNode
from knowledge_api.framework.workflow.nodes.message import MessageNode
from knowledge_api.framework.workflow.nodes.player_turn import PlayerTurnNode
from knowledge_api.framework.workflow.nodes.conditional import ConditionalNode
from knowledge_api.framework.workflow.nodes.game_state import GameStateNode
from knowledge_api.framework.workflow.nodes.loop import LoopNode
from knowledge_api.framework.workflow.nodes.ai_player_speak import AIPlayerSpeakNode

node_registry = {
    "message": MessageNode,
    "player_turn": PlayerTurnNode,
    "conditional": ConditionalNode,
    "game_state": GameStateNode,
    "function_tool": FunctionToolNode,
    "loop": LoopNode,
    "ai_player_speak": AIPlayerSpeakNode,
}