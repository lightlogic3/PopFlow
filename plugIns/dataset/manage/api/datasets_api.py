from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List

from knowledge_api.framework.database.database import get_session
from plugIns.dataset.mapper.datasets.base import DatasetResponse, DatasetCreate, DatasetUpdate
from plugIns.dataset.mapper.datasets.crud import DatasetCRUD
from plugIns.dataset.mapper.sft.crud import SftEntryCRUD
from plugIns.dataset.mapper.conversations.crud import ConversationEntryCRUD
from plugIns.dataset.mapper.dpo.crud import DpoEntryCRUD

router = APIRouter(prefix="/datasets", tags=["数据集管理"])


@router.post("/", response_model=DatasetResponse)
async def create_dataset(
        dataset: DatasetCreate,
        db: Session = Depends(get_session)
) -> DatasetResponse:
    """创建数据集"""
    crud = DatasetCRUD(db)
    return await crud.create(dataset=dataset)


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
        dataset_id: int,
        db: Session = Depends(get_session)
) -> DatasetResponse:
    """获取单个数据集"""
    crud = DatasetCRUD(db)
    dataset = await crud.get_by_id(dataset_id=dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")
    return dataset


@router.get("/", response_model=List[DatasetResponse])
async def list_datasets(
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=100),
        dataset_type: str = Query(default=None),
        tags: str = Query(default=None),
        db: Session = Depends(get_session)
) -> List[DatasetResponse]:
    """获取数据集列表"""
    crud = DatasetCRUD(db)

    if dataset_type:
        return await crud.get_by_type(dataset_type=dataset_type, skip=skip, limit=limit)

    if tags:
        tag_list = [tag.strip() for tag in tags.split(',')]
        return await crud.get_by_tags(tags=tag_list, skip=skip, limit=limit)

    return await crud.get_all(skip=skip, limit=limit)


@router.put("/{dataset_id}", response_model=DatasetResponse)
async def update_dataset(
        dataset_id: int,
        dataset_update: DatasetUpdate,
        db: Session = Depends(get_session)
) -> DatasetResponse:
    """更新数据集"""
    crud = DatasetCRUD(db)
    dataset = await crud.update(dataset_id, dataset_update)
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")
    return dataset


@router.delete("/{dataset_id}", response_model=bool)
async def delete_dataset(
        dataset_id: int,
        db: Session = Depends(get_session)
) -> bool:
    """删除数据集"""
    # 首先删除所有关联数据
    sft_crud = SftEntryCRUD(db)
    await sft_crud.delete_by_dataset_id(dataset_id=dataset_id)

    conversation_crud = ConversationEntryCRUD(db)
    await conversation_crud.delete_by_dataset_id(dataset_id=dataset_id)

    dpo_crud = DpoEntryCRUD(db)
    await dpo_crud.delete_by_dataset_id(dataset_id=dataset_id)

    # 然后删除数据集
    crud = DatasetCRUD(db)
    success = await crud.delete(dataset_id=dataset_id)
    if not success:
        raise HTTPException(status_code=404, detail="数据集不存在")
    return True


@router.get("/{dataset_id}/stats")
async def get_dataset_stats():
    """

## 数据集统计信息接口设计说明

`DatasetStats` 接口是我为数据集管理模块设计的统计信息结构，主要用于：

1. 展示数据集概览信息
2. 提供数据质量分析
3. 为训练过程提供参考

### 设计思路

这个接口根据不同类型的数据集（SFT、DPO、会话）设计了对应的统计指标：

- **通用指标**：条目数量、总Token数、平均Token长度
- **SFT特有**：指令Token数、输出Token数
- **DPO特有**：提示Token数、优选回复Token数、拒绝回复Token数
- **会话特有**：消息数量

### 示例JSON数据

#### SFT数据集统计

```json
{
  "entryCount": 1250,
  "tokenCount": 450000,
  "avgTokensPerEntry": 360,
  "instructionTokens": 187500,
  "outputTokens": 262500,
  "avgInstructionLength": 150,
  "avgOutputLength": 210,
  "languageDistribution": {
    "中文": 850,
    "英文": 400
  }
}
```

#### DPO数据集统计

```json
{
  "entryCount": 800,
  "tokenCount": 320000,
  "avgTokensPerEntry": 400,
  "promptTokens": 96000,
  "chosenTokens": 112000,
  "rejectedTokens": 112000,
  "avgPromptLength": 120,
  "avgChosenLength": 140,
  "avgRejectedLength": 140,
  "preferenceDistribution": {
    "有害内容过滤": 350,
    "回答准确性": 450
  }
}
```

#### 会话数据集统计

```json
{
  "entryCount": 500,
  "tokenCount": 375000,
  "avgTokensPerEntry": 750,
  "messageCount": 6500,
  "avgMessagesPerConversation": 13,
  "roleDistribution": {
    "user": 3250,
    "assistant": 3200,
    "system": 50
  },
  "avgTurns": 6,
  "topicDistribution": {
    "技术问答": 200,
    "创意写作": 150,
    "日常对话": 150
  }
}
```

### 实现建议

您可以根据自己的实际需求选择实现部分或全部统计信息，关键是确保：

1. 基础统计数据准确（条目数、Token数等）
2. 针对不同数据集类型提供特定分析
3. 提供有意义的可视化展示

这些统计数据将帮助用户更好地理解和管理他们的训练数据，为模型训练提供更好的数据支持。

    """
    return {
        "entryCount": 500,
        "tokenCount": 375000,
        "avgTokensPerEntry": 750,
        "messageCount": 6500,
        "avgMessagesPerConversation": 13,
        "roleDistribution":"测试效果",
        "avgTurns": 6,
        "topicDistribution":"测试效果"
    }
