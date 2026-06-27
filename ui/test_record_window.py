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
        self.geometry("480x520")
        self.has_flame = tk.BooleanVar(value=False)
        self.flame_time = tk.StringVar(value="0")
        self.flame_duration = tk.StringVar(value="0")
        self.has_smoke = tk.BooleanVar(value=False)
        self.has_contraction = tk.BooleanVar(value=False)
        self.has_melting = tk.BooleanVar(value=False)
        self.has_discoloration = tk.BooleanVar(value=False)
        self.has_cracking = tk.BooleanVar(value=False)
        self.postweight = tk.StringVar(value="95.0")
        self.memo = tk.StringVar(value="")
        self._build_ui()

    def _build_ui(self) -> None:
        # ── 试验现象多选项 ──
        tk.Label(self, text="试验现象", font=("Microsoft YaHei", 10, "bold")).pack(anchor="w", padx=22, pady=(12, 4))
        row1 = tk.Frame(self)
        row1.pack(anchor="w", padx=22)
        tk.Checkbutton(row1, text="持续火焰", variable=self.has_flame, command=self._update_conclusion).pack(side=tk.LEFT, padx=(0, 8))
        tk.Checkbutton(row1, text="烟雾", variable=self.has_smoke).pack(side=tk.LEFT, padx=(0, 8))
        tk.Checkbutton(row1, text="收缩", variable=self.has_contraction).pack(side=tk.LEFT, padx=(0, 8))
        row2 = tk.Frame(self)
        row2.pack(anchor="w", padx=22, pady=2)
        tk.Checkbutton(row2, text="熔化", variable=self.has_melting).pack(side=tk.LEFT, padx=(0, 8))
        tk.Checkbutton(row2, text="变色", variable=self.has_discoloration).pack(side=tk.LEFT, padx=(0, 8))
        tk.Checkbutton(row2, text="开裂", variable=self.has_cracking).pack(side=tk.LEFT, padx=(0, 8))

        # ── 详细参数 ──
        self._row("火焰发生时刻(s)", self.flame_time)
        self._row("火焰持续时间(s)", self.flame_duration)
        self._row("试验后质量(g)", self.postweight)
        self._row("备注", self.memo)

        # ── ISO 简化判定结论预览 ──
        cf = tk.Frame(self, relief=tk.GROOVE, bd=2, padx=10, pady=6)
        cf.pack(fill=tk.X, padx=22, pady=10)
        tk.Label(cf, text="ISO 简化判定结论：", font=("Microsoft YaHei", 9, "bold")).pack(anchor="w")
        self.conclusion_var = tk.StringVar(value="等待计算...")
        tk.Label(cf, textvariable=self.conclusion_var, fg="blue", font=("Microsoft YaHei", 11, "bold")).pack(anchor="w")

        # ── 按钮 ──
        tk.Button(self, text="保存并导出报告", command=self.save_record, width=20, bg="#4472C4", fg="white").pack(pady=10)

        # 绑定输入变化实时更新结论
        self.postweight.trace_add("write", lambda *_: self._update_conclusion())
        self.flame_duration.trace_add("write", lambda *_: self._update_conclusion())

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

            # 收集附加现象，追加到备注
            pheno_list = []
            if self.has_flame.get():
                pheno_list.append("持续火焰")
            if self.has_smoke.get():
                pheno_list.append("烟雾")
            if self.has_contraction.get():
                pheno_list.append("收缩")
            if self.has_melting.get():
                pheno_list.append("熔化")
            if self.has_discoloration.get():
                pheno_list.append("变色")
            if self.has_cracking.get():
                pheno_list.append("开裂")
            orig_memo = self.memo.get().strip()
            if pheno_list:
                tag = "、".join(pheno_list)
                combined = f"现象[{tag}] {orig_memo}" if orig_memo else f"现象[{tag}]"
            else:
                combined = orig_memo

            result = self.controller.build_result(
                postweight=float(self.postweight.get()),
                has_flame=self.has_flame.get(),
                flame_time=int(self.flame_time.get()),
                flame_duration=int(self.flame_duration.get()),
                memo=combined,
            )
            self.db.update_test_result(record, result)
            csv_path = export_sensor_csv(record, self.controller.record_samples)
            excel_path = export_excel_report(record, self.controller.record_samples, result)
            pdf_path = export_pdf_report(record, self.controller.record_samples, result)

            conclusion = self._judge_iso_conclusion(result)
            messagebox.showinfo("保存成功", f"判定结论：{conclusion}\n\n已生成：\n{csv_path}\n{excel_path}\n{pdf_path}")
            self.on_saved()
            self.destroy()
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc))

    def _update_conclusion(self) -> None:
        """根据已填写的预估数据实时更新 ISO 简化判定结论。"""
        try:
            preweight = self.controller.current_test.preweight if self.controller.current_test else 0
            postweight = float(self.postweight.get()) if self.postweight.get() else 0
            lostweight_per = (preweight - postweight) / preweight * 100 if preweight > 0 else 0
            flame_dur = int(self.flame_duration.get()) if self.has_flame.get() else 0

            reasons = []
            if flame_dur > 0:
                reasons.append(f"火焰持续 {flame_dur}s > 0s")
            if lostweight_per > 50:
                reasons.append(f"失重率 {lostweight_per:.1f}% > 50%")

            if not reasons:
                self.conclusion_var.set("预计合格（A1 级）")
            else:
                self.conclusion_var.set(f"预计不合格 — {'、'.join(reasons)}（温升将在保存后判断）")
        except (ValueError, AttributeError):
            self.conclusion_var.set("等待计算...")

    @staticmethod
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
