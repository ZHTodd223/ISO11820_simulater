"""Excel 报告导出服务。"""

from pathlib import Path

from models.sensor_data import SensorData
from models.test_record import TestRecord


def export_excel_report(record: TestRecord, samples: list[SensorData], result: dict) -> Path:
    """导出 Excel 报告。"""
    out_dir = Path("reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{record.testid}_报告.xlsx"

    try:
        from openpyxl import Workbook
        from openpyxl.chart import LineChart, Reference
    except ImportError:
        out_path = out_path.with_suffix(".txt")
        out_path.write_text("未安装 openpyxl，无法生成 Excel。请执行 pip install -r requirements.txt", encoding="utf-8")
        return out_path

    wb = Workbook()
    ws_info = wb.active
    ws_info.title = "试验信息"
    info_rows = [
        ("样品编号", record.productid),
        ("试验编号", record.testid),
        ("操作员", record.operator),
        ("试验前质量(g)", record.preweight),
        ("试验后质量(g)", result["postweight"]),
        ("失重率(%)", round(result["lostweight_per"], 2)),
        ("样品温升(℃)", round(result["deltatf"], 2)),
    ]
    for row in info_rows:
        ws_info.append(row)

    ws_data = wb.create_sheet("温度数据")
    ws_data.append(["Time", "Temp1", "Temp2", "TempSurface", "TempCenter", "TempCalibration"])
    for sample in samples:
        ws_data.append([
            sample.time_seconds,
            sample.tf1,
            sample.tf2,
            sample.ts,
            sample.tc,
            sample.tcal,
        ])

    ws_chart = wb.create_sheet("温度曲线")
    chart = LineChart()
    chart.title = "ISO11820 温度曲线"
    chart.y_axis.title = "温度(℃)"
    chart.x_axis.title = "时间(s)"
    if len(samples) >= 2:
        values = Reference(ws_data, min_col=2, max_col=5, min_row=1, max_row=len(samples) + 1)
        cats = Reference(ws_data, min_col=1, min_row=2, max_row=len(samples) + 1)
        chart.add_data(values, titles_from_data=True)
        chart.set_categories(cats)
        ws_chart.add_chart(chart, "A1")

    wb.save(out_path)
    return out_path

    # TODO[D]: 美化 Excel 样式并补充判定结论。
