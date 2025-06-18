from typing import Type, Dict, List, Optional

from knowledge_api.framework.ai_collect.base_llm import BaseLLM



class LLMFactory:
    """@Description LLM factory class, create different LLM instances based on the AI name"""
    # Chinese name mapping
    _name_mapping = {
        "bean buns": "doubao",
        "doubao": "doubao",
        "ERNIE Bot": "erniebot",
        "Wenxin": "erniebot",
        "kimi": "kimi",
        "moonshot": "kimi",
        "deepseek": "deepseek",
    }
    
    @classmethod
    def get_available_llms(cls) -> List[str]:
        """@Description Get all available LLM types
@Returns {List [str]} LLM type list"""
        return list(BaseLLM._registry.keys())
    

    @classmethod
    def create_llm(cls, ai_name: str, model: str, api_key: str, base_url: str = None,
                   format_response: bool = True) -> BaseLLM:
        """@Description Factory method for creating LLM instances
@Param {string} ai_name - AI name to determine the LLM subclass to instantiate
@param {string} model - model name
@Param {string} api_key - Key required to access API
@Param {string} base_url - optional, base URL for model API
@Param {boolean} format_response - optional, whether to format the model's response
@Returns {BaseLLM} an instance of a model-specific subclass"""
        # Handling Chinese names or aliases
        if ai_name is None:
            ai_name="all"
        ai_name_lower = ai_name.lower()
        llm_type = None
        
        # Check if it matches regedit directly
        if ai_name_lower in BaseLLM._registry:
            llm_type = ai_name_lower
        else:
            # Check Chinese name mapping
            for name, mapped_type in cls._name_mapping.items():
                if name in ai_name_lower:
                    llm_type = mapped_type
                    break
        
        # If no matching LLM type is found, use the default implementation
        if llm_type is None or llm_type not in BaseLLM._registry:
            print(f"LLM类型 '{ai_name}' 未找到。使用示例LLM作为后备。")
            llm_type = "example"
        
        # Get the LLM class and instantiate it
        model_class: Type[BaseLLM] = BaseLLM._registry[llm_type]
        
        # Create an LLM instance
        return model_class(api_key=api_key, base_url=base_url, model=model, format_response=format_response)
    
    @classmethod
    def create_llm_from_cache(cls, llm_type: str, format_response: bool = True) -> Optional[BaseLLM]:
        """@Description Factory method for creating LLM instances from cache
@Param {string} llm_type - LLM type name or provider name
@Param {boolean} format_response - optional, whether to format the model's response
@Returns {BaseLLM} an instance of a specific model subclass, or None if no configuration is found in the cache"""
        # Imports are placed inside the method to avoid circular imports
        # Get the cache manager instance
        from knowledge_api.framework.redis.cache_manager import CacheManager
        cache_manager = CacheManager()
        
        # Get the LLM provider configuration from the cache
        provider_config = cache_manager.get_llm_provider(llm_type)
        
        if provider_config is None:
            # Try to find the mapped type
            llm_type_lower = llm_type.lower()
            for name, mapped_type in cls._name_mapping.items():
                if name in llm_type_lower:
                    provider_config = cache_manager.get_llm_provider(mapped_type)
                    if provider_config:
                        break
        
        if provider_config is None:
            print(f"无法在缓存中找到LLM提供商配置: {llm_type}")
            return None
        
        # Create an LLM instance using provider configuration
        return cls.create_llm(
            ai_name=provider_config.provider_name,
            model=provider_config.model_name,
            api_key=provider_config.api_key,
            base_url=provider_config.api_url,
            format_response=format_response
        )
    
    @classmethod
    def get_or_create_from_cache(cls, provider_name: str = None) -> Optional[BaseLLM]:
        """@Description Get or create an LLM instance from the cache
@Param {string} provider_name - Optional, provider name. If None, the default provider configured by the system will be used
@Returns {BaseLLM} LLM instance or None if it cannot be created"""
        from knowledge_api.framework.redis.cache_manager import CacheManager
        cache_manager = CacheManager()
        
        # If no provider is specified, use the default value of the system configuration
        if provider_name is None:
            provider_name = cache_manager.get_system_config("LLM_CONFIG")
            if not provider_name:
                print("The system is not configured with a default LLM provider")
                return None
        
        # Attempt to retrieve an existing instance from the cache manager
        if cache_manager.llm is not None and provider_name == cache_manager.get_system_config("LLM_CONFIG"):
            return cache_manager.llm
        
        # Create a new instance
        llm = cls.create_llm_from_cache(provider_name)
        
        # If created successfully, update the instance in the cache manager
        if llm is not None:
            cache_manager.llm = llm
            
        return llm
