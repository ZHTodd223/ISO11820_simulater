"""PDF 报告导出服务。"""

from pathlib import Path

from models.sensor_data import SensorData
from models.test_record import TestRecord


def export_pdf_report(record: TestRecord, samples: list[SensorData], result: dict) -> Path:
    """导出 PDF 报告。"""
    out_dir = Path("reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{record.testid}_报告.pdf"

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfgen import canvas
    except ImportError:
        out_path = out_path.with_suffix(".txt")
        out_path.write_text("未安装 ReportLab，无法生成 PDF。请执行 pip install -r requirements.txt", encoding="utf-8")
        return out_path

    c = canvas.Canvas(str(out_path), pagesize=A4)
    width, height = A4
    font_name = "Helvetica"
    font_path = Path("C:/Windows/Fonts/simhei.ttf")
    if font_path.exists():
        pdfmetrics.registerFont(TTFont("SimHei", str(font_path)))
        font_name = "SimHei"

    c.setFont(font_name, 16)
    c.drawString(72, height - 72, "ISO 11820 建筑材料不燃性试验报告")
    c.setFont(font_name, 11)
    rows = [
        f"样品编号：{record.productid}",
        f"试验编号：{record.testid}",
        f"操作员：{record.operator}",
        f"记录时长：{result['totaltesttime']} 秒",
        f"失重率：{result['lostweight_per']:.2f} %",
        f"样品温升：{result['deltatf']:.2f} ℃",
        f"火焰持续时间：{result['flameduration']} 秒",
        "判定结论：课程演示版，按温升、失重率、火焰持续时间综合判断。",
    ]
    y = height - 120
    for row in rows:
        c.drawString(72, y, row)
        y -= 28

    c.drawString(72, y - 20, f"温度记录点数：{len(samples)}")
    c.save()
    return out_path

    # TODO[D]: 将 Matplotlib 曲线图片嵌入 PDF。
