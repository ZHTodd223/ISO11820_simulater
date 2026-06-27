"""传感器实时数据模型。"""

from collections import deque
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

    def is_anomalous(self) -> bool:
        """判断当前读数是否异常，用于温度异常测试检测。

        规则：任一通道低于 -10℃（传感器失效）或高于 1000℃（超温/尖峰）。
        """
        for value in (self.tf1, self.tf2, self.ts, self.tc, self.tcal):
            if value < -10.0 or value > 1000.0:
                return True
        return False


class SensorHistory:
    """传感器采样历史，承载最近 N 秒温漂计算。"""

    def __init__(self, window_seconds: float = 600.0) -> None:
        self.window_seconds = window_seconds
        self._samples: deque = deque()
        self._elapsed = 0.0

    def reset(self) -> None:
        """清空历史。"""
        self._samples.clear()
        self._elapsed = 0.0

    def add(self, elapsed: float, tf1: float, tf2: float) -> None:
        """追加一条采样 (elapsed_seconds, tf1, tf2)，并裁剪到窗口内。"""
        self._elapsed = float(elapsed)
        self._samples.append((self._elapsed, float(tf1), float(tf2)))
        self._trim()

    def recent(self, seconds: float) -> list:
        """返回最近 seconds 秒内的样本。"""
        if not self._samples:
            return []
        threshold = self._elapsed - seconds
        return [p for p in self._samples if p[0] >= threshold]

    def drift_per_minute(self) -> float:
        """计算窗口内炉温1 的温漂（℃/min）。"""
        window = list(self._samples)
        if len(window) < 2:
            return 0.0
        t0, tf1_0, _ = window[0]
        t1, tf1_1, _ = window[-1]
        dt = t1 - t0
        if dt <= 0:
            return 0.0
        return (tf1_1 - tf1_0) / dt * 60.0

    def __len__(self) -> int:
        return len(self._samples)

    def _trim(self) -> None:
        """丢弃窗口外的旧样本。"""
        threshold = self._elapsed - self.window_seconds
        while self._samples and self._samples[0][0] < threshold:
            self._samples.popleft()
