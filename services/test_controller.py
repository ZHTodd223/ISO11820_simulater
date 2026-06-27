"""试验流程状态机。"""

from datetime import datetime
from typing import Callable, Optional

from models.sensor_data import SensorData
from models.test_record import TestRecord
from services.simulator import SensorSimulator


class TestController:
    """控制 Idle/Preparing/Ready/Recording/Complete 状态流转。

    状态流转图：
        Idle ──(开始升温)──→ Preparing ──(温度稳定)──→ Ready ──(开始记录)──→ Recording
         ↑                      ↑   ←──(温度跌出稳定范围)──   │
         │                      ↑                              │
         │                      └──(保存后保温)── Complete ←───┘
         │                           (手动/自动/固定时长)
         └──(停止升温)── Preparing / Ready / Complete
    """

    STATES = {
        "Idle": "空闲",
        "Preparing": "升温中",
        "Ready": "就绪",
        "Recording": "记录中",
        "Complete": "完成",
    }

    # 试验时长模式
    DURATION_MODES = {
        "standard_60min": "标准60分钟",
        "fixed": "固定时长",
        "manual": "手动停止",
    }

    def __init__(self) -> None:
        self.state = "Idle"
        self.current_test: Optional[TestRecord] = None
        self.simulator = SensorSimulator()
        self.record_seconds = 0
        self.record_samples: list[SensorData] = []
        self.on_message: Optional[Callable[[str], None]] = None
        self.on_state_changed: Optional[Callable[[str], None]] = None

        # 未保存试验保护：Recording 完成后置 True，保存后置 False
        self.needs_save: bool = False

        # 试验时长配置
        self.duration_mode: str = "standard_60min"
        self.target_duration_seconds: int = 3600

    # ── 试验时长配置 ──────────────────────────────────────────────────

    def set_duration_mode(self, mode: str, target_seconds: int = 3600) -> None:
        """设置试验时长模式。

        Args:
            mode: 'standard_60min' | 'fixed' | 'manual'
            target_seconds: 固定模式下的目标秒数（最低 60 秒）
        """
        if mode not in self.DURATION_MODES:
            return
        self.duration_mode = mode
        if mode == "standard_60min":
            self.target_duration_seconds = 3600
        elif mode == "fixed":
            self.target_duration_seconds = max(60, target_seconds)
        else:  # manual
            self.target_duration_seconds = 999_999_999

    # ── 试验生命周期 ──────────────────────────────────────────────────

    def set_current_test(self, record: TestRecord) -> None:
        """设置当前试验。"""
        if self.needs_save:
            self._message("⚠ 上一试验尚未保存，新建试验将丢弃未保存的数据")
        self.current_test = record
        self.record_seconds = 0
        self.record_samples.clear()
        self.needs_save = False
        self._message(f"已创建试验：{record.productid} / {record.testid}")

    def start_heating(self) -> None:
        """Idle -> Preparing。"""
        if self.state != "Idle":
            return
        if self.needs_save:
            self._message("⚠ 上一试验尚未保存，请先保存试验记录")
            return
        self.simulator.reset()
        self._set_state("Preparing")
        self._message("开始升温，系统升温中")

    def start_recording(self) -> bool:
        """Ready -> Recording。"""
        if self.state != "Ready" or not self.current_test:
            self._message("请先新建试验并等待温度稳定")
            return False
        self.record_seconds = 0
        self.record_samples.clear()
        self._set_state("Recording")
        self._message("开始记录，计时开始")
        return True

    def stop_recording(self) -> None:
        """Recording -> Complete（手动停止）。"""
        if self.state == "Recording":
            self._set_state("Complete")
            self.needs_save = True
            self._message("用户手动停止记录")

    def stop_heating(self) -> None:
        """停止升温并回到空闲（炉温开始下降）。"""
        if self.state in ("Preparing", "Ready", "Complete"):
            self._set_state("Idle")
            self._message("停止升温，炉温开始下降")

    def mark_saved(self) -> None:
        """标记当前试验已保存。

        Complete → Preparing（保温），炉子保持高温，
        用户新建下一次试验后可直接等待 Ready，省去升温时间。
        """
        self.needs_save = False
        self._message("试验记录已保存，系统保持恒温状态")
        if self.state == "Complete":
            self._set_state("Preparing")

    # ── 定时驱动 ──────────────────────────────────────────────────────

    def tick(self) -> SensorData:
        """主界面每 800ms 调用一次，驱动仿真和状态检查。"""
        data = self.simulator.update(self.state, self.record_seconds)

        if self.state == "Preparing" and self.simulator.is_stable():
            self._set_state("Ready")
            self._message("温度已稳定，可以开始记录")

        elif self.state == "Ready":
            # Ready → Preparing：温度跌出稳定范围时自动回退
            if not self.simulator.is_stable():
                self._set_state("Preparing")
                self._message("炉温波动，重新升温中")

        elif self.state == "Recording":
            self.record_seconds += 1
            data.time_seconds = self.record_seconds
            self.record_samples.append(data)

            # 检查是否到达目标时长（自动停止）
            if self.record_seconds >= self.target_duration_seconds:
                self._auto_complete(
                    f"记录时间到达 {self.target_duration_seconds} 秒，试验自动结束"
                )
                return data

        return data

    # ── 试验结果计算 ──────────────────────────────────────────────────

    def build_result(self, postweight: float, has_flame: bool, flame_time: int, flame_duration: int, memo: str) -> dict:
        """根据记录样本计算试验结果。"""
        if not self.current_test or not self.record_samples:
            raise ValueError("没有可保存的试验数据")

        preweight = self.current_test.preweight
        lostweight = preweight - postweight
        lostweight_per = lostweight / preweight * 100 if preweight > 0 else 0
        final = self.record_samples[-1]
        maxtf1 = max(x.tf1 for x in self.record_samples)
        maxtf2 = max(x.tf2 for x in self.record_samples)
        maxts = max(x.ts for x in self.record_samples)
        maxtc = max(x.tc for x in self.record_samples)

        return {
            "postweight": postweight,
            "lostweight": lostweight,
            "lostweight_per": lostweight_per,
            "totaltesttime": self.record_seconds,
            "phenocode": "flame" if has_flame else "none",
            "flametime": flame_time if has_flame else 0,
            "flameduration": flame_duration if has_flame else 0,
            "maxtf1": maxtf1,
            "maxtf2": maxtf2,
            "maxts": maxts,
            "maxtc": maxtc,
            "finaltf1": final.tf1,
            "finaltf2": final.tf2,
            "finalts": final.ts,
            "finaltc": final.tc,
            "deltatf1": final.tf1 - self.current_test.ambtemp,
            "deltatf2": final.tf2 - self.current_test.ambtemp,
            "deltatf": final.ts - self.current_test.ambtemp,
            "deltats": final.ts - self.current_test.ambtemp,
            "deltatc": final.tc - self.current_test.ambtemp,
            "memo": memo,
        }

    # ── 内部方法 ──────────────────────────────────────────────────────

    def _auto_complete(self, message: str) -> None:
        """自动完成试验（到达时长或满足终止条件）。"""
        self._set_state("Complete")
        self.needs_save = True
        self._message(message)

    def _set_state(self, state: str) -> None:
        self.state = state
        if self.on_state_changed:
            self.on_state_changed(state)

    def _message(self, text: str) -> None:
        msg = f"{datetime.now().strftime('%H:%M:%S')}  {text}"
        if self.on_message:
            self.on_message(msg)

    # TODO[B]: 将按钮可用状态整理为独立方法，供主界面直接绑定。
