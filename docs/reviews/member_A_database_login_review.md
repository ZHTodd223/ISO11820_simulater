# 成员 A 分支代码审查说明

审查分支：`origin/feat/member-A-database-login`

审查日期：2026-06-26

结论：暂不合并。当前分支存在会影响测试可运行性和账号权限边界的问题，需要修复后再次提交审查。

## 已执行检查

```bash
git fetch origin main feat/member-A-database-login
git switch -c review/member-A-database-login origin/feat/member-A-database-login
python -m py_compile main.py database\init_db.py database\db_helper.py ui\login_window.py ui\main_window.py ui\new_test_window.py ui\operator_manage_window.py tests\test_member_A_manual.py
python tests\test_member_A_manual.py
```

编译检查通过。

成员 A 测试脚本结果：7 项中 1 项通过，6 项失败。

主要失败信息：

```text
ModuleNotFoundError: No module named 'database'
```

## 必须修复的问题

### 1. 测试脚本无法直接运行

文件：`tests/test_member_A_manual.py`

问题位置：

```python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
```

这里加入的是 `tests` 目录，不是项目根目录。直接执行：

```bash
python tests\test_member_A_manual.py
```

会导致 `from database.db_helper import DbHelper` 等导入失败。

建议修复：

```python
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
```

修复后需要保证测试脚本能在项目根目录直接运行。

### 2. 账号管理入口没有权限保护

文件：`ui/login_window.py`

问题位置：

```python
tk.Button(self, text="账号管理", width=16, command=self._open_operator_manage).pack(pady=4)
```

当前账号管理按钮显示在登录窗口，任何未登录用户都可以打开 `OperatorManageWindow`，并执行新增、删除、修改密码等操作。这会绕过“管理员登录后才能管理账号”的权限边界。

建议修复方式任选其一：

- 移除登录窗口上的“账号管理”按钮，把账号管理入口放到主窗口，并且仅 `usertype == "admin"` 时显示或启用。
- 或者打开账号管理前先要求管理员密码验证。

课程项目可以简单处理，但不能让未登录用户直接维护账号。

### 3. 新增账号无法通过当前登录窗口登录

文件：`ui/login_window.py`

当前登录窗口仍然只有两个固定角色：

```python
管理员 -> admin
试验员 -> experimenter
```

成员 A 新增了 `add_operator()` 和账号管理窗口，但新增的用户名没有入口可以登录。比如新增 `test_user` 后，登录窗口没有用户名输入框，也没有动态操作员选择框，因此新账号无法实际使用。

建议二选一：

- 保持课程原始要求：只支持 `admin` 和 `experimenter` 两个固定登录账号，则删除或暂缓账号管理窗口。
- 扩展登录逻辑：增加用户名输入框或操作员下拉框，让数据库中的账号都可以登录。

两种方案必须选一种，不要出现“能新增账号但不能登录”的半成品状态。

### 4. 测试脚本中 DB-004 的试验员登录检查不可达

文件：`tests/test_member_A_manual.py`

问题位置：

```python
if user is None:
    print(...)
    return True
...
# 也测 experimenter 登录
user2 = db.login("experimenter", "123456")
```

当错误密码测试成功时函数已经 `return True`，后面的 `experimenter` 登录检查不会执行。

建议修复：

- 把 `experimenter` 登录测试拆成单独测试函数。
- 或者先保存错误密码检查结果，最后统一 `return wrong_password_ok and experimenter_ok`。

## 可以保留的改动

- `DbHelper.query_tests()` 增加 `date_from`、`date_to`、`operator` 参数，方向正确。
- `check_test_exists()` 用于给重复试验更清晰提示，方向正确。
- 操作员增删改方法本身基本可用，但需要和登录权限设计保持一致。
- 历史查询 Tab 增加筛选条件，符合成员 A 和成员 F 的接口需求。

## 修复后复测要求

修复后至少执行：

```bash
python -m py_compile main.py database\init_db.py database\db_helper.py ui\login_window.py ui\main_window.py ui\new_test_window.py ui\operator_manage_window.py tests\test_member_A_manual.py
python tests\test_member_A_manual.py
python main.py
```

验收标准：

- 成员 A 测试脚本全部通过。
- 未登录用户不能直接管理账号。
- 如果保留账号管理功能，新增账号必须能通过 UI 登录；如果不保留，则删除相关入口和窗口。
- 原有 `admin / 123456`、`experimenter / 123456` 登录流程不被破坏。
