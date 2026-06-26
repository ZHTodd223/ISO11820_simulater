# 成员 A：数据库与登录模块

## 负责模块

数据库初始化、SQLite 访问封装、登录验证、新建试验入库、历史查询接口。

## 主要文件

| 文件 | 说明 |
|---|---|
| `database/init_db.py` | 创建数据库、表和默认数据 |
| `database/db_helper.py` | 封装登录、插入、更新、查询 |
| `ui/login_window.py` | 登录窗口 |
| `models/test_record.py` | 试验记录模型 |

## 需要实现的功能

- 初始化 `data/ISO11820.db`。
- 创建 6 张表。
- 写入默认账号、设备和 5 个传感器。
- 登录时按 `username + pwd` 查询。
- 新建试验时写入 `productmaster` 和 `testmaster`。
- 查询历史记录。

## 与其他成员的接口

| 调用方 | 接口 |
|---|---|
| 登录 UI | `DbHelper.login()` |
| 新建试验 UI | `DbHelper.insert_new_test()` |
| 试验记录模块 | `DbHelper.update_test_result()` |
| 历史查询 UI | `DbHelper.query_tests()` |

## 测试方法

运行 `python database/init_db.py`，检查 `data/ISO11820.db` 是否生成。启动程序后用 admin / 123456 登录。

## 最终交付物

数据库能初始化、登录能验证、新建试验能入库、历史查询能查到数据。

## TODO 清单

- TODO[A]: 增加按日期范围查询。
- TODO[A]: 增加操作员下拉查询。
- TODO[A]: 优化重复试验编号错误提示。
- TODO[F]: 检查数据库字段与报告字段一致性。
