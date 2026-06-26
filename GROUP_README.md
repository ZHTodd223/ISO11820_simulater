# 六人分工说明

## 总体原则

本项目按“数据库、状态机、仿真、报告、界面、集成测试”拆分。每位成员负责自己的模块，但所有模块都必须通过统一接口协作。不要把所有代码写进一个文件，也不要绕过 `db_helper.py` 直接在 UI 中到处写 SQL。

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

## 成员 F：组长 / 架构整合 / 测试与答辩模块

职责：

- 统一项目结构。
- 统一代码规范。
- 维护 README。
- 合并各成员代码。
- 解决模块接口冲突。
- 编写最终测试文档。
- 准备演示流程。
- 准备答辩说明。
- 使用 PyInstaller 打包项目。

重要说明：F 是掌管全局的组长，不是单独只写一个小功能。F 负责整体架构、进度、接口、集成、测试和答辩，必须持续检查 A-E 的模块能否组合成完整可演示系统。

## 推荐开发顺序

1. A 完成数据库初始化与登录。
2. B 完成状态机基础流转。
3. C 完成温度仿真与曲线。
4. D 完成保存结果和导出报告。
5. E 完成界面布局、校准和交互体验。
6. F 统一合并、测试、修复和打包。
