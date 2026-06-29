"""统一导出目录工具。"""

from pathlib import Path

from models.test_record import TestRecord
from utils.path_utils import app_base_dir


def get_test_export_dir(record: TestRecord) -> Path:
    """返回当前试验的统一导出目录。"""
    safe_productid = _safe_path_part(record.productid)
    safe_testid = _safe_path_part(record.testid)
    out_dir = app_base_dir() / "exports" / safe_productid / safe_testid
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _safe_path_part(value: str) -> str:
    """替换 Windows 路径非法字符，避免编号中带特殊符号时导出失败。"""
    text = str(value).strip() or "unknown"
    for ch in '<>:"/\\|?*':
        text = text.replace(ch, "_")
    return text
