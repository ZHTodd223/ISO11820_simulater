"""运行路径工具。

源码运行时返回项目根目录；PyInstaller 打包后返回 exe 所在目录。
"""

import sys
from pathlib import Path


def app_base_dir() -> Path:
    """获取应用运行根目录。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent
