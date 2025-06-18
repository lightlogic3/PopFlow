from enum import Enum
from typing import Dict, Type, Optional, List

from .graphiti_memory import GraphitiMemory
from .memory_interface import MemoryInterface


class MemoryLevel(Enum):
    """记忆系统级别枚举"""
    LEVEL_6_CONVERSATION = 6  # 对话记忆系统
    LEVEL_7_Mem0=7 # 使用Mem0进行记忆
    LEVEL_10_CONVERSATION = 10  # 对话记忆系统


class MemoryFactory:
    """
    记忆系统工厂类
    负责创建和管理不同级别的记忆系统
    """

    def __init__(self):
        self._registry: Dict[MemoryLevel, Type[MemoryInterface]] = {}
        self._instances: Dict[MemoryLevel, MemoryInterface] = {}
        self._background_enabled = True  # 默认启用后台处理
        self._debug_mode = False  # 调试模式

    def register(self, level: MemoryLevel, memory_class: Type[MemoryInterface]) -> None:
        """
        注册记忆系统类

        Args:
            level: 记忆级别
            memory_class: 记忆系统类
        """
        print(f"注册记忆系统: {level} -> {memory_class.__name__}")
        self._registry[level] = memory_class

    async def create(self, level: MemoryLevel, **kwargs) -> MemoryInterface:
        """
        创建指定级别的记忆系统实例

        Args:
            level: 记忆级别
            **kwargs: 传递给记忆系统构造函数的参数

        Returns:
            MemoryInterface: 记忆系统实例

        Raises:
            ValueError: 如果指定级别未注册
        """
        if level not in self._registry:
            raise ValueError(f"未注册的记忆系统级别: {level}")

        memory_class = self._registry[level]
        print(f"创建记忆系统实例: {level} -> {memory_class.__name__}")
        instance = memory_class(**kwargs)
        self._instances[level] = instance
        return instance

    def get_instance(self, level: MemoryLevel) -> Optional[MemoryInterface]:
        """
        获取指定级别的记忆系统实例

        Args:
            level: 记忆级别

        Returns:
            Optional[MemoryInterface]: 记忆系统实例，如果不存在则返回None
        """
        return self._instances.get(level)

    def get_all_instances(self) -> List[MemoryInterface]:
        """
        获取所有已创建的记忆系统实例

        Returns:
            List[MemoryInterface]: 记忆系统实例列表
        """
        return list(self._instances.values())

    def get_registered_levels(self) -> List[MemoryLevel]:
        """
        获取所有已注册的记忆级别

        Returns:
            List[MemoryLevel]: 记忆级别列表
        """
        return list(self._registry.keys())

    def enable_background_processing(self, enabled: bool = True) -> None:
        """
        启用或禁用后台处理

        Args:
            enabled: 是否启用后台处理
        """
        self._background_enabled = enabled

    def is_background_enabled(self) -> bool:
        """
        检查是否启用后台处理

        Returns:
            bool: 是否启用后台处理
        """
        return self._background_enabled

    def enable_debug_mode(self, enabled: bool = True) -> None:
        """
        启用或禁用调试模式

        Args:
            enabled: 是否启用调试模式
        """
        self._debug_mode = enabled
        print(f"调试模式: {'启用' if enabled else '禁用'}")

    def is_debug_mode(self) -> bool:
        """
        检查是否启用调试模式

        Returns:
            bool: 是否启用调试模式
        """
        return self._debug_mode

    def register_default_systems(self) -> None:
        """注册默认的记忆系统实现"""
        from .conversation_rag_memory import ConversationRAGMemory
        from .mem0_memory.mem0_memory import Mem0Memory

        # 尝试导入Graphiti记忆系统
        print("注册默认记忆系统...")

        self.register(MemoryLevel.LEVEL_6_CONVERSATION, ConversationRAGMemory)
        self.register(MemoryLevel.LEVEL_10_CONVERSATION, GraphitiMemory)
        self.register(MemoryLevel.LEVEL_7_Mem0, Mem0Memory)