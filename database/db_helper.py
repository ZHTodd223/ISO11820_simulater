"""数据库访问封装，所有 sqlite3 操作尽量集中在这里。"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from models.calibration_record import CalibrationRecord
from models.test_record import TestRecord


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "ISO11820.db"


class DbHelper:
    """SQLite 数据库帮助类。"""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def login(self, username: str, pwd: str) -> Optional[dict]:
        """按 username + pwd 验证登录。"""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT userid, username, usertype FROM operators WHERE username=? AND pwd=?",
                (username, pwd),
            ).fetchone()
        return dict(row) if row else None

    def insert_new_test(self, record: TestRecord) -> None:
        """新建样品和试验主记录。"""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO productmaster
                (productid, productname, specific, diameter, height, flag)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record.productid,
                    record.productname,
                    record.specific,
                    record.diameter,
                    record.height,
                    "",
                ),
            )
            conn.execute(
                """
                INSERT INTO testmaster (
                    productid, testid, testdate, ambtemp, ambhumi, according, operator,
                    apparatusid, apparatusname, apparatuschkdate, rptno, preweight,
                    postweight, lostweight, lostweight_per, totaltesttime, constpower,
                    phenocode, flametime, flameduration, maxtf1, maxtf2, maxts, maxtc,
                    finaltf1, finaltf2, finalts, finaltc, deltatf1, deltatf2, deltatf,
                    deltats, deltatc, memo, flag
                ) VALUES (
                    ?, ?, ?, ?, ?, 'ISO 11820:2022', ?, 'FURNACE-01', '一号试验炉',
                    date('now'), ?, ?, 0, 0, 0, 0, 2048, '', 0, 0, 0, 0, 0, 0,
                    0, 0, 0, 0, 0, 0, 0, 0, 0, '', ''
                )
                """,
                (
                    record.productid,
                    record.testid,
                    record.testdate,
                    record.ambtemp,
                    record.ambhumi,
                    record.operator,
                    record.testid,
                    record.preweight,
                ),
            )
            conn.commit()

    def update_test_result(self, record: TestRecord, result: dict) -> None:
        """试验完成后更新统计字段。"""
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE testmaster SET
                    postweight=?, lostweight=?, lostweight_per=?, totaltesttime=?,
                    phenocode=?, flametime=?, flameduration=?,
                    maxtf1=?, maxtf2=?, maxts=?, maxtc=?,
                    finaltf1=?, finaltf2=?, finalts=?, finaltc=?,
                    deltatf1=?, deltatf2=?, deltatf=?, deltats=?, deltatc=?,
                    memo=?, flag='10000000'
                WHERE productid=? AND testid=?
                """,
                (
                    result["postweight"],
                    result["lostweight"],
                    result["lostweight_per"],
                    result["totaltesttime"],
                    result["phenocode"],
                    result["flametime"],
                    result["flameduration"],
                    result["maxtf1"],
                    result["maxtf2"],
                    result["maxts"],
                    result["maxtc"],
                    result["finaltf1"],
                    result["finaltf2"],
                    result["finalts"],
                    result["finaltc"],
                    result["deltatf1"],
                    result["deltatf2"],
                    result["deltatf"],
                    result["deltats"],
                    result["deltatc"],
                    result["memo"],
                    record.productid,
                    record.testid,
                ),
            )
            conn.commit()

    def query_tests(self, keyword: str = "") -> list[dict]:
        """查询历史试验记录。"""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT productid, testid, testdate, operator, totaltesttime, lostweight_per, deltatf, flag
                FROM testmaster
                WHERE productid LIKE ? OR testid LIKE ?
                ORDER BY testdate DESC, testid DESC
                LIMIT 100
                """,
                (f"%{keyword}%", f"%{keyword}%"),
            ).fetchall()
        return [dict(row) for row in rows]

    def insert_calibration_record(self, record: CalibrationRecord) -> None:
        """保存设备校准记录。"""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO CalibrationRecords
                (Id, CalibrationDate, CalibrationType, ApparatusId, Operator, TemperatureData,
                 PassedCriteria, Remarks, CreatedAt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.calibration_date,
                    record.calibration_type,
                    record.apparatus_id,
                    record.operator,
                    record.temperature_data,
                    record.passed_criteria,
                    record.remarks,
                    record.created_at,
                ),
            )
            conn.commit()

    def query_calibrations(self) -> list[dict]:
        """查询最近校准记录。"""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT CalibrationDate, Operator, TemperatureData, PassedCriteria, Remarks
                FROM CalibrationRecords
                ORDER BY CreatedAt DESC
                LIMIT 50
                """
            ).fetchall()
        return [dict(row) for row in rows]

    # TODO[A]: 增加按日期范围、操作员、样品编号组合查询接口。
    # TODO[F]: 为历史查询补充导出所需的完整字段。
