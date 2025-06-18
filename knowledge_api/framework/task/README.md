# FastAPI异步任务处理框架

专为FastAPI项目设计的异步任务处理框架，提供线程池管理、任务调度和监控功能。

## 特性

- 基于`concurrent.futures`的增强型线程池
- 异步任务管理和监控
- 多种任务装饰器（后台任务、异步任务、节流任务、重试任务）
- 与FastAPI生命周期集成
- 任务状态跟踪和结果获取

## 安装

本框架是项目内部模块，不需要额外安装。

## 使用方法

### 1. 初始化框架

在FastAPI应用中初始化异步任务框架：

```python
from fastapi import FastAPI
from knowledge_api.framework import setup_async_framework

app = FastAPI(
    # ... 其他配置
    lifespan=setup_async_framework  # 使用框架的生命周期管理器
)
```

如果需要指定线程池大小：

```python
from contextlib import asynccontextmanager
from knowledge_api.framework import setup_async_framework

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with setup_async_framework(app, max_workers=10):
        yield

app = FastAPI(
    # ... 其他配置
    lifespan=lifespan
)
```

### 2. 使用任务装饰器

#### 后台任务装饰器

适用于长时间运行的任务，立即返回任务ID，不阻塞主请求：

```python
from knowledge_api.framework import background_task

@background_task(timeout=30, description="数据处理任务")
def process_large_data(data_id: str) -> dict:
    # 长时间运行的处理逻辑
    return {"status": "completed", "data_id": data_id}

@app.post("/process")
async def start_processing(data_id: str):
    task_id = process_large_data(data_id)
    return {"task_id": task_id, "status": "processing"}
```

#### 异步任务装饰器

适用于需要等待结果的异步任务：

```python
from knowledge_api.framework import async_task

@async_task(timeout=10)
async def fetch_data(user_id: str) -> dict:
    # 异步获取数据
    return {"user_id": user_id, "data": "..."}

@app.get("/data/{user_id}")
async def get_user_data(user_id: str):
    try:
        result = await fetch_data(user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### 节流任务装饰器

限制函数调用频率：

```python
from knowledge_api.framework import throttled_task

@throttled_task(rate_limit=5, time_window=60)  # 每60秒最多5次调用
async def limited_api_call() -> dict:
    # API调用
    return {"status": "success"}
```

#### 重试任务装饰器

自动重试易失败的操作：

```python
from knowledge_api.framework import retry_task

@retry_task(max_retries=3, retry_delay=1.0)
async def unreliable_operation() -> dict:
    # 可能失败的操作
    return {"status": "success"}
```

### 3. 任务管理

获取任务状态和结果：

```python
from knowledge_api.framework import get_task_manager, TaskStatus

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    task_manager = get_task_manager()
    task = await task_manager.get_task(task_id)
    
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # 获取任务信息
    task_info = task.to_dict()
    
    # 如果任务已完成，也获取结果
    if task.status == TaskStatus.COMPLETED:
        result = await task_manager.get_result(task_id)
        task_info["result"] = result
        
    return task_info
```

获取所有任务状态：

```python
@app.get("/tasks")
def list_all_tasks():
    task_manager = get_task_manager()
    return task_manager.get_all_tasks()
```

### 4. 手动创建任务

直接使用任务管理器创建任务：

```python
from knowledge_api.framework import get_task_manager

@app.post("/custom-task")
async def create_custom_task(params: dict):
    task_manager = get_task_manager()
    
    # 提交自定义任务
    task_id = await task_manager.submit(
        func=my_custom_function,
        args=(params["arg1"], params["arg2"]),
        kwargs={"option": params.get("option")},
        timeout=30,
        description="Custom task",
        wait=False  # 不等待结果
    )
    
    return {"task_id": task_id}
```

### 5. 线程池访问

直接访问线程池：

```python
from knowledge_api.framework import get_thread_pool

@app.get("/pool-stats")
def get_thread_pool_stats():
    pool = get_thread_pool()
    return pool.get_stats()
```

## 完整示例

查看 `knowledge_api/framework/example.py` 获取完整的使用示例。

## 注意事项

1. 对于CPU密集型任务，推荐使用`background_task`装饰器在线程池中运行，避免阻塞事件循环
2. 对于IO密集型任务，如果它们已经是异步的，可以直接在FastAPI路由中使用
3. 使用`throttled_task`时，同一装饰器实例的速率限制由所有请求共享
4. 后台任务的结果会保存在内存中，定期使用`cleanup_completed_tasks`清理旧任务

## 高级配置

### 自定义线程池

```python
from knowledge_api.framework import ThreadPoolExecutorEnhanced

# 创建自定义线程池
custom_pool = ThreadPoolExecutorEnhanced(
    max_workers=20,
    thread_name_prefix="custom-pool-",
    task_timeout=60.0
)

# 在应用中使用自定义线程池
# ...
```

### 任务监控和清理

可以设置定期任务来清理已完成的任务：

```python
import asyncio
from fastapi import FastAPI
from knowledge_api.framework import get_task_manager, setup_async_framework

app = FastAPI(lifespan=setup_async_framework)

@app.on_event("startup")
async def start_cleanup_task():
    asyncio.create_task(periodic_cleanup())

async def periodic_cleanup():
    task_manager = get_task_manager()
    while True:
        await asyncio.sleep(3600)  # 每小时运行一次
        removed = task_manager.cleanup_completed_tasks(max_age=86400)  # 清理一天前的任务
        print(f"Removed {removed} completed tasks")
``` 