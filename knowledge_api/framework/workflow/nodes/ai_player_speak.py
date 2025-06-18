"""AI player speaking node"""
import random
from typing import Dict, Any

from knowledge_api.framework.workflow.model.node import Node
from knowledge_api.framework.workflow.model.node_status import NodeStatus
from knowledge_api.utils.log_config import get_logger

# Initialize the logger
logger = get_logger()

class AIPlayerSpeakNode(Node):
    """AI player speaking node, used to let AI characters speak

Configuration parameters:
- speech_template: speech content template
- memory_roles: List of characters who need to add memories
- speaker_id: Speaker ID ("random", "none" or specific character ID)
- character_setting: Character Template
- system_message: System Message Template

Input:
- Supports arbitrary names and numbers of input parameters that will be used to replace variables in the template

Output:
- message: AI speech content
- memory_roles: Memory character list"""
    # Node type identifier
    node_type: str = "ai_player_speak"
    def __init__(self, id: str, name: str, config: Dict[str, Any]):
        """Initialize the AI player speech node

Supports two parameter modes:
1. (id, name, config) - For creating directly from the engine
2. (id, name, component_type, config) - for creating from a loop node

Args:
ID: Node ID
Name: Node name
Args: Variable argument, may be config or (component_type, config)"""
        # Call the parent class constructor
        super().__init__(id, name, self.node_type, config)
        
        self.speech_template = config.get("speech_template", "")
        self.memory_roles = config.get("memory_roles", [])
        self.speaker_id = config.get("speaker_id", "random")
        self.character_setting = config.get("character_setting", "")
        self.system_message = config.get("system_message", "")
    
    async def process(self, context):
        """Processing AI player speaking nodes

Args:
Context: workflow context

Returns:
processing result"""
        logger.info(f"AI玩家发言节点 {self.id} 处理开始")
        
        # Check the context type and get the data
        try:
            if hasattr(context, 'data') and isinstance(context.data, dict):
                # If it is a WorkflowContext object
                context_data = context.data
            elif isinstance(context, dict):
                # If it is an ordinary dictionary
                logger.info(f"AI玩家发言节点 {self.id} 收到字典对象而非 WorkflowContext")
                context_data = context
            else:
                logger.error(f"AI玩家发言节点 {self.id} 收到未知类型的上下文: {type(context)}")
                self.status = NodeStatus.ERROR
                return {
                    "error": f"未知的上下文类型: {type(context)}"
                }
        except Exception as e:
            logger.error(f"AI玩家发言节点 {self.id} 处理上下文时发生异常: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            self.status = NodeStatus.ERROR
            return {
                "error": f"处理上下文时发生异常: {str(e)}"
            }
        
        # Get Node Input
        input_data = context_data.get("current_node_inputs", {})
        
        # Log all input variables for debugging
        logger.info(f"AI玩家发言节点 {self.id} 收到的输入变量键: {list(input_data.keys())}")
        
        # Analyze template variables in all configurations
        def extract_template_vars(template):
            """Extract all variable names from template string"""
            if not template:
                return []
            import re
            vars = re.findall(r'{{(.*?)}}', template)
            return [v.strip() for v in vars]
        
        # Collect variables used in all templates
        all_template_vars = set()
        for template_name, template_content in [
            ('character_setting', self.character_setting),
            ('system_message', self.system_message),
            ('speech_template', self.speech_template)
        ]:
            vars = extract_template_vars(template_content)
            if vars:
                all_template_vars.update(vars)
                logger.info(f"{template_name}模板需要的变量: {vars}")
        
        # Check if template variables are accessible
        if all_template_vars:
            logger.info(f"所有模板共需要的变量: {list(all_template_vars)}")
            for var in all_template_vars:
                var_parts = var.split('.')
                if len(var_parts) == 1:
                    # direct field
                    if var in input_data:
                        logger.debug(f"找到直接变量: {var}")
                else:
                    # nested field
                    parent = var_parts[0]
                    if len(var_parts) > 1 and parent in input_data and isinstance(input_data[parent], dict):
                        logger.debug(f"找到嵌套变量的父字段: {parent}")
        
        # Output key debugging information
        logger.info(f"当前speaker_id设置为: {self.speaker_id}")
        logger.info(f"上下文数据键: {list(context_data.keys())}")
        if "_loop" in context_data:
            logger.info(f"_loop数据: {context_data['_loop']}")
        
        # Render all templates
        rendered_character_setting = self.render_template(self.character_setting, input_data) if self.character_setting else ""
        rendered_system_message = self.render_template(self.system_message, input_data) if self.system_message else ""
        
        # Examine the players data structure in the context
        players = context_data.get("players", [])
        logger.info(f"players列表长度: {len(players)}")
        
        if len(players) > 0:
            # Show the attributes of the first player
            player0 = players[0]
            logger.info(f"第一个玩家类型: {type(player0)}")
            logger.info(f"第一个玩家属性: chat={hasattr(player0, 'chat')}, identity={hasattr(player0, 'identity')}")
        else:
            logger.warning(f"AI玩家发言节点 {self.id} 无法找到玩家列表")
            self.status = NodeStatus.ERROR
            return {
                "error": "Player list is empty"
            }
        
        # Determine the list of speakers
        speaking_players = []
        
        # Marks whether a speaker has been found (for controlling flow)
        found_speaker = False
        
        # Checks if it is in a loop and the current item is available
        if self.is_in_loop_context(context):
            loop_item = self.get_loop_item(context)
            logger.info(f"检测到循环上下文，迭代项: {loop_item}")
            
            # If speaker_id is set to none, try using a loop item
            if self.speaker_id == "none":
                # Use the base class method to check if it is a GameRole object
                if self.is_game_role(loop_item):
                    logger.info(f"循环迭代器中的对象是GameRole，将作为发言者: {getattr(loop_item, 'name', '未知')}")
                    speaking_players = [loop_item]
                    found_speaker = True
                else:
                    logger.info(f"循环迭代项不是GameRole对象: {type(loop_item)}")
                    
                    # Additional check, if the loop item has an identity attribute, it may be a GameRole.
                    if hasattr(loop_item, "identity"):
                        logger.info(f"循环迭代项具有identity属性: {getattr(loop_item, 'identity', '未知')}")
                        
                        # Attempt to present this object as a speaker
                        if hasattr(loop_item, "name"):
                            logger.info(f"尝试使用带有identity和name属性的对象作为发言者")
                            speaking_players = [loop_item]
                            found_speaker = True
                    
                    # Try to view the properties of the loop item to assist in debugging
                    for attr_name in ["type", "role", "name", "__class__"]:
                        if hasattr(loop_item, attr_name):
                            logger.info(f"循环迭代项属性 {attr_name}: {getattr(loop_item, attr_name)}")
        else:
            logger.info("Does not execute in a loop context")
        
        # If a speaker is found in the loop, you can return early
        if found_speaker and speaking_players:
            logger.info(f"已在循环上下文中找到发言者: {len(speaking_players)} 个")
        # If it is not a loop situation, or there is no suitable item in the loop
        if not speaking_players:
            if self.speaker_id == "random":
                # Check if there is a GameRole object in the inputs
                has_game_role = False
                for key, value in input_data.items():
                    if hasattr(value, "chat") and callable(getattr(value, "chat")):
                        has_game_role = True
                        break
                    elif isinstance(value, list):
                        for item in value:
                            if hasattr(item, "chat") and callable(getattr(item, "chat")):
                                has_game_role = True
                                break
                
                if not has_game_role:
                    # Choose one of the players at random
                    if players:
                        selected_player = random.choice(players)
                        speaking_players = [selected_player]
                        logger.info(f"随机选择玩家作为发言者: {getattr(selected_player, 'name', '未知')}")
            
            elif self.speaker_id == "none":
                # Finding GameRole objects from inputs
                for key, value in input_data.items():
                    if hasattr(value, "chat") and callable(getattr(value, "chat")):
                        speaking_players.append(value)
                    elif isinstance(value, list):
                        for item in value:
                            if hasattr(item, "chat") and callable(getattr(item, "chat")):
                                speaking_players.append(item)
                
                if not speaking_players:
                    logger.info(f"speaker_id为none但未找到GameRole对象，节点不执行任何操作")
                    self.status = NodeStatus.COMPLETED
                    return {
                        "message": "",
                        "memory_roles": []
                    }
            
            else:
                # Filter from players by specified speaker_id
                for player in players:
                    if hasattr(player, "identity") and player.identity == self.speaker_id:
                        speaking_players.append(player)
                
                if not speaking_players:
                    logger.warning(f"未找到identity为{self.speaker_id}的玩家")
        
        if not speaking_players:
            logger.warning(f"未能确定发言玩家")
            self.status = NodeStatus.ERROR
            return {
                "error": "Unable to identify speaker"
            }
        
        # Determine message content
        message_content = ""
        if self.speech_template:
            # Format with template
            message_content = self.render_template(self.speech_template, input_data)
            logger.info(f"渲染后的发言内容: {message_content[:100]}")
        
        # Save all speeches
        all_messages = []
        
        # Handle each speaker
        for player in speaking_players:
            # Update system settings
            if rendered_system_message or rendered_character_setting:
                system_setting = f"{rendered_system_message} {rendered_character_setting}".strip()
                if hasattr(player, "memory") and hasattr(player.memory, "update_system_message"):
                    player.memory.update_system_message(system_setting)
                    logger.info(f"更新玩家系统设定: {system_setting}")
            
            # Send message
            if hasattr(player, "chat") and callable(player.chat):
                try:
                    response = await player.chat(message_content)
                    all_messages.append(response)
                    logger.info(f"玩家 {getattr(player, 'name', '未知')} 发言: {response}")
                except Exception as e:
                    logger.error(f"玩家发言失败: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
            else:
                logger.warning(f"玩家对象没有chat方法")
        
        # Update the memories of other characters
        updated_memory_roles = []
        if all_messages and self.memory_roles:
            # Get the last message as memory content
            memory_content = all_messages[-1]
            
            # Get the identity of the current speaking player
            current_speaker_identities = []
            for player in speaking_players:
                if hasattr(player, "identity"):
                    current_speaker_identities.append(player.identity)
            
            # Update the memories of other players
            for player in players:
                # skip itself
                if hasattr(player, "identity") and player.identity in current_speaker_identities:
                    continue
                
                # Check if the player's memory needs to be updated
                should_update = False
                if "ALL" in self.memory_roles:
                    should_update = True
                elif hasattr(player, "identity") and player.identity in self.memory_roles:
                    should_update = True
                
                if should_update and hasattr(player, "memory") and hasattr(player.memory, "add"):
                    # Add a message to the memory of the intended character
                    try:
                        player.memory.add(memory_content)
                        updated_memory_roles.append(getattr(player, "identity", "unknown"))
                        logger.info(f"已更新玩家 {getattr(player, 'name', '未知')} 的记忆")
                    except Exception as e:
                        logger.error(f"更新玩家记忆失败: {str(e)}")
        
        # Set the status to complete
        self.status = NodeStatus.COMPLETED
        
        # Return result
        return {
            "message": "\n".join(all_messages),
            "memory_roles": updated_memory_roles
        } 