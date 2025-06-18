# 定时任务管理系统

基于APScheduler的定时任务管理系统，支持任务的创建、修改、删除、暂停、恢复和立即执行等操作。

## 功能特性

- 支持三种触发器类型：
  - 日期触发器(date)：在指定日期时间执行一次
  - 间隔触发器(interval)：按固定时间间隔重复执行
  - Cron触发器(cron)：按cron表达式定义的时间规则执行
- 任务状态管理：等待(pending)、运行(running)、暂停(paused)、完成(completed)、失败(failed)
- 任务执行日志记录
- RESTful API接口
- 支持任务暂停与恢复
- 支持立即触发任务执行

## 数据库表设计

### 定时任务表(task_manage)

```sql
CREATE TABLE `task_manage` (
  `id` varchar(36) NOT NULL COMMENT '任务ID',
  `name` varchar(100) NOT NULL COMMENT '任务名称',
  `task_type` varchar(50) NOT NULL COMMENT '任务类型',
  `status` varchar(20) NOT NULL DEFAULT 'pending' COMMENT '任务状态：pending/running/paused/completed/failed',
  `trigger_type` varchar(20) NOT NULL COMMENT '触发器类型：date/interval/cron',
  `trigger_args` json DEFAULT NULL COMMENT '触发器参数，JSON格式',
  `func_path` varchar(255) NOT NULL COMMENT '执行函数路径',
  `func_args` json DEFAULT NULL COMMENT '函数参数，JSON格式',
  `next_run_time` datetime DEFAULT NULL COMMENT '下次运行时间',
  `max_instances` int DEFAULT 1 COMMENT '最大实例数',
  `description` text COMMENT '任务描述',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_status` (`status`),
  KEY `idx_next_run_time` (`next_run_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='定时任务管理表';
```

### 任务执行日志表(task_execution_log)

```sql
CREATE TABLE `task_execution_log` (
  `id` varchar(36) NOT NULL COMMENT '日志ID',
  `task_id` varchar(36) NOT NULL COMMENT '任务ID',
  `start_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
  `end_time` datetime DEFAULT NULL COMMENT '结束时间',
  `status` varchar(20) NOT NULL DEFAULT 'running' COMMENT '状态：running/completed/failed',
  `result` text COMMENT '执行结果',
  `error` text COMMENT '错误信息',
  PRIMARY KEY (`id`),
  KEY `idx_task_id` (`task_id`),
  KEY `idx_start_time` (`start_time`),
  KEY `idx_status` (`status`),
  CONSTRAINT `fk_task_execution_log_task_id` FOREIGN KEY (`task_id`) REFERENCES `task_manage` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务执行日志表';
```

## API接口

### 创建任务

```
POST /task-manage/
```

请求示例：

```json
{
  "name": "定时通知任务",
  "task_type": "notification",
  "trigger_type": "cron",
  "trigger_args": {
    "hour": "9",
    "minute": "0"
  },
  "func_path": "knowledge_api.framework.task_manage.example_tasks.notification_task",
  "func_args": {
    "user_id": "user123",
    "message": "This is a scheduled notification",
    "channel": "email"
  },
  "max_instances": 1,
  "description": "每天早上9点发送通知"
}
```

### 获取任务列表

```
GET /task-manage/
```

### 获取单个任务

```
GET /task-manage/{task_id}
```

### 更新任务

```
PUT /task-manage/{task_id}
```

### 删除任务

```
DELETE /task-manage/{task_id}
```

### 暂停任务

```
POST /task-manage/{task_id}/pause
```

### 恢复任务

```
POST /task-manage/{task_id}/resume
```

### 立即执行任务

```
POST /task-manage/{task_id}/trigger
```

### 获取任务执行日志

```
GET /task-manage/{task_id}/logs
```

## 使用示例

### 创建日期触发器任务

```json
{
  "name": "一次性任务",
  "task_type": "simple",
  "trigger_type": "date",
  "trigger_args": {
    "run_date": "2023-12-31T23:59:59"
  },
  "func_path": "knowledge_api.framework.task_manage.example_tasks.simple_task",
  "func_args": {
    "message": "Happy New Year!"
  },
  "description": "新年倒计时任务"
}
```

### 创建间隔触发器任务

```json
{
  "name": "周期性任务",
  "task_type": "processing",
  "trigger_type": "interval",
  "trigger_args": {
    "hours": 1
  },
  "func_path": "knowledge_api.framework.task_manage.example_tasks.data_processing_task",
  "func_args": {
    "data_id": "data123",
    "process_type": "hourly_update"
  },
  "description": "每小时处理一次数据"
}
```

### 创建Cron触发器任务

```json
{
  "name": "Cron任务",
  "task_type": "backup",
  "trigger_type": "cron",
  "trigger_args": {
    "day_of_week": "mon-fri", 
    "hour": "23", 
    "minute": "30"
  },
  "func_path": "knowledge_api.framework.task_manage.example_tasks.simple_task",
  "func_args": {
    "message": "Daily backup started"
  },
  "description": "工作日每晚23:30执行备份"
}
```

## 安装依赖

确保已安装APScheduler：

```bash
pip install apscheduler>=3.10.4
``` 