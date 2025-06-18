# 定时任务装饰器模块

该模块提供了一种简便的方式来定义和注册定时任务，支持在前端通过下拉菜单选择任务。

## 功能特点

- 使用装饰器自动注册定时任务
- 自动收集任务参数信息
- 前端支持下拉选择任务
- 自动导入任务参数默认值

## 使用方法

### 1. 创建定时任务

在 `knowledge_api/scheduler_task` 目录下创建新的Python文件，使用 `@scheduled_task` 装饰器标记定时任务函数：

```python
from knowledge_api.scheduler_task import scheduled_task
from typing import Dict, Any

@scheduled_task(
    name="我的任务",  # 任务名称（前端显示用）
    description="这是一个示例任务",  # 任务描述
    tags=["示例", "测试"]  # 任务标签（可用于分类）
)
async def my_task(message: str = "默认消息") -> Dict[str, Any]:
    """
    任务函数文档字符串（会被收集）
    
    @param message: 消息参数
    @return: 任务执行结果
    """
    # 任务实现...
    return {"result": "success", "message": message}
```

### 2. 任务参数规范

- 使用类型注解明确参数类型
- 为参数提供默认值（可选）
- 添加参数文档注释

### 3. 在前端使用

前端会自动从API获取所有注册的任务，用户可以：

1. 从下拉菜单选择任务
2. 系统会自动填充任务的默认参数
3. 用户可以根据需要修改参数

## API接口

### 获取所有注册任务

```
GET /task-manage/registered-tasks
```

返回所有注册的任务列表，包含名称、描述、参数信息等。

## 自动扫描机制

系统会在启动时自动扫描 `knowledge_api/scheduler_task` 目录下的所有Python文件，加载并注册所有标记了 `@scheduled_task` 装饰器的函数。

## 临时任务使用示例

除了使用装饰器注册的定时任务外，还可以使用`TaskManager`创建临时的耗时任务，这些任务可以通过前端界面监控执行情况。

```python
from knowledge_api.framework.task import get_task_manager

async def example_view():
    # 获取任务管理器
    task_manager = get_task_manager()
    
    # 定义耗时任务函数
    async def my_long_running_task(arg1, arg2, option=None):
        # 这里可以是任何耗时操作
        import time
        time.sleep(10)  # 模拟耗时操作
        return {"result": f"Processed {arg1} and {arg2} with option {option}"}
    
    # 提交耗时任务
    task_id = await task_manager.submit_time_consuming_tasks(
        func=my_long_running_task,
        args=("value1", "value2"),  # 位置参数
        kwargs={"option": "special"},  # 关键字参数
        timeout=30,  # 超时时间（秒）
        description="处理重要数据的任务",  # 任务描述
        wait=False  # 不等待结果，立即返回
    )
    
    return {"message": "任务已提交", "task_id": task_id}
```

提交的临时任务会显示在任务管理页面的"临时任务"标签页中，可以查看任务状态、执行时间和结果。与定时任务不同，临时任务只执行一次，但同样会记录到数据库，并生成执行日志。 