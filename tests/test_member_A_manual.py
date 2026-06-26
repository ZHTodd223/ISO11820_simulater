# -*- coding: utf-8 -*-
"""成员 A 手动测试脚本 — 对应 tests/test_database_manual.md"""

import sys
import os

# 确保项目根目录在 sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS = "[PASS]"
FAIL = "[FAIL]"


def test_db001():
    """DB-001: 数据库初始化 — 执行 init_db.py，期望生成 data/ISO11820.db"""
    print("=" * 60)
    print("DB-001: 数据库初始化")
    print("=" * 60)
    from database.init_db import init_database
    from pathlib import Path

    db_path = Path("data/ISO11820.db")
    if db_path.exists():
        db_path.unlink()

    init_database()
    if db_path.exists():
        print(f"  {PASS} 数据库已生成: {db_path} ({db_path.stat().st_size} bytes)")
    else:
        print(f"  {FAIL} 数据库未生成")
        return False
    return True


def test_db002():
    """DB-002: 操作员初始化 — 查 operators 表，存在 admin 和 experimenter"""
    print("=" * 60)
    print("DB-002: 操作员初始化")
    print("=" * 60)
    import sqlite3

    conn = sqlite3.connect("data/ISO11820.db")
    cur = conn.cursor()

    # 检查 6 张表
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    expected = ["CalibrationRecords", "apparatus", "operators", "productmaster", "sensors", "testmaster"]
    all_tables_ok = all(t in tables for t in expected)
    print(f"  表: {tables}")
    print(f"  {PASS if all_tables_ok else FAIL} 6 张表齐全 (期望: {expected})")

    # 检查 operators
    cur.execute("SELECT * FROM operators ORDER BY userid")
    rows = cur.fetchall()
    usernames = [r[1] for r in rows]
    has_admin = "admin" in usernames
    has_exp = "experimenter" in usernames
    print(f"  operators 记录: {[(r[1], r[3]) for r in rows]}")
    print(f"  {PASS if has_admin and has_exp else FAIL} admin 和 experimenter 账号存在")

    # 检查 sensors (5 个)
    cur.execute("SELECT COUNT(*) FROM sensors")
    cnt = cur.fetchone()[0]
    print(f"  sensors 数量: {cnt}")
    print(f"  {PASS if cnt >= 5 else FAIL} 至少 5 个传感器")

    # 检查 apparatus
    cur.execute("SELECT innernumber, apparatusname FROM apparatus")
    app = cur.fetchone()
    print(f"  apparatus: {app[0]}, {app[1]}")
    print(f"  {PASS if app and app[0] == 'FURNACE-01' else FAIL} 设备记录正确")

    conn.close()
    return all_tables_ok and has_admin and has_exp and cnt >= 5


def test_db003():
    """DB-003: 登录验证 — admin / 123456 登录成功"""
    print("=" * 60)
    print("DB-003: 登录验证 (admin / 123456)")
    print("=" * 60)
    from database.db_helper import DbHelper

    db = DbHelper()
    user = db.login("admin", "123456")
    if user and user["username"] == "admin" and user["usertype"] == "admin":
        print(f"  {PASS} 登录成功 -> {user}")
        return True
    else:
        print(f"  {FAIL} 登录失败 -> {user}")
        return False


def test_db004():
    """DB-004: 登录失败 — admin / 111111 应返回 None"""
    print("=" * 60)
    print("DB-004: 登录失败 (admin / 111111)")
    print("=" * 60)
    from database.db_helper import DbHelper

    db = DbHelper()
    user = db.login("admin", "111111")
    if user is None:
        print(f"  {PASS} 密码错误返回 None (登录被拒绝)")
        return True
    else:
        print(f"  {FAIL} 错误密码居然登录成功 -> {user}")
        return False

    # 也测 experimenter 登录
    user2 = db.login("experimenter", "123456")
    if user2 and user2["usertype"] == "operator":
        print(f"  {PASS} 试验员登录成功 -> {user2}")
    else:
        print(f"  {FAIL} 试验员登录失败 -> {user2}")
        return False
    return True


def test_db005():
    """DB-005: 新建试验入库 — 写入 productmaster 和 testmaster"""
    print("=" * 60)
    print("DB-005: 新建试验入库")
    print("=" * 60)
    import sqlite3
    from database.db_helper import DbHelper
    from models.test_record import TestRecord

    db = DbHelper()

    record = TestRecord(
        productid="P20260626",
        testid="20260626-100000",
        productname="岩棉隔热板",
        specific="100x50x25mm",
        diameter=50.0,
        height=50.0,
        operator="admin",
        preweight=100.0,
        ambtemp=25.0,
        ambhumi=50.0,
    )

    # 插入
    try:
        db.insert_new_test(record)
        print(f"  {PASS} 新建试验写入成功")
    except Exception as e:
        print(f"  {FAIL} 写入失败: {e}")
        return False

    # 验证 productmaster
    conn = sqlite3.connect("data/ISO11820.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM productmaster WHERE productid='P20260626'")
    pm = cur.fetchone()
    print(f"  productmaster: {pm}")
    print(f"  {PASS if pm else FAIL} productmaster 有记录")

    # 验证 testmaster
    cur.execute("SELECT productid, testid, operator, preweight FROM testmaster WHERE productid='P20260626'")
    tm = cur.fetchone()
    print(f"  testmaster: {tm}")
    print(f"  {PASS if tm else FAIL} testmaster 有记录")

    # 测试重复插入拦截
    print("  测试重复试验编号拦截...")
    try:
        db.insert_new_test(record)
        print(f"  {FAIL} 重复插入未被拦截!")
        conn.close()
        return False
    except ValueError as e:
        msg = str(e)
        has_productid = record.productid in msg
        has_testid = record.testid in msg
        if has_productid or has_testid:
            print(f"  {PASS} 重复插入被正确拦截, 错误信息包含样品/试验编号")
        else:
            print(f"  {PASS} 重复插入被拦截 (信息: {msg[:60]}...)")

    conn.close()
    return True


def test_db006():
    """DB-006: 历史查询 — 能查到刚创建的试验"""
    print("=" * 60)
    print("DB-006: 历史查询")
    print("=" * 60)
    from database.db_helper import DbHelper

    db = DbHelper()

    # 关键字查询
    results = db.query_tests(keyword="P20260626")
    found = any(r["productid"] == "P20260626" for r in results)
    print(f"  关键字查询结果: {len(results)} 条")
    print(f"  {PASS if found else FAIL} 能通过关键字查到刚创建的试验")

    # 日期范围查询
    results2 = db.query_tests(date_from="2026-06-01", date_to="2026-12-31")
    found2 = any(r["productid"] == "P20260626" for r in results2)
    print(f"  日期范围查询结果: {len(results2)} 条")
    print(f"  {PASS if found2 else FAIL} 能通过日期范围查询")

    # 操作员查询
    results3 = db.query_tests(operator="admin")
    found3 = any(r["productid"] == "P20260626" for r in results3)
    print(f"  操作员查询结果: {len(results3)} 条")
    print(f"  {PASS if found3 else FAIL} 能通过操作员筛选")

    # 组合查询
    results4 = db.query_tests(keyword="P20", date_from="2026-01-01", operator="admin")
    found4 = any(r["productid"] == "P20260626" for r in results4)
    print(f"  组合查询结果: {len(results4)} 条")
    print(f"  {PASS if found4 else FAIL} 组合筛选正确")

    return found and found2 and found3 and found4


def test_operator_management():
    """附加: 操作员管理功能测试"""
    print("=" * 60)
    print("附加: 操作员账号管理")
    print("=" * 60)
    from database.db_helper import DbHelper

    db = DbHelper()

    # 查询操作员
    ops = db.query_operators()
    print(f"  当前操作员: {[o['username'] for o in ops]}")
    print(f"  {PASS if len(ops) >= 2 else FAIL} 查询操作员列表")

    # 新增操作员
    try:
        db.add_operator("test_user", "pass123", "operator")
        ops2 = db.query_operators()
        names = [o["username"] for o in ops2]
        if "test_user" in names:
            print(f"  {PASS} 新增操作员成功")
        else:
            print(f"  {FAIL} 新增操作员失败")
    except Exception as e:
        print(f"  {FAIL} 新增操作员异常: {e}")

    # 重复用户名检测
    try:
        db.add_operator("test_user", "pass456", "operator")
        print(f"  {FAIL} 重复用户名未被拦截")
    except ValueError:
        print(f"  {PASS} 重复用户名被正确拦截")

    # 修改密码
    try:
        db.update_operator_password("test_user", "newpass")
        user = db.login("test_user", "newpass")
        if user:
            print(f"  {PASS} 修改密码后可用新密码登录")
        else:
            print(f"  {FAIL} 修改密码后无法登录")
    except Exception as e:
        print(f"  {FAIL} 修改密码异常: {e}")

    # 删除操作员
    try:
        db.delete_operator("test_user")
        ops3 = db.query_operators()
        names3 = [o["username"] for o in ops3]
        if "test_user" not in names3:
            print(f"  {PASS} 删除操作员成功")
        else:
            print(f"  {FAIL} 删除操作员失败")
    except Exception as e:
        print(f"  {FAIL} 删除操作员异常: {e}")

    # 最后一个管理员保护
    try:
        db.delete_operator("admin")
        print(f"  {FAIL} 删除最后一个管理员未被拦截!")
        return False
    except ValueError:
        print(f"  {PASS} 最后一个管理员删除被正确拦截")

    return True


def cleanup():
    """清理测试数据"""
    import sqlite3
    conn = sqlite3.connect("data/ISO11820.db")
    conn.execute("DELETE FROM testmaster WHERE productid='P20260626'")
    conn.execute("DELETE FROM productmaster WHERE productid='P20260626'")
    conn.commit()
    conn.close()
    print("\n测试数据已清理")


def main():
    results = {}
    for name, func in [
        ("DB-001", test_db001),
        ("DB-002", test_db002),
        ("DB-003", test_db003),
        ("DB-004", test_db004),
        ("DB-005", test_db005),
        ("DB-006", test_db006),
        ("附加-操作员管理", test_operator_management),
    ]:
        try:
            results[name] = func()
        except Exception as e:
            print(f"  {FAIL} 测试异常: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False
        print()

    # 汇总
    print("=" * 60)
    print("测试汇总")
    print("=" * 60)
    for name, ok in results.items():
        status = "PASS" if ok else "FAIL"
        print(f"  {name}: {status}")

    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\n通过: {passed}/{total}")
    if passed == total:
        print("全部测试通过!")
    else:
        print(f"有 {total - passed} 项失败")

    cleanup()


if __name__ == "__main__":
    main()
