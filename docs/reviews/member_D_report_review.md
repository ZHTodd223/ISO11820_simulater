# 成员 D 分支代码审查说明

审查分支：`origin/dev-D`

审查日期：2026-06-27

结论：暂不合并。当前分支存在误提交文件和 PDF 导出运行时错误，需要修复后再次审查。

## 已执行检查

```bash
git fetch origin main dev-D
git switch -c review/D-report origin/dev-D
python -m py_compile services\csv_service.py services\excel_service.py services\pdf_service.py ui\test_record_window.py services\test_controller.py models\sensor_data.py models\test_record.py
```

编译检查通过。

为了验证真实 Excel/PDF 导出，已在本地临时虚拟环境中安装：

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install openpyxl reportlab matplotlib
```

## 阻塞问题

### 1. 根目录误提交了安装日志文件

文件：`3.8`

该文件内容是 pip 安装 `matplotlib` 的日志，不属于项目源码、文档或测试数据，不应提交到仓库。

示例内容：

```text
Looking in indexes: https://pypi.tuna.tsinghua.edu.cn/simple
Collecting matplotlib
...
Successfully installed ...
```

修复要求：删除根目录文件 `3.8`。

### 2. PDF 导出在真实依赖环境下会崩溃

文件：`services/pdf_service.py`

问题位置：

```python
c.drawImage(buf, 72, img_y, width=width - 144, height=200, preserveAspectRatio=True)
```

`reportlab.canvas.drawImage()` 不能直接接收 `io.BytesIO`，当前代码会抛出：

```text
TypeError: expected str, bytes or os.PathLike object, not BytesIO
```

复现命令：

```bash
.venv\Scripts\python.exe - <<'PY'
from models.test_record import TestRecord
from models.sensor_data import SensorData
from services.pdf_service import export_pdf_report

record = TestRecord(
    productid='DTEST',
    testid='D-REAL-001',
    productname='测试样品',
    specific='spec',
    diameter=50,
    height=50,
    operator='admin',
    preweight=100.0,
)
samples = [
    SensorData(time_seconds=i, tf1=750+i*0.1, tf2=749+i*0.1, ts=100+i, tc=90+i, tcal=750)
    for i in range(5)
]
result = {
    'postweight': 95.0,
    'lostweight': 5.0,
    'lostweight_per': 5.0,
    'totaltesttime': 5,
    'phenocode': 'none',
    'flametime': 0,
    'flameduration': 0,
    'deltatf': 79,
}
print(export_pdf_report(record, samples, result))
PY
```

修复建议：

使用 ReportLab 的 `ImageReader` 包装内存图片：

```python
from reportlab.lib.utils import ImageReader

image = ImageReader(buf)
c.drawImage(image, 72, img_y, width=width - 144, height=200, preserveAspectRatio=True)
```

### 3. Matplotlib 中文字体缺失警告

PDF 曲线生成时出现多条中文 glyph 缺失警告：

```text
UserWarning: Glyph ... missing from font(s) DejaVu Sans
```

这不会立刻导致程序崩溃，但会让 PDF 曲线图中的中文标题或坐标轴显示异常。建议在 Matplotlib 图中设置中文字体，或将曲线图中的标题/坐标轴改为英文。

## 已确认可用的部分

- `csv_service.py` 编译通过，CSV 导出可生成。
- `excel_service.py` 在安装 `openpyxl` 后可以生成 `.xlsx`。
- `test_record_window.py` 的试验现象多选和结论预览方向合理。

## 修复后复测要求

修复后至少执行：

```bash
python -m py_compile services\csv_service.py services\excel_service.py services\pdf_service.py ui\test_record_window.py services\test_controller.py models\sensor_data.py models\test_record.py
.venv\Scripts\python.exe -m pip install openpyxl reportlab matplotlib
```

然后用真实依赖验证：

- CSV 生成 `sensor_data.csv`。
- Excel 生成 `.xlsx`。
- PDF 生成 `.pdf`，且不抛出 `TypeError`。
- 仓库根目录没有 `3.8` 这类误提交日志文件。
