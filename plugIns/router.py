from fastapi import APIRouter

from plugIns.dataset.api_router import dataset_router

plugIn_router = APIRouter(prefix="/plugIn", tags=["插件管理"])

plugIn_router.include_router(dataset_router)
