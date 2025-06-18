# 工作流框架

工作流框架是一个灵活、可扩展的组件驱动工作流引擎，支持多种游戏逻辑和交互模式。框架基于事件驱动和数据流模型，可以轻松实现复杂的游戏逻辑和交互流程。

## 核心概念

- **节点 (Node)**: 工作流的最小执行单元，每个节点完成特定功能
- **数据流 (DataFlow)**: 管理节点间数据传递和映射
- **上下文 (Context)**: 维护工作流执行状态和共享数据
- **事件系统 (EventSystem)**: 处理节点间通信和异步事件
- **工作流引擎 (WorkflowEngine)**: 负责加载、执行和管理工作流

## 目录结构

```
workflow/
├── __init__.py        # 包入口
├── node.py            # 节点基类和状态管理
├── data_flow.py       # 数据流管理模块
├── context.py         # 上下文管理模块
├── event_system.py    # 事件系统模块
├── engine.py          # 工作流引擎核心
└── README.md          # 文档说明
```

## 设计理念

1. **组件化**: 所有功能都封装在独立的节点中，便于扩展和复用
2. **数据驱动**: 通过数据流和上下文实现组件间的数据传递
3. **事件驱动**: 使用事件机制实现组件间的松耦合通信
4. **声明式**: 工作流定义采用JSON格式，支持可视化编辑

## 节点状态管理

节点有以下状态:

- **IDLE**: 初始/空闲状态
- **READY**: 已准备好，等待执行
- **RUNNING**: 执行中
- **COMPLETED**: 执行完成
- **FAILED**: 执行失败
- **SKIPPED**: 被跳过

## 数据流处理

数据流处理支持以下特性:

1. **端口映射**: 自动根据节点输入/输出端口创建映射
2. **条件评估**: 支持条件边的数据评估
3. **数据传递**: 在节点间传递和转换数据

## 上下文共享

上下文支持以下特性:

1. **全局状态**: 维护工作流执行的全局状态
2. **嵌套访问**: 支持使用点号访问嵌套数据 (`game_state.players[0].name`)
3. **快照管理**: 自动创建上下文快照，支持回溯

## 事件系统

事件系统支持以下事件类型:

- **WORKFLOW_START**: 工作流开始执行
- **WORKFLOW_COMPLETE**: 工作流执行完成
- **WORKFLOW_ERROR**: 工作流执行错误
- **NODE_BEFORE_EXECUTE**: 节点执行前
- **NODE_AFTER_EXECUTE**: 节点执行后
- **NODE_ERROR**: 节点执行错误
- **DATA_UPDATED**: 数据更新
- **CONTEXT_CHANGED**: 上下文变更

## 使用示例

```python
# 创建节点工厂
from knowledge_api.framework.workflow import WorkflowEngine, NodeFactory
from game_components.nodes import MessageNode, ConditionalNode

# 注册节点类型
node_factory = NodeFactory()
node_factory.register_node_type("message", MessageNode)
node_factory.register_node_type("conditional", ConditionalNode)

# 创建工作流引擎
engine = WorkflowEngine(node_factory)

# 加载工作流定义
engine.load_workflow("werewolf_game.json")

# 执行工作流
initial_context = {
    "game_type": "werewolf",
    "players": [{"id": "p1", "name": "玩家1"}, {"id": "p2", "name": "玩家2"}]
}
context = await engine.execute_workflow(initial_context)

# 获取执行结果
result = context.data
```

## 扩展节点

创建自定义节点:

```python
from knowledge_api.framework.workflow import Node, NodeStatus, DataPort

class CustomNode(Node):
    # 节点类型标识
    node_type = "custom_node"
    
    # 节点描述
    description = "自定义节点示例"
    
    def _init_ports(self) -> None:
        """初始化输入输出端口"""
        self.inputs = [
            DataPort("input1", "message", "string", "输入消息", True)
        ]
        
        self.outputs = [
            DataPort("output1", "result", "string", "处理结果")
        ]
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """处理节点逻辑"""
        # 获取输入
        message = context.get("message", "")
        
        # 处理逻辑
        result = f"已处理: {message}"
        
        # 返回结果
        return {"result": result}
```

## 工作流定义示例

```json
{
  "id": "simple_workflow",
  "name": "简单示例工作流",
  "description": "示例工作流定义",
  "start_node": "node1",
  "nodes": [
    {
      "id": "node1",
      "name": "消息节点",
      "component_type": "message",
      "config": {
        "message": "欢迎使用工作流框架"
      },
      "outputs": [
        {
          "id": "out1",
          "key": "message",
          "type": "string",
          "description": "消息内容"
        }
      ]
    },
    {
      "id": "node2",
      "name": "条件节点",
      "component_type": "conditional",
      "config": {
        "condition": "message != ''"
      },
      "inputs": [
        {
          "id": "in1",
          "key": "message",
          "type": "string",
          "description": "消息内容",
          "required": true
        }
      ]
    }
  ],
  "edges": [
    {
      "source": "node1",
      "target": "node2"
    }
  ]
}
```

## 前后端协作

该框架设计与前端工作流编辑器兼容，支持以下特性:

1. **节点输入/输出映射**: 自动建立节点间的数据连接
2. **条件边评估**: 支持基于条件表达式的流程控制
3. **JSON序列化**: 支持工作流定义的导入导出

## 注意事项

1. 所有节点实现应当是异步的，使用 `async/await` 模式
2. 数据流处理基于端口的键名匹配，确保端口键名在连接的节点间保持一致
3. 节点实现应捕获并妥善处理异常，避免整个工作流中断
4. 工作流引擎使用事件系统进行状态通知，可注册自定义事件处理器

## 节点类型

### 游戏状态节点 (game_state)

游戏状态节点用于初始化游戏状态和玩家智能体。该节点必须作为工作流的第一个节点。

**配置项**：
- `state_storage`：状态存储方式，例如 "memory"
- `initial_state`：初始游戏状态，包含以下字段：
  - `game_type`：游戏类型
  - `status`：游戏状态，初始为 "initialized"
  - `min_players`：最小玩家数量
  - `max_players`：最大玩家数量
  - `game_atmosphere`：游戏氛围描述
  - `default_model_id`：默认模型ID，当玩家角色未指定模型时使用

**输入**：
- `character_list`：角色列表，包含角色信息（必需）

**输出**：
- `state`：完整的游戏状态对象
- `players`：根据角色列表创建的玩家智能体列表
- `game_type`：游戏类型
- `game_atmosphere`：游戏氛围描述
- `min_players`：最小玩家数量
- `max_players`：最大玩家数量
- `status`：游戏状态
- `round`：游戏回合

**处理逻辑**：
1. 验证节点是否为工作流的第一个节点
2. 获取并验证角色列表
3. 验证玩家数量是否在限制范围内
4. 初始化游戏状态
5. 创建玩家智能体
6. 更新并返回游戏状态 