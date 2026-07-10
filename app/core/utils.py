"""通用工具函数"""

from typing import List


def detect_image_format(raw_data: bytes) -> str:
    """通过文件头魔数检测图片格式"""
    if raw_data[:8] == b'\x89PNG\r\n\x1a\n':
        return "png"
    if raw_data[:3] == b'\xff\xd8\xff':
        return "jpg"
    if raw_data[:4] == b'RIFF' and raw_data[8:12] == b'WEBP':
        return "webp"
    return "jpg"

def fix_subgraph_status(status: str, generated_topics: List[str]) -> str:
    """修正子图 interrupt 时 status 未合并回父图的问题"""
    if status == "started" and generated_topics:
        return "topics_generated"
    return status
