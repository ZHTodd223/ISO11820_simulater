"""五通道温度仿真引擎。"""

import random

from models.sensor_data import SensorData


class SensorSimulator:
    """根据当前状态生成炉温、样品温度和校准温。"""

    def __init__(self) -> None:
        self.target_temp = 750.0
        self.heating_rate_per_second = 40.0
        self.temp_fluctuation = 0.5
        self.stable_threshold = 3.0
        self.tick_seconds = 0.8
        self.stable_count = 0
        self.data = SensorData()

    def reset(self) -> None:
        """重置仿真温度。"""
        self.stable_count = 0
        self.data = SensorData()

    def update(self, state: str, record_seconds: int) -> SensorData:
        """每 800ms 更新一次温度。"""
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
            self.data.tf1 = max(25.0, self.data.tf1 - 0.5 + self._noise() * 0.1)
            self.data.tf2 = max(25.0, self.data.tf2 - 0.5 + self._noise() * 0.1)

        self.data.tcal = self.data.tf1 + self._noise() * 2
        return SensorData(
            time_seconds=self.data.time_seconds,
            tf1=self.data.tf1,
            tf2=self.data.tf2,
            ts=self.data.ts,
            tc=self.data.tc,
            tcal=self.data.tcal,
        )

    def is_stable(self) -> bool:
        """判断炉温是否已稳定。"""
        return self.data.tf1 >= 747 and self.data.tf2 >= 747 and self.stable_count > 3

    def _noise(self) -> float:
        return random.uniform(-1, 1) * self.temp_fluctuation

    # TODO[C]: 按最近 10 分钟数据计算温度漂移，替代简单 stable_count。
