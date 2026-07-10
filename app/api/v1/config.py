"""模型配置 API"""

import os
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.dependencies.auth import User, get_current_user

router = APIRouter()


class ModelConfigResponse(BaseModel):
    """模型配置响应"""
    llm_model: str
    llm_model_fast: str
    llm_base_url: str
    llm_api_key: str
    llm_temperature: float
    llm_temperature_fast: float
    image_model: str
    image_base_url: str
    image_api_key: str
    embedding_model: str
    embedding_base_url: str


@router.get("/models", response_model=ModelConfigResponse)
async def get_model_config(current_user: User = Depends(get_current_user)):
    """获取当前系统模型配置（从环境变量读取的默认值）"""
    return ModelConfigResponse(
        llm_model=os.getenv("LLM_MODEL", "doubao-seed-1-8-251228"),
        llm_model_fast=os.getenv("LLM_MODEL_FAST", "doubao-seed-1-6-flash-250828"),
        llm_base_url=os.getenv("LLM_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
        llm_temperature_fast=float(os.getenv("LLM_TEMPERATURE_FAST", "0.7")),
        image_model=os.getenv("IMAGE_MODEL", "gemini-3-pro-image-preview"),
        image_base_url=os.getenv("IMAGE_BASE_URL", ""),
        image_api_key=os.getenv("IMAGE_API_KEY", ""),
        embedding_model=os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3"),
        embedding_base_url=os.getenv("EMBEDDING_BASE_URL", ""),
    )
