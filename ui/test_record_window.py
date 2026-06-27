"""试验现象记录窗口。"""

import tkinter as tk
from tkinter import messagebox

from database.db_helper import DbHelper
from services.csv_service import export_sensor_csv
from services.excel_service import export_excel_report
from services.pdf_service import export_pdf_report
from services.test_controller import TestController


class TestRecordWindow(tk.Toplevel):
    """保存试验后质量、火焰现象并导出报告。"""

    def __init__(self, master: tk.Toplevel, controller: TestController, on_saved) -> None:
        super().__init__(master)
        self.controller = controller
        self.on_saved = on_saved
        self.db = DbHelper()
        self.title("试验记录")
        self.geometry("420x360")
        self.has_flame = tk.BooleanVar(value=False)
        self.postweight = tk.StringVar(value="95.0")
        self.flame_time = tk.StringVar(value="0")
        self.flame_duration = tk.StringVar(value="0")
        self.memo = tk.StringVar(value="")
        self._build_ui()

    def _build_ui(self) -> None:
        tk.Checkbutton(self, text="是否出现持续火焰", variable=self.has_flame).pack(anchor="w", padx=22, pady=10)
        self._row("火焰发生时刻(s)", self.flame_time)
        self._row("火焰持续时间(s)", self.flame_duration)
        self._row("试验后质量(g)", self.postweight)
        self._row("备注", self.memo)
        tk.Button(self, text="保存并导出报告", command=self.save_record, width=20).pack(pady=18)

    def _row(self, label: str, var: tk.StringVar) -> None:
        frame = tk.Frame(self)
        frame.pack(fill=tk.X, padx=18, pady=6)
        tk.Label(frame, text=label, width=16, anchor="e").pack(side=tk.LEFT)
        tk.Entry(frame, textvariable=var, width=24).pack(side=tk.LEFT)

    def save_record(self) -> None:
        try:
            record = self.controller.current_test
            if not record:
                raise ValueError("当前没有试验")
            result = self.controller.build_result(
                postweight=float(self.postweight.get()),
                has_flame=self.has_flame.get(),
                flame_time=int(self.flame_time.get()),
                flame_duration=int(self.flame_duration.get()),
                memo=self.memo.get(),
            )
            self.db.update_test_result(record, result)
            csv_path = export_sensor_csv(record, self.controller.record_samples)
            excel_path = export_excel_report(record, self.controller.record_samples, result)
            pdf_path = export_pdf_report(record, self.controller.record_samples, result)
            messagebox.showinfo("保存成功", f"已生成：\n{csv_path}\n{excel_path}\n{pdf_path}")
            self.on_saved()
            self.destroy()
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc))

    # TODO[D]: 增加试验现象多选项和 ISO 简化判定结论展示。
