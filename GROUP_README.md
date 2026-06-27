# 六人分工说明

## 总体原则

本项目按“数据库、状态机、仿真、报告、界面校准、历史查询测试打包”拆分。每位成员负责自己的功能模块，但所有模块都必须通过统一接口协作。不要把所有代码写进一个文件，也不要绕过 `db_helper.py` 直接在 UI 中到处写 SQL。

项目组长由项目负责人兼任，组长同时参与功能实现，不单独占用一个成员分工。组长额外负责协调进度、合并代码、处理冲突、组织演示和答辩。

## 成员 A：数据库与登录模块

职责：

- 数据库初始化。
- SQLite 表结构。
- `db_helper.py`。
- 登录验证。
- 新建试验初始入库。
- 历史查询数据库接口。

主要文件：

- `database/init_db.py`
- `database/db_helper.py`
- `ui/login_window.py`
- `models/test_record.py`

## 成员 B：试验流程与状态机模块

职责：

- `test_controller.py`。
- Idle / Preparing / Ready / Recording / Complete 状态流转。
- 按钮可用状态控制。
- 未保存试验保护。
- 计时器控制。
- 系统消息触发。

主要文件：

- `services/test_controller.py`
- `ui/main_window.py`

## 成员 C：温度仿真与实时曲线模块

职责：

- `simulator.py`。
- 五个温度通道仿真。
- 每 800ms 更新温度。
- Matplotlib 实时曲线。
- 温度稳定判定。
- 温度漂移计算。

主要文件：

- `services/simulator.py`
- `models/sensor_data.py`
- `ui/main_window.py`

## 成员 D：试验记录与报告导出模块

职责：

- `test_record_window.py`。
- 试验后质量录入。
- 火焰现象记录。
- 失重量、失重率、温升计算。
- CSV 导出。
- Excel 导出。
- PDF 导出。

主要文件：

- `ui/test_record_window.py`
- `services/csv_service.py`
- `services/excel_service.py`
- `services/pdf_service.py`

## 成员 E：界面设计与设备校准模块

职责：

- `main_window.py`。
- `new_test_window.py`。
- `calibration_window.py`。
- 主界面布局。
- 设备校准录入。
- 校准历史查看。
- 系统消息日志显示。
- UI 美化。

主要文件：

- `ui/main_window.py`
- `ui/new_test_window.py`
- `ui/calibration_window.py`
- `services/calibration_service.py`

## 成员 F：历史查询 / 测试 / 打包模块

职责：

- 完善历史查询页面。
- 实现按日期、样品编号、操作员查询。
- 实现历史查询结果导出。
- 维护手动测试文档。
- 执行最终验收测试。
- 记录测试问题和修复情况。
- 使用 PyInstaller 打包项目。

重要说明：F 不再作为组长分工，而是负责一个明确的功能模块：历史查询、测试与打包。项目组长由项目负责人兼任，负责统筹所有成员协作。

## 推荐开发顺序

1. A 完成数据库初始化与登录。
2. B 完成状态机基础流转。
3. C 完成温度仿真与曲线。
4. D 完成保存结果和导出报告。
5. E 完成界面布局、校准和交互体验。
6. F 完善历史查询、执行最终测试并完成打包。
