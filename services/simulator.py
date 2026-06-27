"""五通道温度仿真引擎。"""

import json
import random

from models.sensor_data import SensorData, SensorHistory
from utils.path_utils import app_base_dir


BASE_DIR = app_base_dir()
CONFIG_PATH = BASE_DIR / "config.json"

# 默认仿真参数（config.json 缺失或字段缺失时回退使用）
_DEFAULTS = {
    "initial_furnace_temp": 25.0,
    "target_furnace_temp": 750.0,
    "heating_rate_per_second": 40.0,
    "temp_fluctuation": 0.5,
    "stable_threshold": 3.0,
    "tick_ms": 800,
}


def _load_simulation_config() -> dict:
    """从 config.json 读取 simulation 段，缺失时回退默认值。"""
    config = dict(_DEFAULTS)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        sim = data.get("simulation", {})
        for key in _DEFAULTS:
            if key in sim:
                config[key] = sim[key]
    except (OSError, json.JSONDecodeError):
        pass
    return config


class SensorSimulator:
    """根据当前状态生成炉温、样品温度和校准温。"""

    # 温漂计算窗口：最近 10 分钟
    DRIFT_WINDOW_SECONDS = 600
    # 稳定判定使用最近窗口（替代简单 stable_count）
    STABLE_WINDOW_SECONDS = 10
    STABLE_MIN_SAMPLES = 5

    # 异常模式常量（用于温度异常测试）
    ANOMALY_NONE = "none"
    ANOMALY_SPIKE = "spike"            # 温度尖峰
    ANOMALY_SENSOR_FAILURE = "sensor_failure"  # 传感器失效
    ANOMALY_OVERHEAT = "overheat"      # 超温

    def __init__(self) -> None:
        cfg = _load_simulation_config()
        self.initial_temp = float(cfg["initial_furnace_temp"])
        self.target_temp = float(cfg["target_furnace_temp"])
        self.heating_rate_per_second = float(cfg["heating_rate_per_second"])
        self.temp_fluctuation = float(cfg["temp_fluctuation"])
        self.stable_threshold = float(cfg["stable_threshold"])
        self.tick_ms = int(cfg["tick_ms"])
        self.tick_seconds = self.tick_ms / 1000.0

        self.stable_count = 0
        self.data = SensorData(tf1=self.initial_temp, tf2=self.initial_temp)
        self._elapsed = 0.0
        # 采样历史承载最近 10 分钟温漂计算
        self._history = SensorHistory(window_seconds=self.DRIFT_WINDOW_SECONDS)
        self.anomaly_mode = self.ANOMALY_NONE

    def reset(self) -> None:
        """重置仿真温度。"""
        self.stable_count = 0
        self.data = SensorData(tf1=self.initial_temp, tf2=self.initial_temp)
        self._elapsed = 0.0
        self._history.reset()
        self.anomaly_mode = self.ANOMALY_NONE

    def set_anomaly_mode(self, mode: str) -> None:
        """设置异常模式用于温度异常测试。"""
        self.anomaly_mode = mode

    def update(self, state: str, record_seconds: int) -> SensorData:
        """每 tick_ms 更新一次温度。"""
        self._elapsed += self.tick_seconds
        noise1 = self._noise()
        noise2 = self._noise()

        if state == "Preparing":
            if self.data.tf1 < self.target_temp - self.stable_threshold:
                self.data.tf1 += self.heating_rate_per_second * self.tick_seconds + noise1
                self.data.tf2 += self.heating_rate_per_second * self.tick_seconds + noise2
                self.stable_count = 0
            else:
                self.data.tf1 = self.target_temp + noise1
                self.data.tf2 = self.target_temp + noise2
                self.stable_count += 1
            self.data.ts = self.data.tf1 * 0.30 + self._noise()
            self.data.tc = self.data.tf1 * 0.25 + self._noise()

        elif state == "Ready":
            self.data.tf1 = self.target_temp + noise1
            self.data.tf2 = self.target_temp + noise2
            # 同步表面温/中心温，避免异常模式残留旧值（与 Preparing 末态一致）
            self.data.ts = self.data.tf1 * 0.30 + self._noise()
            self.data.tc = self.data.tf1 * 0.25 + self._noise()
            self.stable_count += 1

        elif state == "Recording":
            self.data.time_seconds = record_seconds
            self.data.tf1 = self.target_temp + noise1
            self.data.tf2 = self.target_temp + noise2
            surface_target = min(self.data.tf1 * 0.95, 800)
            center_target = min(self.data.tf1 * 0.85, 750)
            self.data.ts += (surface_target - self.data.ts) * 0.02 + self._noise()
            self.data.tc += (center_target - self.data.tc) * 0.01 + self._noise()

        elif state == "Idle":
            self.data.tf1 = max(self.initial_temp, self.data.tf1 - 0.5 + self._noise() * 0.1)
            self.data.tf2 = max(self.initial_temp, self.data.tf2 - 0.5 + self._noise() * 0.1)

        self.data.tcal = self.data.tf1 + self._noise() * 2

        # 注入异常用于温度异常测试
        self._apply_anomaly()

        # 记录历史用于最近 10 分钟温漂计算
        self._history.add(self._elapsed, self.data.tf1, self.data.tf2)

        return SensorData(
            time_seconds=self.data.time_seconds,
            tf1=self.data.tf1,
            tf2=self.data.tf2,
            ts=self.data.ts,
            tc=self.data.tc,
            tcal=self.data.tcal,
        )

    def _apply_anomaly(self) -> None:
        """根据异常模式修改输出温度，用于温度异常测试。"""
        if self.anomaly_mode == self.ANOMALY_SPIKE:
            self.data.tf1 += 80.0
            self.data.tf2 += 80.0
        elif self.anomaly_mode == self.ANOMALY_SENSOR_FAILURE:
            # 传感器失效：输出固定异常值
            self.data.tf1 = -20.0
            self.data.tf2 = -20.0
            self.data.ts = -20.0
            self.data.tc = -20.0
        elif self.anomaly_mode == self.ANOMALY_OVERHEAT:
            self.data.tf1 = self.target_temp + 60.0
            self.data.tf2 = self.target_temp + 60.0

    def is_stable(self) -> bool:
        """判断炉温是否已稳定：接近目标且最近窗口温漂很小。"""
        lo = self.target_temp - self.stable_threshold
        hi = self.target_temp + self.stable_threshold
        if not (lo <= self.data.tf1 <= hi and lo <= self.data.tf2 <= hi):
            return False
        recent = self._history.recent(self.STABLE_WINDOW_SECONDS)
        if len(recent) < self.STABLE_MIN_SAMPLES:
            return False
        tf1_range = max(p[1] for p in recent) - min(p[1] for p in recent)
        tf2_range = max(p[2] for p in recent) - min(p[2] for p in recent)
        return tf1_range <= self.stable_threshold and tf2_range <= self.stable_threshold

    def calc_drift(self) -> float:
        """计算最近 10 分钟炉温1 的温漂（℃/min）。"""
        return self._history.drift_per_minute()

    def _noise(self) -> float:
        return random.uniform(-1, 1) * self.temp_fluctuation
