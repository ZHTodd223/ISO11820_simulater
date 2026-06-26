"""CSV 温度数据导出服务。"""

import csv
from pathlib import Path

from models.sensor_data import SensorData
from models.test_record import TestRecord


def export_sensor_csv(record: TestRecord, samples: list[SensorData]) -> Path:
    """导出每秒温度数据。"""
    out_dir = Path("test_data") / record.productid / record.testid
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "sensor_data.csv"
    with out_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["Time", "Temp1", "Temp2", "TempSurface", "TempCenter", "TempCalibration"])
        for sample in samples:
            writer.writerow(sample.as_csv_row())
    return out_path

    # TODO[D]: 增加导出失败时的用户友好提示。
