"""设备校准服务。"""

import json
from typing import Optional

from database.db_helper import DbHelper
from models.calibration_record import CalibrationRecord

# 标准温度点（℃）与允许偏差（℃）
STANDARD_TEMP_POINTS = [100, 200, 400, 600, 750]
DEFAULT_TOLERANCE = 5.0  # 默认允许偏差 ±5℃


class CalibrationService:
    """保存和查询设备校准数据。"""

    def __init__(self) -> None:
        self.db = DbHelper()

    def save_current_temperature(self, operator: str, tcal: float, remarks: str = "") -> None:
        """保存当前校准温度（单点快速校准）。"""
        payload = json.dumps({"tcal": round(tcal, 2)}, ensure_ascii=False)
        record = CalibrationRecord(operator=operator, temperature_data=payload, remarks=remarks)
        self.db.insert_calibration_record(record)

    def save_multi_point_calibration(
        self,
        operator: str,
        readings: dict[int, float],
        remarks: str = "",
        tolerance: float = DEFAULT_TOLERANCE,
    ) -> dict:
        """保存多点校准记录并返回判定结果。

        Args:
            operator: 操作员用户名。
            readings: {标准温度值: 实测温度值}，如 {100: 102.3, 200: 198.5, ...}。
            remarks: 备注。
            tolerance: 允许偏差（℃），默认 ±5℃。

        Returns:
            {
                "passed": True/False,
                "failed_points": [100, ...],    # 不合格的温度点
                "detail": {100: {"expected": 100, "actual": 102.3, "deviation": 2.3, "ok": True}, ...},
            }
        """
        detail = {}
        failed_points = []
        for std_temp, actual_temp in readings.items():
            deviation = actual_temp - std_temp
            ok = abs(deviation) <= tolerance
            detail[std_temp] = {
                "expected": std_temp,
                "actual": round(actual_temp, 2),
                "deviation": round(deviation, 2),
                "ok": ok,
            }
            if not ok:
                failed_points.append(std_temp)

        passed = len(failed_points) == 0 and len(readings) > 0
        payload = json.dumps({
            "type": "multi_point",
            "tolerance": tolerance,
            "readings": {str(k): round(v, 2) for k, v in readings.items()},
            "detail": detail,
            "passed": passed,
        }, ensure_ascii=False)

        record = CalibrationRecord(
            operator=operator,
            temperature_data=payload,
            passed_criteria=1 if passed else 0,
            remarks=remarks,
        )
        self.db.insert_calibration_record(record)

        return {"passed": passed, "failed_points": failed_points, "detail": detail}

    def list_records(self) -> list[dict]:
        """查询校准历史。"""
        return self.db.query_calibrations()

    def get_record_detail(self, calibration_date: str, operator: str) -> Optional[dict]:
        """根据日期和操作员获取单条校准记录的详细数据。"""
        records = self.db.query_calibrations()
        for r in records:
            if r["CalibrationDate"] == calibration_date and r["Operator"] == operator:
                return dict(r)
        return None
