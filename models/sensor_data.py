"""传感器实时数据模型。"""

from dataclasses import dataclass


@dataclass
class SensorData:
    """五通道温度数据。"""

    time_seconds: int = 0
    tf1: float = 25.0
    tf2: float = 25.0
    ts: float = 25.0
    tc: float = 25.0
    tcal: float = 25.0

    def as_csv_row(self) -> list:
        """转换为 CSV 行。"""
        return [
            self.time_seconds,
            f"{self.tf1:.1f}",
            f"{self.tf2:.1f}",
            f"{self.ts:.1f}",
            f"{self.tc:.1f}",
            f"{self.tcal:.1f}",
        ]
