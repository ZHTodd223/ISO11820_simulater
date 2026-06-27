"""CSV 温度数据导出服务。"""

import csv
from pathlib import Path

from models.sensor_data import SensorData
from models.test_record import TestRecord
from utils.path_utils import app_base_dir


def export_sensor_csv(record: TestRecord, samples: list[SensorData]) -> Path:
    """导出每秒温度数据。"""
    out_dir = app_base_dir() / "test_data" / record.productid / record.testid
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "sensor_data.csv"
    try:
        with out_path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["Time", "Temp1", "Temp2", "TempSurface", "TempCenter", "TempCalibration"])
            for sample in samples:
                writer.writerow(sample.as_csv_row())
        return out_path
    except (OSError, PermissionError) as exc:
        raise RuntimeError(
            f"CSV 文件导出失败：{exc}\n"
            f"请检查文件 '{out_path}' 是否被其他程序打开或目录权限不足。"
        ) from exc
