"""试验流程状态机。"""

from datetime import datetime
from typing import Callable, Optional

from models.sensor_data import SensorData
from models.test_record import TestRecord
from services.simulator import SensorSimulator


class TestController:
    """控制 Idle/Preparing/Ready/Recording/Complete 状态流转。"""

    STATES = {
        "Idle": "空闲",
        "Preparing": "升温中",
        "Ready": "就绪",
        "Recording": "记录中",
        "Complete": "完成",
    }

    def __init__(self) -> None:
        self.state = "Idle"
        self.current_test: Optional[TestRecord] = None
        self.simulator = SensorSimulator()
        self.record_seconds = 0
        self.record_samples: list[SensorData] = []
        self.on_message: Optional[Callable[[str], None]] = None
        self.on_state_changed: Optional[Callable[[str], None]] = None

    def set_current_test(self, record: TestRecord) -> None:
        """设置当前试验。"""
        self.current_test = record
        self.record_seconds = 0
        self.record_samples.clear()
        self._message(f"已创建试验：{record.productid} / {record.testid}")

    def start_heating(self) -> None:
        """Idle -> Preparing。"""
        if self.state != "Idle":
            return
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
        """Recording -> Complete。"""
        if self.state == "Recording":
            self._set_state("Complete")
            self._message("用户手动停止记录")

    def stop_heating(self) -> None:
        """停止升温并回到空闲。"""
        if self.state in ("Preparing", "Ready", "Complete"):
            self._set_state("Idle")
            self._message("停止升温，炉温开始下降")

    def tick(self) -> SensorData:
        """主界面定时调用，驱动仿真和状态检查。"""
        data = self.simulator.update(self.state, self.record_seconds)

        if self.state == "Preparing" and self.simulator.is_stable():
            self._set_state("Ready")
            self._message("温度已稳定，可以开始记录")
        elif self.state == "Recording":
            self.record_seconds += 1
            data.time_seconds = self.record_seconds
            self.record_samples.append(data)

        return data

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

    def _set_state(self, state: str) -> None:
        self.state = state
        if self.on_state_changed:
            self.on_state_changed(state)

    def _message(self, text: str) -> None:
        msg = f"{datetime.now().strftime('%H:%M:%S')}  {text}"
        if self.on_message:
            self.on_message(msg)

    # TODO[B]: 增加标准 60 分钟、固定时长和未保存试验保护。
    # TODO[B]: 将按钮可用状态整理为独立方法，供主界面直接绑定。
