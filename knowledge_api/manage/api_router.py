from fastapi import APIRouter

from knowledge_api.config import API_PREFIX
from knowledge_api.manage.api import role_knowledge_api, world_knowledge_api
from knowledge_api.manage.api.audio_timbre_api import router_audio_timbre
from knowledge_api.manage.api.character_prompt_config_api import router_role_prompt
from knowledge_api.manage.api.character_test import character_prompt_router
from knowledge_api.manage.api.conversation_api import router_conversation
from knowledge_api.manage.api.game_play_type_api import router_game_play_type
from knowledge_api.manage.api.llm_provider_config_api import llm_config_router
from knowledge_api.manage.api.llm_model_config_api import llm_model_router
from knowledge_api.manage.api.llm_usage_records_api import llm_usage_records_router
from knowledge_api.manage.api.task_game_messages_api import task_game_messages_router
from knowledge_api.manage.api.llm_router import llm_router
from knowledge_api.manage.api.relationship_level_api import router_relationship_level
from knowledge_api.manage.api.role_api import router_role
from knowledge_api.manage.api.role_task_api import router_role_task
from knowledge_api.manage.api.role_subtask_api import router_role_subtask
from knowledge_api.manage.api.session_api import router_session
from knowledge_api.manage.api.system.system_config_api import router_system_config
from knowledge_api.manage.api.task_api import router_task
from knowledge_api.manage.api.task_game_sessions_api import task_game_sessions_router
from knowledge_api.manage.api.task_manage_api import router_task_manage
from knowledge_api.manage.api.tts_api import router_tts
from knowledge_api.manage.api.user_blind_box_stats_api import router_user_blind_box_stats
from knowledge_api.manage.api.world_api import router_world
from knowledge_api.manage.api.roles_world_api import router_roles_world
from knowledge_api.manage.api.router import router as api_router
from knowledge_api.manage.ws.workflow_play import workflow_router
from knowledge_api.manage.api.auth_api import router_auth
from knowledge_api.manage.api.system.system_user_api import router_system_user
from knowledge_api.manage.api.system.system_role_api import router_system_role
from knowledge_api.manage.api.system.system_menu_api import router_system_menu
from knowledge_api.manage.api.oss_api import router_oss
from knowledge_api.manage.api.user_detail_api import router_user_detail
from knowledge_api.manage.api.point_record_api import router_point_record
from knowledge_api.manage.api.card_series_api import router_card_series
from knowledge_api.manage.api.card_api import router_card
from knowledge_api.manage.api.blind_box_api import router
from knowledge_api.manage.api.blind_box_card_api import router as blind_box_card_router
from knowledge_api.manage.api.user_card_api import router_user_card
from knowledge_api.manage.api.card_usage_record_api import router_card_usage_record
from knowledge_api.manage.api.blind_box_record_api import router_blind_box_record
from plugIns.router import plugIn_router
from knowledge_api.manage.api.memory_router import router as memory_router
manage_router = APIRouter(prefix=API_PREFIX)

manage_router.include_router(memory_router)

manage_router.include_router(api_router)

manage_router.include_router(router_system_config)

manage_router.include_router(router_role_prompt, prefix="/role_prompt")

manage_router.include_router(llm_config_router, prefix="/llm_config_router")
manage_router.include_router(llm_model_router)
manage_router.include_router(llm_usage_records_router)
manage_router.include_router(task_game_messages_router)

manage_router.include_router(router_role)
manage_router.include_router(router_world)
manage_router.include_router(router_roles_world)
manage_router.include_router(router_session)
manage_router.include_router(router_conversation)
manage_router.include_router(world_knowledge_api.router_world_knowledge)
manage_router.include_router(router_audio_timbre)

manage_router.include_router(role_knowledge_api.router_role_knowledge)
manage_router.include_router(router_relationship_level)
manage_router.include_router(router_role_task)
manage_router.include_router(router_role_subtask)
manage_router.include_router(router_tts)

# multi-role task management
manage_router.include_router(router_task)

# timed task management
manage_router.include_router(router_task_manage)
manage_router.include_router(task_game_sessions_router)
manage_router.include_router(character_prompt_router, prefix="/test", tags=["test"])
# manage_router.include_router(mock)
# Gameplay, multi-role management
manage_router.include_router(router_game_play_type)

# Workflow Engine WebSocket
manage_router.include_router(workflow_router)

manage_router.include_router(llm_router)



# Registration system management related routes
manage_router.include_router(router_auth)
manage_router.include_router(router_system_user)
manage_router.include_router(router_system_role)
manage_router.include_router(router_system_menu)
manage_router.include_router(router_oss)

# Registered User Details Management Routing
manage_router.include_router(router_user_detail)

# Registration Credits Records Management Routing
manage_router.include_router(router_point_record)

# Registered Card Management Related Routing
manage_router.include_router(router_card_series)
manage_router.include_router(router_card)

# Register blind box management related routes
manage_router.include_router(router)
manage_router.include_router(blind_box_card_router)

# Registered user card management routing
manage_router.include_router(router_user_card)

# Registration Card Usage Record Management Routing
manage_router.include_router(router_card_usage_record)

# Registration blind box extraction record management routing
manage_router.include_router(router_blind_box_record)
manage_router.include_router(router_user_blind_box_stats)


# integrated plug-in
manage_router.include_router(plugIn_router)
