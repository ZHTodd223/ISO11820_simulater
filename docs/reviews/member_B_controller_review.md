# 成员 B 分支代码审查说明

审查分支：`origin/feature/B-controller`

审查日期：2026-06-27

结论：暂不合并。当前分支存在运行时崩溃风险，需要修复后再次审查。

## 已执行检查

```bash
git fetch origin main feature/B-controller dev-D
git switch -c review/B-controller origin/feature/B-controller
python -m py_compile main.py database\init_db.py database\db_helper.py services\simulator.py services\test_controller.py ui\main_window.py tests\test_member_A_manual.py
python tests\test_member_A_manual.py
```

编译检查通过。

成员 A 数据库与登录测试通过：`7/7`。

## 阻塞问题

### 1. 标准 60 分钟提前终止检查会调用不存在的方法

文件：`services/test_controller.py`

问题位置：

```python
drift = abs(self.simulator.calc_drift())
```

当前 `main` 分支中的 `services/simulator.py` 没有 `calc_drift()` 方法。B 分支在标准 60 分钟模式下，到达 30 分钟等提前终止检查点时会触发运行时错误。

复现命令：

```bash
python - <<'PY'
from services.test_controller import TestController
from models.test_record import TestRecord

ctl = TestController()
ctl.set_current_test(TestRecord(
    productid='BTEST',
    testid='B-001',
    productname='样品',
    specific='spec',
    diameter=50,
    height=50,
    operator='admin',
    preweight=100,
))
ctl.state = 'Recording'
ctl.duration_mode = 'standard_60min'
ctl.target_duration_seconds = 3600
ctl.record_seconds = 1799
ctl.tick()
PY
```

实际结果：

```text
AttributeError: 'SensorSimulator' object has no attribute 'calc_drift'
```

## 修复建议

任选一种方式修复：

1. 在 B 分支中补齐不依赖成员 C 的 `calc_drift()` 兜底实现。
2. 将提前终止检查改为安全调用，例如：

```python
if not hasattr(self.simulator, "calc_drift"):
    return
```

3. 等成员 C 的仿真模块先合并后，B 分支再基于最新 `main` 重新整理并提交。

如果采用第 2 种方式，建议同时写系统消息说明“温漂计算接口暂不可用，跳过提前终止检查”，避免静默跳过。

## 额外提醒

B 分支新增了：

- 未保存试验保护。
- 多时长模式。
- Ready 温度回退到 Preparing。
- 按钮状态集中到 `get_button_states()`。

这些方向是对的，但需要保证它们不依赖未合并模块，否则不能进入 `main`。

## 修复后复测要求

修复后至少执行：

```bash
python -m py_compile main.py database\init_db.py database\db_helper.py services\simulator.py services\test_controller.py ui\main_window.py tests\test_member_A_manual.py
python tests\test_member_A_manual.py
```

还需要补充一段 B 模块状态机测试，覆盖：

- Idle -> Preparing -> Ready -> Recording -> Complete。
- 手动停止记录。
- 固定时长自动停止。
- 标准模式 30 分钟检查点不崩溃。
- 保存前禁止新建试验。
