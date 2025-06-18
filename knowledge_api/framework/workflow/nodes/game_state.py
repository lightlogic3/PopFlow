"""game state node
Responsible for game initialization and state management"""

from typing import Dict, Any, List, Optional
import random
from knowledge_api.framework.workflow.model.node import Node
from knowledge_api.framework.workflow.model.node_status import NodeStatus
from knowledge_api.framework.workflow.types import WorkflowContext
from knowledge_api.mapper.roles.base import Role
from knowledge_api.model.agent.game_agent import BaseGameAgent, GameRole
from knowledge_api.utils.log_config import get_logger

logger = get_logger()

class GameStateNode(Node):
    """Game state node, which must be the first node in the workflow
Responsible for initializing game states and player agents"""
    
    # Node type identifier
    node_type: str = "game_state"
    
    # node description
    description: str = "Game state initialization node"
    
    def __init__(self, id: str, name: str, config: Dict[str, Any]):
        """Initialize the game state node

Args:
ID: Node ID
Name: Node name
Config: Node configuration, which must contain the following fields:
- state_storage: state storage method, such as "memory"
- initial_state: Initial game state, including game type, state, etc"""
        super().__init__(id, name, self.node_type, config)
        
        # authentication configuration item
        self._validate_config()
        
        # initialization state store
        self.state_storage = config.get("state_storage", "memory")
        self.initial_state = config.get("initial_state", {})
        
        # Current game state
        self.game_state = self.initial_state.copy()
        
        # Set to initialized state
        self.status = NodeStatus.IDLE
    
    def _validate_config(self) -> None:
        """Verify that the node configuration is valid"""
        if "initial_state" not in self.config:
            raise ValueError("Game state node configuration must contain initial_state fields")
        
        initial_state = self.config["initial_state"]
        if not isinstance(initial_state, dict):
            raise ValueError("initial_state must be a dictionary type")
        
        # Check the necessary initial status fields
        required_fields = ["game_type", "status", "min_players", "max_players"]
        for field in required_fields:
            if field not in initial_state:
                raise ValueError(f"initial_state 必须包含 {field} 字段")
    
    async def process(self, context: WorkflowContext) -> Dict[str, Any]:
        """Handling node logic

Args:
Context: workflow context

Returns:
updated context"""
        logger.info(f"GameStateNode开始处理: {self.id}")
        
        try:
            # Make sure this is the first node in the workflow
            if not self._is_first_node(context):
                raise ValueError("The game state node must be the first node in the workflow")
            
            # Get a list of roles
            character_list = context.data.get("character_list", None)
            
            # validation role list
            if character_list is None:
                error_message = "Necessary parameters are missing: character_list"
                logger.error(error_message)
                raise ValueError(error_message)
            
            if not isinstance(character_list, list):
                error_message = "character_list must be a list type"
                logger.error(error_message)
                raise ValueError(error_message)
            
            # Number of verified players
            min_players = self.initial_state.get("min_players", 1)
            max_players = self.initial_state.get("max_players", 8)
            
            if len(character_list) < min_players:
                error_message = f"玩家数量不能少于 {min_players} 人"
                logger.error(error_message)
                raise ValueError(error_message)
            
            if len(character_list) > max_players:
                error_message = f"玩家数量不能超过 {max_players} 人"
                logger.error(error_message)
                raise ValueError(error_message)
            
            # Initialize game state
            game_state = self.initial_state.copy()
            
            # Create a player agent
            players = await self._create_players(character_list, game_state)
            # Update game status
            game_state["players"] = players
            # Set the status to initialized
            game_state["status"] = "initialized"
            game_state["round"] = 0
            
            # Initialize the resulting dictionary to include the complete game state
            result = {"state": game_state, "players": players}
            
            # Add all top-level fields in game_state to result as well
            for key, value in game_state.items():
                # Avoid overwriting existing fields
                if key not in result:
                    result[key] = value
                    logger.debug(f"添加游戏状态字段到上下文: {key}")
            
            # Save current state
            self.game_state = game_state
            
            # Set node status to complete
            self.status = NodeStatus.COMPLETED
            
            # Important: Update the results to the global context so that other nodes can access them
            context.data.update(result)
            
            logger.info(f"GameStateNode处理完成: {self.id}")
            logger.info(f"已将游戏状态更新到全局上下文: state字段={len(game_state)}个, players={len(players)}个")
            
            return result
        
        except Exception as e:
            error_message = f"游戏状态节点处理失败: {str(e)}"
            logger.error(error_message)
            self.status = NodeStatus.FAILED
            self._error_message = error_message
            raise
    
    def _is_first_node(self, context: WorkflowContext) -> bool:
        """Check if it is the first node of the workflow

Args:
Context: workflow context

Returns:
Is it the first node?"""
        # Additional logic can be added here to ensure that this is the first node to execute
        return len(self.upstream_nodes) == 0
    
    async def _create_players(self, character_list: List[Role], game_state: Dict[str, Any]) -> List[BaseGameAgent]:
        """Create player agents based on character lists

Args:
character_list: Character List
game_state: Game Status

Returns:
Player Agent List"""
        players = []
        default_model_id = game_state.get("default_model_id", "doubao-pro-32k-241215")
        
        # Get a list of characters, if present
        characters = game_state.get("characters", [])
        logger.info(f"游戏中指定的角色: {characters}")
        
        # Create a list of roles
        game_roles = []
        if characters:
            for char_id in characters:
                # Create a special character
                game_role = GameRole(
                    role_id=char_id,
                    model_id=default_model_id,
                    setting="",
                    voice="",
                    role_info=None
                )
                game_role.identity = char_id  # Set identity to role ID
                game_roles.append(game_role)
                logger.info(f"创建游戏角色: {char_id}")
        
        # If no character is specified or the number of characters is insufficient, all players are normal players
        if not game_roles:
            for character in character_list:
                model_id=default_model_id
                if character.llm_choose:
                    model_id=character.llm_choose
                # Create role
                role = GameRole(
                    role_id=character.role_id,
                    model_id=model_id,
                    setting="",
                    voice="",
                    role_info=character
                )
                
                # Create an agent
                agent = BaseGameAgent(role)
                agent.identity = "player"  # Default setting is player identity
                
                # Initialize client side asynchronously
                await agent.init_client()
                
                # Add to player list
                players.append(agent)
        else:
            # If there are special characters, each player is assigned a role
            # If the number of special characters is less than the number of players, the extra players are set to normal players
            
            # randomly scramble the character list
            random.shuffle(game_roles)
            
            # Assign roles to each player
            for i, character in enumerate(character_list):
                model_id=default_model_id
                if character.llm_choose:
                    model_id=character.llm_choose
                
                # If a special character is available, use it
                if i < len(game_roles):
                    role = game_roles[i]
                    role.model_id = model_id
                    role.role_info = character
                    identity = role.identity
                else:
                    # Otherwise create a normal player
                    role = GameRole(
                        role_id=character.role_id,
                        model_id=model_id,
                        setting="",
                        voice="",
                        role_info=character
                    )
                    identity = "player"
                
                # Create an agent
                agent = BaseGameAgent(role)
                agent.identity = identity
                
                # Initialize client side asynchronously
                await agent.init_client()
                
                # Add to player list
                players.append(agent)
                logger.info(f"为玩家 {character.role_id} 分配身份: {identity}")
        
        return players
        
    def _render_template(self, template: str, data: Dict[str, Any]) -> str:
        """Render template string

Replace variables in the template with actual values

Args:
Template: template string
Data: Variable data

Returns:
Rendered string"""
        # Use regular expressions to find all variable placeholders
        pattern = r"{{(.*?)}}"
        
        def replace_var(match):
            var_name = match.group(1).strip()
            var_value = data.get(var_name)
            
            if var_value is None:
                logger.warning(f"变量 {var_name} 不存在，使用空字符串代替")
                return ""
            
            return str(var_value)
        
        # Replace all variables
        import re
        result = re.sub(pattern, replace_var, template)
        
        return result 