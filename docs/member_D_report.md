# 成员 D：试验记录与报告导出模块

## 负责模块

试验现象记录、结果计算、CSV/Excel/PDF 导出。

## 主要文件

| 文件 | 说明 |
|---|---|
| `ui/test_record_window.py` | 试验记录窗口 |
| `services/csv_service.py` | CSV 导出 |
| `services/excel_service.py` | Excel 导出 |
| `services/pdf_service.py` | PDF 导出 |
| `services/test_controller.py` | `build_result()` 计算结果 |

## 需要实现的功能

- 录入试验后质量。
- 录入火焰发生时刻和持续时间。
- 计算失重量、失重率、温升。
- 保存结果到 `testmaster`。
- 导出温度 CSV。
- 导出 Excel 报告。
- 导出 PDF 报告。

## 与其他成员的接口

| 成员 | 接口 |
|---|---|
| A | 调用 `DbHelper.update_test_result()` |
| B | 读取当前状态和记录样本 |
| C | 使用温度样本生成曲线和数据表 |
| F | 配合历史查询导出和最终打包测试 |

## 测试方法

完成一次记录后打开试验记录窗口，填写试验后质量并保存，检查 `test_data/` 和 `reports/`。

## 最终交付物

CSV、Excel、PDF 文件能生成，数据库结果能更新。

## TODO 清单

- [x] TODO[D]: PDF 中嵌入温度曲线图片。
- [x] TODO[D]: Excel 样式美化。
- [x] TODO[D]: 增加判定结论。
- [x] TODO[D]: 增加导出失败提示。
