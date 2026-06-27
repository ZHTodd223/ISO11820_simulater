# 成员 C 分支代码审查说明

审查分支：`origin/feat/member-C-simulator`

审查日期：2026-06-27

结论：暂不合并。仿真器底层功能方向正确，但 `ui/main_window.py` 回退了成员 A 和成员 B 已合并到 `main` 的功能，需要重新整理后再审查。

## 已执行检查

```bash
git fetch --all --prune
git switch -c review/C-simulator origin/feat/member-C-simulator
python -m py_compile main.py database\init_db.py database\db_helper.py models\sensor_data.py services\simulator.py services\test_controller.py ui\login_window.py ui\main_window.py ui\new_test_window.py ui\operator_manage_window.py tests\test_member_A_manual.py
python tests\test_member_A_manual.py
```

编译检查通过。

成员 A 数据库与登录测试通过：`7/7`。

另外执行了仿真器与 B 状态机的简单冒烟测试，`calc_drift()` 和固定时长记录流程可运行。

## 阻塞问题

### 1. 主窗口删除了管理员账号管理入口

文件：`ui/main_window.py`

当前 `main` 中已有成员 A 的管理员账号管理入口：

```python
from ui.operator_manage_window import OperatorManageWindow

if self.user.get("usertype") == "admin":
    self.btn_manage = tk.Button(top, text="账号管理", command=self._open_operator_manage)
    self.btn_manage.pack(side=tk.LEFT, padx=4)
```

C 分支删除了该 import、按钮和 `_open_operator_manage()` 方法。这样会导致成员 A 已合并的账号管理功能从 UI 上消失。

### 2. 主窗口回退了历史查询筛选 UI

文件：`ui/main_window.py`

当前 `main` 已支持：

- 按样品/试验编号查询。
- 按操作员查询。
- 按开始日期、结束日期查询。
- 重置筛选条件。

C 分支把历史查询 UI 退回为只按关键字查询，并删除了：

```python
history_operator_var
history_operator_combo
date_from_var
date_to_var
_load_operator_list()
_reset_history_filters()
```

这会回退成员 A 的历史查询功能。

### 3. 主窗口回退了 B 的按钮状态集中控制和未保存保护

文件：`ui/main_window.py`

当前 `main` 已合并成员 B 的：

```python
states = self.controller.get_button_states()
```

以及：

```python
if self.controller.needs_save:
    messagebox.showwarning(...)
    return
```

保存后也应调用：

```python
self.controller.mark_saved()
```

C 分支把这些改回了旧逻辑：

```python
state = self.controller.state
...
self.controller.stop_heating()
```

这会破坏成员 B 的未保存试验保护、保存后保温流转和按钮状态集中管理。

## 可以保留的改动

以下改动方向是正确的，建议保留并重新合并到最新 `main`：

- `models/sensor_data.py`
  - 新增 `SensorData.is_anomalous()`。
  - 新增 `SensorHistory`。
- `services/simulator.py`
  - 从 `config.json` 读取仿真参数。
  - 新增温漂历史与 `calc_drift()`。
  - 新增异常模式测试。
  - 稳定判定从简单计数升级为窗口数据判断。
- `ui/main_window.py`
  - 新增温漂显示。
  - 新增异常测试下拉。
  - 曲线 X 轴改为真实秒数并滚动显示最近 10 分钟。

但修改 `ui/main_window.py` 时必须基于当前 `main`，保留成员 A、B 的 UI 逻辑。

## 修复建议

建议成员 C 重新从最新 `main` 分支创建或整理分支：

```bash
git checkout main
git pull
git checkout feat/member-C-simulator
git merge main
```

处理冲突时不要用旧版 `main_window.py` 整体覆盖。只把 C 负责的温漂显示、异常测试、曲线滚动逻辑合进去，保留：

- `OperatorManageWindow` 账号管理入口。
- 历史查询日期/操作员筛选。
- `controller.get_button_states()`。
- `controller.needs_save` 新建试验保护。
- `controller.mark_saved()` 保存后保温流转。

## 修复后复测要求

修复后至少执行：

```bash
python -m py_compile main.py database\init_db.py database\db_helper.py models\sensor_data.py services\simulator.py services\test_controller.py ui\login_window.py ui\main_window.py ui\new_test_window.py ui\operator_manage_window.py tests\test_member_A_manual.py
python tests\test_member_A_manual.py
```

还需要补充 C 模块冒烟测试：

- `SensorSimulator` 能从 `config.json` 读取参数。
- `calc_drift()` 可调用且返回数字。
- 升温后能进入 Ready。
- 异常模式 `sensor_failure` 能让 `SensorData.is_anomalous()` 返回 `True`。
- 主窗口仍保留账号管理、历史筛选、B 的按钮状态逻辑。
