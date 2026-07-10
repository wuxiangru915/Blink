"""
图片生成服务模块
使用火山引擎 Doubao Seedream API 生成小红书风格配图
"""

import asyncio
import os
import random
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import httpx
from dotenv import load_dotenv

from app.core.logger import get_logger
from app.core.utils import detect_image_format

load_dotenv()

logger = get_logger(__name__)


class ImageService:
    """图片生成服务类"""

    XHS_STYLE_PROMPT = """请根据以下内容生成一张小红书风格的爆款配图：

【内容主题】
{content}

【图片要求】
- 风格：小红书流行的高质感、精致感、氛围感风格
- 色调：明亮温暖、柔和治愈、或高级感色调
- 构图：简洁大气、留白得当、视觉重点突出
- 比例：3:4 竖版构图（适合手机浏览）

【风格参考】
- 美食：诱人的食物特写，暖色调打光
- 穿搭：时尚感穿搭展示，简约背景
- 家居：温馨舒适的生活场景，ins风或日系风
- 知识/干货：清新简约的图文排版，扁平插画
- 其他：根据内容匹配最适合的小红书流行风格

请生成一张高质量、有吸引力的图片。"""

    FALLBACK_PROMPTS = [
        "小红书风格，明亮温暖的生活场景，咖啡和书本，柔和自然光，3:4竖版构图",
        "小红书风格，创意工作台，文具和绿植，ins风格，3:4竖版构图",
        "小红书风格，清新简约的扁平插画，渐变色背景，3:4竖版构图",
    ]

    def __init__(self):
        self.api_key = os.getenv("IMAGE_API_KEY", "")
        self.base_url = os.getenv("IMAGE_BASE_URL", "https://ark.cn-beijing.volces.com/api/plan/v3/images/generations")
        self.model = os.getenv("IMAGE_MODEL", "gemini-3-pro-image-preview")

        self.image_dir = Path("static/images/generated")
        self.image_dir.mkdir(parents=True, exist_ok=True)

    def _ensure_configured(self):
        if not self.api_key:
            raise ValueError("IMAGE_API_KEY 未配置，无法使用图片生成功能")

    def _get_image_model(self, model_config: dict = None) -> str:
        """获取图片模型名称，支持运行时覆盖"""
        if model_config and model_config.get("image_model"):
            return model_config["image_model"]
        return self.model

    def _get_image_api_key(self, model_config: dict = None) -> str:
        """获取图片 API Key，支持运行时覆盖"""
        if model_config and model_config.get("image_api_key"):
            return model_config["image_api_key"]
        return self.api_key

    def _get_image_base_url(self, model_config: dict = None) -> str:
        """获取图片 API Base URL，支持运行时覆盖"""
        if model_config and model_config.get("image_base_url"):
            return model_config["image_base_url"]
        return self.base_url

    def _build_api_url(self) -> str:
        """构建火山引擎 API URL"""
        return self.base_url

    def _write_bytes(self, file_path: Path, raw_data: bytes) -> None:
        """同步写入字节数据到文件"""
        with open(file_path, "wb") as f:
            f.write(raw_data)

    async def _save_image(self, image_base64: str, prefix: str = "xhs") -> str:
        """保存 base64 图片到本地，自动检测格式"""
        import base64

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]

        # 检测实际图片格式
        raw_data = base64.b64decode(image_base64)
        ext = detect_image_format(raw_data)

        filename = f"{prefix}_{timestamp}_{unique_id}.{ext}"
        file_path = self.image_dir / filename
        await asyncio.to_thread(self._write_bytes, file_path, raw_data)

        return f"/static/images/generated/{filename}"

    async def _call_image_api(
        self, prompt: str, model: str = None, api_key: str = None, base_url: str = None
    ) -> Optional[dict]:
        """调用图片生成 API，返回 {'b64_json': ...} 或 {'url': ...}"""
        url = base_url or self._build_api_url()

        payload = {
            "model": model or self.model,
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
        }

        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key or self.api_key}"}

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()

                if "data" in result and result["data"]:
                    item = result["data"][0]
                    # 返回 b64_json 或 url
                    if item.get("b64_json"):
                        return {"b64_json": item["b64_json"]}
                    if item.get("url"):
                        return {"url": item["url"]}

                logger.warning(f"API 响应中未找到图片数据: {result}")
                return None

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP 错误: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"请求异常: {e}")
            return None

    async def _download_image(self, url: str, prefix: str = "xhs") -> Optional[str]:
        """下载 URL 图片并保存到本地，自动检测格式"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                raw_data = response.content

                # 检测实际图片格式
                ext = detect_image_format(raw_data)

                filename = f"{prefix}_{timestamp}_{unique_id}.{ext}"
                file_path = self.image_dir / filename
                await asyncio.to_thread(self._write_bytes, file_path, raw_data)
            return f"/static/images/generated/{filename}"
        except Exception as e:
            logger.error(f"下载图片失败: {e}")
            return None

    async def _process_api_result(self, api_result: Optional[dict], prefix: str = "xhs") -> Optional[str]:
        """处理 API 返回结果，保存图片并返回本地路径"""
        if not api_result:
            return None

        # Base64 直接保存
        if api_result.get("b64_json"):
            return await self._save_image(api_result["b64_json"], prefix)

        # URL 下载后保存
        if api_result.get("url"):
            return await self._download_image(api_result["url"], prefix)

        return None

    async def generate_single_image(
        self,
        prompt: str,
        optimize_for_xhs: bool = True,
        model_config: dict = None,
    ) -> Optional[str]:
        """生成单张图片（失败时使用备用提示词重试一次）"""
        self._ensure_configured()
        current_prompt = self.XHS_STYLE_PROMPT.format(content=prompt) if optimize_for_xhs else prompt
        model = self._get_image_model(model_config)
        api_key = self._get_image_api_key(model_config)
        base_url = self._get_image_base_url(model_config)

        logger.info(f"生成图片: {prompt[:50]}...")

        # 首次尝试
        api_result = await self._call_image_api(current_prompt, model, api_key, base_url)
        image_path = await self._process_api_result(api_result)
        if image_path:
            logger.info(f"图片生成成功: {image_path}")
            return image_path

        # 使用备用提示词重试
        logger.info("首次失败，使用备用提示词重试...")
        await asyncio.sleep(1)

        fallback_prompt = random.choice(self.FALLBACK_PROMPTS)
        api_result = await self._call_image_api(fallback_prompt, model, api_key, base_url)
        image_path = await self._process_api_result(api_result)
        if image_path:
            logger.info(f"备用提示词成功: {image_path}")
            return image_path

        logger.error("图片生成失败，跳过")
        return None

    async def generate_images(
        self,
        visual_points: List[str],
        optimize_for_xhs: bool = True,
        model_config: dict = None,
    ) -> List[str]:
        """批量生成配图（并行）"""
        self._ensure_configured()
        if not visual_points:
            return []

        tasks = [
            self.generate_single_image(prompt=point, optimize_for_xhs=optimize_for_xhs, model_config=model_config)
            for point in visual_points
        ]
        results = await asyncio.gather(*tasks)

        image_paths = [path for path in results if path is not None]
        logger.info(f"成功生成 {len(image_paths)}/{len(visual_points)} 张图片")
        return image_paths


# 单例实例
image_service = ImageService()
