from typing import Dict, Type

from knowledge_api.manage.game_knowledge.services.rag_service import RAGService
from knowledge_api.manage.game_knowledge.services.role_rag_service import RoleRAGService
from knowledge_api.manage.game_knowledge.services.world_rag_service import WorldRAGService
from knowledge_api.utils.log_config import get_logger

logger = get_logger()

class RAGManager:
    """RAG management center for centralized management and access to different types of RAG services"""
    # singleton
    _instance = None
    
    # Registered service types
    _service_types = {
        "role": RoleRAGService,
        "world": WorldRAGService,
    }
    
    # active service instance
    _active_services = {}
    
    def __new__(cls):
        """Ensure Singleton Pattern"""
        if cls._instance is None:
            cls._instance = super(RAGManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        """Initialize RAG Management Center (only executed once)"""
        if getattr(self, "_initialized", False):
            return
            
        logger.info("Initialize RAG Management Center")
        self._initialized = True
        
    @classmethod
    def register_service_type(cls, name: str, service_class: Type[RAGService]):
        """Register a new RAG service type

Args:
Name: service type name
service_class: Services"""
        if name in cls._service_types:
            logger.warning(f"服务类型 {name} 已存在，将被覆盖")
            
        cls._service_types[name] = service_class
        logger.info(f"已注册服务类型: {name}")
        
    async def get_service(self, service_type: str, **kwargs) -> RAGService:
        """Get a RAG service instance of the specified type

Args:
service_type: Service Type Name
** kwargs: service initialization parameters

Returns:
RAG service example"""
        # Create cache key
        cache_key = service_type
        if "collection_name" in kwargs:
            cache_key = f"{service_type}:{kwargs['collection_name']}"
            
        # Check if the service already exists
        if cache_key in self._active_services:
            logger.info(f"使用现有的RAG服务: {cache_key}")
            return self._active_services[cache_key]
            
        # Get service class
        if service_type not in self._service_types:
            raise ValueError(f"未注册的服务类型: {service_type}")
            
        service_class = self._service_types[service_type]
        
        # Create a new service instance
        logger.info(f"创建新的RAG服务: {cache_key}")
        service = service_class(**kwargs)
        
        # initialization service
        await service.initialize()
        
        # caching service instance
        self._active_services[cache_key] = service
        
        return service
        
    def get_available_service_types(self) -> Dict[str, str]:
        """Get the available service types

Returns:
Service Type Dictionary {Name: Description}"""
        return {name: service_class.__doc__ or "" for name, service_class in self._service_types.items()}
        
    async def close_all(self):
        """Shut down all active services"""
        for service_name, service in self._active_services.items():
            logger.info(f"关闭RAG服务: {service_name}")
            await service.close()
            
        self._active_services.clear()
        
    async def close_service(self, service_type: str):
        """Close all services of the specified type

Args:
service_type: Service Type Name"""
        services_to_close = [name for name in list(self._active_services.keys()) if name.startswith(service_type)]
        
        for name in services_to_close:
            logger.info(f"关闭RAG服务: {name}")
            await self._active_services[name].close()
            del self._active_services[name] 