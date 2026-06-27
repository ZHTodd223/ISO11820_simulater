"""PDF 报告导出服务。"""

from pathlib import Path

from models.sensor_data import SensorData
from models.test_record import TestRecord
from utils.path_utils import app_base_dir


def export_pdf_report(record: TestRecord, samples: list[SensorData], result: dict) -> Path:
    """导出 PDF 报告。"""
    out_dir = app_base_dir() / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{record.testid}_报告.pdf"

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.utils import ImageReader
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

    conclusion = _judge_iso_conclusion(result)
    rows = [
        f"样品编号：{record.productid}",
        f"试验编号：{record.testid}",
        f"操作员：{record.operator}",
        f"记录时长：{result['totaltesttime']} 秒",
        f"失重率：{result['lostweight_per']:.2f} %",
        f"样品温升：{result['deltatf']:.2f} ℃",
        f"火焰持续时间：{result['flameduration']} 秒",
        f"判定结论：{conclusion}",
    ]
    y = height - 120
    for row in rows:
        c.drawString(72, y, row)
        y -= 28

    c.drawString(72, y - 20, f"温度记录点数：{len(samples)}")

    # ── 嵌入 Matplotlib 温度曲线图片 ──
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import io

        fig, ax = plt.subplots(figsize=(6, 3))
        if samples:
            xs = [s.time_seconds for s in samples]
            ax.plot(xs, [s.tf1 for s in samples], label="TF1")
            ax.plot(xs, [s.tf2 for s in samples], label="TF2")
            ax.plot(xs, [s.ts for s in samples], label="TS")
            ax.plot(xs, [s.tc for s in samples], label="TC")
            ax.legend(loc="upper left")
        ax.set_title("Temperature Curve")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Temperature (℃)")
        ax.set_ylim(0, 800)
        fig.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150)
        plt.close(fig)
        buf.seek(0)

        img_y = y - 220
        image = ImageReader(buf)
        c.drawImage(image, 72, img_y, width=width - 144, height=200, preserveAspectRatio=True)
    except ImportError:
        c.drawString(72, y - 40, "（未安装 Matplotlib，曲线图略）")

    c.save()
    return out_path


def _judge_iso_conclusion(result: dict) -> str:
    """根据 ISO 11820 简化判定规则输出结论。"""
    deltatf = result.get("deltatf", 0)
    lostweight = result.get("lostweight_per", 0)
    flameduration = result.get("flameduration", 0)

    reasons = []
    if deltatf > 30:
        reasons.append(f"温升 {deltatf:.1f}℃ > 30℃")
    if lostweight > 50:
        reasons.append(f"失重率 {lostweight:.1f}% > 50%")
    if flameduration > 0:
        reasons.append(f"火焰持续 {flameduration}s > 0s")

    if not reasons:
        return "合格（A1 级）"
    return f"不合格 — {'、'.join(reasons)}"
