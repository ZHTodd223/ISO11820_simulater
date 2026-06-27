# Git 协作规范

这份规范用于 6 人课程小组协作，目标是让每个人都能安全提交自己的模块，减少冲突，方便项目组长合并和答辩前回滚。

## 1. 第一次拉取项目

```bash
git clone https://github.com/ZHTodd223/ISO11820_simulater.git
cd ISO11820_simulater
```

安装依赖并启动：

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## 2. 分支命名规范

不要直接在 `main` 分支上开发。每个人从 `main` 新建自己的功能分支。

| 成员 | 分支示例 | 负责内容 |
|---|---|---|
| A | `feature/A-database-login` | 数据库与登录 |
| B | `feature/B-controller` | 状态机与流程 |
| C | `feature/C-simulator-chart` | 仿真与曲线 |
| D | `feature/D-report-export` | 试验记录与报告 |
| E | `feature/E-ui-calibration` | UI 与校准 |
| F | `feature/F-history-test-package` | 历史查询、测试、打包 |

创建分支：

```bash
git checkout main
git pull
git checkout -b feature/A-database-login
```

## 3. 提交前必须做的事

提交前先查看改了什么：

```bash
git status
git diff
```

至少运行一次基础检查：

```bash
python -m py_compile main.py database\*.py models\*.py services\*.py ui\*.py
```

如果改了界面或流程，还要手动运行：

```bash
python main.py
```

## 4. Commit 信息规范

提交信息建议使用下面格式：

```text
类型(成员): 中文简短说明
```

要求：

- 冒号后面的说明必须写中文。
- 说明用一句话写清楚“做了什么”。
- 不要只写 `修改`、`更新`、`修复bug` 这种太模糊的内容。
- 建议一次 commit 只做一类事情，方便项目组长审查。

常用类型：

| 类型 | 含义 | 示例 |
|---|---|---|
| `feat` | 新功能 | `feat(A): 增加历史记录查询接口` |
| `fix` | 修复问题 | `fix(B): 禁止未就绪时开始记录` |
| `docs` | 文档 | `docs(F): 更新最终验收测试清单` |
| `style` | 样式或格式 | `style(E): 调整主界面按钮间距` |
| `test` | 测试 | `test(F): 补充报告导出手动测试用例` |
| `refactor` | 重构 | `refactor(C): 拆分温度漂移计算函数` |
| `chore` | 杂项 | `chore(F): 更新忽略文件配置` |

示例：

```bash
git add services/test_controller.py
git commit -m "feat(B): 增加固定时长记录模式"
```

更多中文 commit 示例：

```bash
git commit -m "fix(A): 修复重复初始化默认账号的问题"
git commit -m "feat(C): 增加校准温度实时显示"
git commit -m "docs(F): 补充分支合并说明"
git commit -m "test(D): 增加报告导出检查表"
```

## 5. 推送自己的分支

```bash
git push -u origin feature/A-database-login
```

之后在 GitHub 上创建 Pull Request，由项目组长负责检查和合并。

## 6. Pull Request 要求

每个 PR 至少写清楚：

- 改了哪些文件。
- 完成了哪个 TODO。
- 怎么测试的。
- 是否影响其他成员接口。

PR 描述模板：

```text
## 修改内容
- 

## 对应 TODO
- TODO[A]:

## 测试结果
- [ ] python -m py_compile 通过
- [ ] python main.py 能启动
- [ ] 相关手动测试已完成

## 需要项目组长注意
- 
```

## 7. 合并前同步 main

开发期间如果别人已经合并了代码，先同步 `main`：

```bash
git checkout main
git pull
git checkout feature/A-database-login
git merge main
```

如果出现冲突，先不要乱删代码，找项目组长一起处理。

## 8. 文件归属建议

| 文件或目录 | 主要负责人 |
|---|---|
| `database/` | A |
| `models/` | A、C、D |
| `services/test_controller.py` | B |
| `services/simulator.py` | C |
| `services/*_service.py` | D、E |
| `ui/` | E，相关模块成员配合 |
| `README.md`、`GROUP_README.md` | 项目组长 |
| `tests/`、历史查询相关代码、打包说明 | F |

修改别人负责的核心文件前，先在群里说一声。

## 9. 不要提交的内容

这些内容已经在 `.gitignore` 中忽略：

- `.venv/`
- `__pycache__/`
- `data/*.db`
- `reports/` 下生成的报告
- `test_data/` 下生成的 CSV
- `dist/` 和 `build/`

如果误提交了运行生成文件，先联系项目组长处理。

## 10. 推荐协作流程

1. 每天开始前：`git checkout main`，然后 `git pull`。
2. 新功能：新建自己的 `feature/...` 分支。
3. 小步提交：完成一个小功能就 commit。
4. 推送分支：`git push`。
5. 创建 PR：写清楚修改内容和测试结果。
6. 项目组长合并到 `main`。
7. 演示前：所有人只使用最新 `main` 测试。

## 11. 常用命令速查

```bash
git status
git add .
git commit -m "feat(A): 增加数据库查询接口"
git pull
git push
git branch
git checkout main
git checkout -b feature/A-database-login
```

## 12. 项目组长的合并检查清单

- PR 是否只改了相关模块。
- 是否有运行生成文件被提交。
- 是否更新了相关 README 或测试文档。
- 是否通过 `python -m py_compile`。
- 是否能运行 `python main.py`。
- 是否破坏其他成员接口。
- 是否完成对应手动测试表。
