# ISO11820_Python

## 1. 项目简介

本项目是“ISO 11820 建筑材料不燃性试验仿真系统”的 Python 课程作业版本。系统不连接真实硬件，通过软件仿真加热炉温度变化，完成登录、新建试验、开始升温、温度稳定、开始记录、停止记录、保存试验结果、导出报告、历史查询和设备校准等演示流程。

当前版本定位为“可运行最小版本 + 后续 TODO 骨架”，适合 6 人小组分工继续完善。

## 2. 技术栈

| 模块 | 技术 |
|---|---|
| 开发语言 | Python 3.11 / 3.12 |
| 桌面界面 | Tkinter |
| 数据库 | SQLite，使用 Python 自带 sqlite3 |
| 实时曲线 | Matplotlib |
| CSV 导出 | Python 自带 csv |
| Excel 导出 | openpyxl |
| PDF 导出 | ReportLab |
| 打包 | PyInstaller |

不使用 Flask、Django、FastAPI、Vue、React，也不做前后端分离。

## 3. 环境搭建

1. 安装 Python 3.11 或 3.12。
2. 进入项目目录：

```bash
cd ISO11820_Python
```

3. 创建虚拟环境：

```bash
python -m venv .venv
```

4. 激活虚拟环境：

```bash
.venv\Scripts\activate
```

5. 安装依赖：

```bash
pip install -r requirements.txt
```

6. 启动项目：

```bash
python main.py
```

默认账号：

| 角色 | 用户名 | 密码 |
|---|---|---|
| 管理员 | admin | 123456 |
| 试验员 | experimenter | 123456 |

## 4. 项目结构

```text
ISO11820_Python/
├── main.py
├── config.json
├── requirements.txt
├── README.md
├── GROUP_README.md
├── database/
├── models/
├── services/
├── ui/
├── data/
├── test_data/
├── reports/
├── docs/
└── tests/
```

## 5. 功能模块说明

| 模块 | 说明 |
|---|---|
| 登录 | 角色选择 + 密码登录 |
| 新建试验 | 填写样品、环境、质量信息并入库 |
| 温度仿真 | 五通道温度：炉温1、炉温2、表面温、中心温、校准温 |
| 状态机 | Idle / Preparing / Ready / Recording / Complete |
| 实时显示 | 温度数值、计时器、状态、系统消息、曲线 |
| 试验记录 | 录入试验后质量和火焰现象 |
| 报告导出 | CSV、Excel、PDF |
| 历史查询 | 从 SQLite 查询试验记录 |
| 设备校准 | 保存当前校准温度和校准历史 |

## 6. 六人分工简介

| 成员 | 模块 |
|---|---|
| A | 数据库与登录 |
| B | 试验流程与状态机 |
| C | 温度仿真与实时曲线 |
| D | 试验记录与报告导出 |
| E | 界面设计与设备校准 |
| F | 历史查询、测试、打包 |

详细分工见 `GROUP_README.md` 和 `docs/`。项目组长由项目负责人兼任，组长同时参与功能实现，不单独占用一个成员分工。

## 7. 测试方式

手动测试文档位于 `tests/`，建议按以下顺序执行：

1. `test_database_manual.md`
2. `test_controller_manual.md`
3. `test_simulator_manual.md`
4. `test_report_manual.md`
5. `final_acceptance_test.md`

## 8. Git 协作规范

小组开发请先阅读 `GIT_GUIDE.md`。建议每个人使用自己的功能分支开发，提交信息按 `feat(A): 增加登录查询接口` 这种中文格式书写，由项目组长统一检查 Pull Request 并合并到 `main`。

## 9. 打包方式

```bash
pyinstaller --noconsole --onefile --name ISO11820_Python main.py
```

打包后程序在 `dist/ISO11820_Python.exe`。

## 10. 后续开发约定

- 数据库操作集中在 `database/db_helper.py`。
- 状态机集中在 `services/test_controller.py`。
- 温度仿真集中在 `services/simulator.py`。
- UI 代码集中在 `ui/`。
- 报告导出集中在 `services/csv_service.py`、`excel_service.py`、`pdf_service.py`。
- TODO 必须标明负责人，例如 `TODO[A]`、`TODO[B]`。
