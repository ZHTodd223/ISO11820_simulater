"""设备校准服务。"""

import json

from database.db_helper import DbHelper
from models.calibration_record import CalibrationRecord


class CalibrationService:
    """保存和查询设备校准数据。"""

    def __init__(self) -> None:
        self.db = DbHelper()

    def save_current_temperature(self, operator: str, tcal: float, remarks: str = "") -> None:
        """保存当前校准温度。"""
        payload = json.dumps({"tcal": round(tcal, 2)}, ensure_ascii=False)
        record = CalibrationRecord(operator=operator, temperature_data=payload, remarks=remarks)
        self.db.insert_calibration_record(record)

    def list_records(self) -> list[dict]:
        """查询校准历史。"""
        return self.db.query_calibrations()

    # TODO[E]: 支持多个标准温度点录入与合格判定。
