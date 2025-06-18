from fastapi import APIRouter

from plugIns.dataset.manage.api import datasets_api, sft_api
from plugIns.dataset.manage.api import conversations_api, dpo_api

dataset_router = APIRouter(prefix="/datasets")
dataset_router.include_router(conversations_api.router)
dataset_router.include_router(datasets_api.router)
dataset_router.include_router(dpo_api.router)
dataset_router.include_router(sft_api.router)
