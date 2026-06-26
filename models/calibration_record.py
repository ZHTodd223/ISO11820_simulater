"""设备校准记录模型。"""

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4


@dataclass
class CalibrationRecord:
    """一条校准历史记录。"""

    operator: str
    temperature_data: str
    calibration_type: str = "Temperature"
    apparatus_id: int = 0
    passed_criteria: int = 1
    remarks: str = ""
    id: str = ""
    calibration_date: str = ""
    created_at: str = ""

    def __post_init__(self) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        if not self.id:
            self.id = str(uuid4())
        if not self.calibration_date:
            self.calibration_date = now
        if not self.created_at:
            self.created_at = now
