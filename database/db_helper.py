"""数据库访问封装，所有 sqlite3 操作尽量集中在这里。"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from models.calibration_record import CalibrationRecord
from models.test_record import TestRecord
from utils.path_utils import app_base_dir

BASE_DIR = app_base_dir()
DB_PATH = BASE_DIR / "data" / "ISO11820.db"


class DbHelper:
    """SQLite 数据库帮助类。"""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ── 登录 ──────────────────────────────────────────────────────────

    def login(self, username: str, pwd: str) -> Optional[dict]:
        """按 username + pwd 验证登录。"""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT userid, username, usertype FROM operators WHERE username=? AND pwd=?",
                (username, pwd),
            ).fetchone()
        return dict(row) if row else None

    # ── 操作员管理 ────────────────────────────────────────────────────

    def query_operators(self) -> list[dict]:
        """查询所有操作员。"""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT userid, username, usertype FROM operators ORDER BY userid"
            ).fetchall()
        return [dict(row) for row in rows]

    def add_operator(self, username: str, pwd: str, usertype: str) -> None:
        """新增操作员账号。

        Raises:
            ValueError: 用户名已存在或参数无效。
        """
        if not username.strip():
            raise ValueError("用户名不能为空")
        if not pwd.strip():
            raise ValueError("密码不能为空")
        if usertype not in ("admin", "operator"):
            raise ValueError("用户类型必须是 admin 或 operator")

        with self._connect() as conn:
            existing = conn.execute(
                "SELECT 1 FROM operators WHERE username=?", (username.strip(),)
            ).fetchone()
            if existing:
                raise ValueError(f"用户名 '{username.strip()}' 已存在，请换一个用户名")
            conn.execute(
                "INSERT INTO operators (userid, username, pwd, usertype) VALUES (?, ?, ?, ?)",
                (str(self._next_userid(conn)), username.strip(), pwd.strip(), usertype),
            )
            conn.commit()

    def delete_operator(self, username: str) -> None:
        """删除操作员账号（不允许删除最后一个管理员）。

        Raises:
            ValueError: 用户名不存在或为最后一个管理员。
        """
        with self._connect() as conn:
            row = conn.execute(
                "SELECT usertype FROM operators WHERE username=?", (username,)
            ).fetchone()
            if not row:
                raise ValueError(f"用户 '{username}' 不存在")
            if row["usertype"] == "admin":
                admin_count = conn.execute(
                    "SELECT COUNT(*) AS cnt FROM operators WHERE usertype='admin'"
                ).fetchone()["cnt"]
                if admin_count <= 1:
                    raise ValueError("不能删除最后一个管理员账号")
            conn.execute("DELETE FROM operators WHERE username=?", (username,))
            conn.commit()

    def update_operator_password(self, username: str, new_pwd: str) -> None:
        """修改操作员密码。

        Raises:
            ValueError: 用户名不存在或密码为空。
        """
        if not new_pwd.strip():
            raise ValueError("密码不能为空")
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM operators WHERE username=?", (username,)
            ).fetchone()
            if not row:
                raise ValueError(f"用户 '{username}' 不存在")
            conn.execute(
                "UPDATE operators SET pwd=? WHERE username=?",
                (new_pwd.strip(), username),
            )
            conn.commit()

    def _next_userid(self, conn: sqlite3.Connection) -> int:
        row = conn.execute("SELECT MAX(CAST(userid AS INTEGER)) AS mx FROM operators").fetchone()
        return (row["mx"] or 0) + 1

    # ── 新建试验 ──────────────────────────────────────────────────────

    def check_test_exists(self, productid: str, testid: str) -> bool:
        """检查 (productid, testid) 组合是否已存在。"""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM testmaster WHERE productid=? AND testid=?",
                (productid, testid),
            ).fetchone()
        return row is not None

    def insert_new_test(self, record: TestRecord) -> None:
        """新建样品和试验主记录。

        Raises:
            ValueError: 当 (productid, testid) 组合已存在时给出清晰提示。
        """
        if self.check_test_exists(record.productid, record.testid):
            raise ValueError(
                f"试验编号 '{record.testid}' 在样品 '{record.productid}' 下已存在，\n"
                "请修改样品编号或试验编号后重新创建。"
            )

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

    # ── 试验结果更新 ──────────────────────────────────────────────────

    def update_test_result(self, record: TestRecord, result: dict) -> None:
        """试验完成后更新统计字段。

        Raises:
            sqlite3.IntegrityError / ValueError 皆由调用方处理。
        """
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

    # ── 历史查询 ──────────────────────────────────────────────────────

    def query_tests(
        self,
        keyword: str = "",
        date_from: str = "",
        date_to: str = "",
        operator: str = "",
    ) -> list[dict]:
        """按样品/试验编号、日期范围、操作员组合查询历史记录。

        不传参数时返回最近 100 条记录。
        """
        conditions = []
        params: list = []

        if keyword.strip():
            conditions.append("(t.productid LIKE ? OR t.testid LIKE ?)")
            params.extend([f"%{keyword.strip()}%", f"%{keyword.strip()}%"])
        if date_from.strip():
            conditions.append("t.testdate >= ?")
            params.append(date_from.strip())
        if date_to.strip():
            conditions.append("t.testdate <= ?")
            params.append(date_to.strip())
        if operator.strip():
            conditions.append("t.operator = ?")
            params.append(operator.strip())

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT t.productid, t.testid, t.testdate, t.operator,
                       t.totaltesttime, t.lostweight_per, t.deltatf, t.flag
                FROM testmaster t
                {where}
                ORDER BY t.testdate DESC, t.testid DESC
                LIMIT 100
                """,
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def query_test_full_detail(self, productid: str, testid: str) -> Optional[dict]:
        """查询单条试验的完整字段（供导出使用）。"""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM testmaster WHERE productid=? AND testid=?",
                (productid, testid),
            ).fetchone()
        return dict(row) if row else None

    # ── 设备校准 ──────────────────────────────────────────────────────

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
