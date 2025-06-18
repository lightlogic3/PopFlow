from sqlmodel import Session

from knowledge_api.mapper.roles.crud import RoleCRUD
from knowledge_api.mapper.world.crud import WorldCRUD
from knowledge_api.utils.log_config import get_logger

logger = get_logger()


async def role_knowledge_count(db: Session, role_id: str, count: int = 1):
    role_db = RoleCRUD(db)
    await role_db.increment_knowledge_count(role_id=role_id, count=count)
    logger.info("The character knowledge base information is entered, and the background task execution is completed!")


async def world_knowledge_count(db: Session, world_id: str, count: int = 1):
    world_db = WorldCRUD(db)
    await world_db.increment_knowledge_count(id=world_id, count=count)
    logger.info("The world knowledge base information is entered, and the background task execution is completed!")
