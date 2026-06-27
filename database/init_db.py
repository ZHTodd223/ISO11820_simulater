"""SQLite 数据库初始化脚本。"""

import os
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "ISO11820.db"


def init_database() -> None:
    """创建数据库表并写入默认账号、设备和传感器。"""
    os.makedirs(DB_PATH.parent, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS operators (
                userid TEXT,
                username TEXT,
                pwd TEXT,
                usertype TEXT
            );

            CREATE TABLE IF NOT EXISTS apparatus (
                apparatusid INTEGER PRIMARY KEY,
                innernumber TEXT,
                apparatusname TEXT,
                checkdatef TEXT,
                checkdatet TEXT,
                pidport TEXT,
                powerport TEXT,
                constpower INTEGER
            );

            CREATE TABLE IF NOT EXISTS productmaster (
                productid TEXT PRIMARY KEY,
                productname TEXT,
                specific TEXT,
                diameter REAL,
                height REAL,
                flag TEXT
            );

            CREATE TABLE IF NOT EXISTS testmaster (
                productid TEXT,
                testid TEXT,
                testdate TEXT,
                ambtemp REAL,
                ambhumi REAL,
                according TEXT,
                operator TEXT,
                apparatusid TEXT,
                apparatusname TEXT,
                apparatuschkdate TEXT,
                rptno TEXT,
                preweight REAL,
                postweight REAL,
                lostweight REAL,
                lostweight_per REAL,
                totaltesttime INTEGER,
                constpower INTEGER,
                phenocode TEXT,
                flametime INTEGER,
                flameduration INTEGER,
                maxtf1 REAL,
                maxtf2 REAL,
                maxts REAL,
                maxtc REAL,
                finaltf1 REAL,
                finaltf2 REAL,
                finalts REAL,
                finaltc REAL,
                deltatf1 REAL,
                deltatf2 REAL,
                deltatf REAL,
                deltats REAL,
                deltatc REAL,
                memo TEXT,
                flag TEXT,
                PRIMARY KEY(productid, testid)
            );

            CREATE TABLE IF NOT EXISTS sensors (
                sensorid INTEGER PRIMARY KEY,
                sensorname TEXT,
                dispname TEXT,
                sensorgroup TEXT,
                unit TEXT,
                description TEXT,
                flag TEXT,
                outputvalue REAL
            );

            CREATE TABLE IF NOT EXISTS CalibrationRecords (
                Id TEXT PRIMARY KEY,
                CalibrationDate TEXT,
                CalibrationType TEXT,
                ApparatusId INTEGER,
                Operator TEXT,
                TemperatureData TEXT,
                PassedCriteria INTEGER,
                Remarks TEXT,
                CreatedAt TEXT
            );
            """
        )

        cur.execute(
            """
            INSERT INTO operators (userid, username, pwd, usertype)
            SELECT '1', 'admin', '123456', 'admin'
            WHERE NOT EXISTS (SELECT 1 FROM operators WHERE username='admin')
            """
        )
        cur.execute(
            """
            INSERT INTO operators (userid, username, pwd, usertype)
            SELECT '2', 'experimenter', '123456', 'operator'
            WHERE NOT EXISTS (SELECT 1 FROM operators WHERE username='experimenter')
            """
        )
        cur.execute(
            """
            INSERT OR IGNORE INTO apparatus
            VALUES (0, 'FURNACE-01', '一号试验炉', date('now'), date('now', '+1 year'), 'COM9', 'COM9', 2048)
            """
        )

        sensors = [
            (0, "Sensor0", "炉温1", "采集", "℃", "炉温1", "启用", 25.0),
            (1, "Sensor1", "炉温2", "采集", "℃", "炉温2", "启用", 25.0),
            (2, "Sensor2", "表面温度", "采集", "℃", "表面温度", "启用", 25.0),
            (3, "Sensor3", "中心温度", "采集", "℃", "中心温度", "启用", 25.0),
            (16, "Sensor16", "校准温度", "校准", "℃", "校准温度", "启用", 25.0),
        ]
        cur.executemany("INSERT OR IGNORE INTO sensors VALUES (?, ?, ?, ?, ?, ?, ?, ?)", sensors)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_database()
    print(f"数据库已初始化：{DB_PATH}")
