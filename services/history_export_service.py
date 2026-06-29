"""历史试验记录重新导出服务。"""

import csv
from pathlib import Path

from models.sensor_data import SensorData
from models.test_record import TestRecord
from services.csv_service import export_sensor_csv
from services.excel_service import export_excel_report
from services.export_paths import get_test_export_dir
from services.pdf_service import export_pdf_report
from utils.path_utils import app_base_dir


def export_history_record(detail: dict) -> tuple[list[Path], int]:
    """根据数据库中的历史记录重新导出 CSV、Excel 和 PDF。"""
    record = _record_from_detail(detail)
    result = _result_from_detail(detail)
    samples = _load_existing_samples(record)
    paths = [
        export_sensor_csv(record, samples),
        export_excel_report(record, samples, result),
        export_pdf_report(record, samples, result),
    ]
    return paths, len(samples)


def _record_from_detail(detail: dict) -> TestRecord:
    return TestRecord(
        productid=str(detail.get("productid") or ""),
        testid=str(detail.get("testid") or ""),
        productname=str(detail.get("productname") or "历史样品"),
        specific=str(detail.get("specific") or ""),
        diameter=float(detail.get("diameter") or 0),
        height=float(detail.get("height") or 0),
        operator=str(detail.get("operator") or ""),
        preweight=float(detail.get("preweight") or 0),
        ambtemp=float(detail.get("ambtemp") or 25),
        ambhumi=float(detail.get("ambhumi") or 50),
        testdate=str(detail.get("testdate") or ""),
        postweight=float(detail.get("postweight") or 0),
        memo=str(detail.get("memo") or ""),
    )


def _result_from_detail(detail: dict) -> dict:
    keys = [
        "postweight", "lostweight", "lostweight_per", "totaltesttime",
        "phenocode", "flametime", "flameduration", "maxtf1", "maxtf2",
        "maxts", "maxtc", "finaltf1", "finaltf2", "finalts", "finaltc",
        "deltatf1", "deltatf2", "deltatf", "deltats", "deltatc", "memo",
    ]
    result = {key: detail.get(key) for key in keys}
    for key in keys:
        if key in ("phenocode", "memo"):
            result[key] = str(result.get(key) or "")
        elif result[key] is None:
            result[key] = 0
    return result


def _load_existing_samples(record: TestRecord) -> list[SensorData]:
    candidates = [
        get_test_export_dir(record) / "sensor_data.csv",
        app_base_dir() / "test_data" / record.productid / record.testid / "sensor_data.csv",
    ]
    for path in candidates:
        if path.exists():
            return _read_sensor_csv(path)
    return []


def _read_sensor_csv(path: Path) -> list[SensorData]:
    samples: list[SensorData] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            samples.append(
                SensorData(
                    time_seconds=int(float(row.get("Time") or 0)),
                    tf1=float(row.get("Temp1") or 0),
                    tf2=float(row.get("Temp2") or 0),
                    ts=float(row.get("TempSurface") or 0),
                    tc=float(row.get("TempCenter") or 0),
                    tcal=float(row.get("TempCalibration") or 0),
                )
            )
    return samples
