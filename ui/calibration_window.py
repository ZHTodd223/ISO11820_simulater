"""设备校准窗口。"""

import tkinter as tk
from tkinter import messagebox, ttk

from services.calibration_service import (
    STANDARD_TEMP_POINTS,
    DEFAULT_TOLERANCE,
    CalibrationService,
)


class CalibrationWindow(tk.Toplevel):
    """设备校准窗口：支持单点快速校准和多点校准。"""

    def __init__(self, master: tk.Toplevel, operator: str, get_tcal, on_saved) -> None:
        super().__init__(master)
        self.operator = operator
        self.get_tcal = get_tcal
        self.on_saved = on_saved
        self.service = CalibrationService()
        self.remarks = tk.StringVar(value="课堂演示校准")
        self.temp_var = tk.StringVar(value="")
        self.title("设备校准")
        self.geometry("520x540")
        self.resizable(False, False)

        # 多点校准的输入变量
        self.point_vars: dict[int, tk.StringVar] = {
            tp: tk.StringVar(value="") for tp in STANDARD_TEMP_POINTS
        }
        self.tolerance_var = tk.StringVar(value=str(DEFAULT_TOLERANCE))

        self._build_ui()
        self._refresh_temp()

    def _build_ui(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ── Tab 1: 单点快速校准 ──
        tab_single = tk.Frame(notebook)
        notebook.add(tab_single, text="快速校准")
        self._build_single_tab(tab_single)

        # ── Tab 2: 多点校准 ──
        tab_multi = tk.Frame(notebook)
        notebook.add(tab_multi, text="多点校准")
        self._build_multi_tab(tab_multi)

    def _build_single_tab(self, parent: tk.Frame) -> None:
        """单点快速校准 Tab。"""
        header = tk.Label(parent, text="单点校准 — 校准温度来自第 5 通道",
                          font=("Microsoft YaHei", 10, "bold"), fg="#1565C0")
        header.pack(pady=(14, 8))

        tk.Label(parent, textvariable=self.temp_var,
                 font=("Consolas", 20), fg="#333333").pack(pady=10)

        remark_frame = tk.Frame(parent)
        remark_frame.pack(pady=8)
        tk.Label(remark_frame, text="备注：", font=("Microsoft YaHei", 10)).pack(side=tk.LEFT)
        tk.Entry(remark_frame, textvariable=self.remarks, width=24,
                 font=("Microsoft YaHei", 10)).pack(side=tk.LEFT)

        tk.Button(parent, text="保存校准记录", command=self.save_single,
                  width=18, bg="#4CAF50", fg="white",
                  font=("Microsoft YaHei", 10, "bold")).pack(pady=14)

    def _build_multi_tab(self, parent: tk.Frame) -> None:
        """多点校准 Tab。"""
        header = tk.Label(parent, text="多点校准 — 输入各标准温度点的实测值",
                          font=("Microsoft YaHei", 10, "bold"), fg="#1565C0")
        header.pack(pady=(14, 8))

        # 当前参考温度
        cur_frame = tk.Frame(parent)
        cur_frame.pack(fill=tk.X, padx=14, pady=4)
        tk.Label(cur_frame, text="当前通道温度：").pack(side=tk.LEFT)
        tk.Label(cur_frame, textvariable=self.temp_var,
                 font=("Consolas", 11), fg="#555555").pack(side=tk.LEFT)

        # 允差设置
        tol_frame = tk.Frame(parent)
        tol_frame.pack(fill=tk.X, padx=14, pady=4)
        tk.Label(tol_frame, text="允许偏差 (±℃)：").pack(side=tk.LEFT)
        tk.Entry(tol_frame, textvariable=self.tolerance_var, width=8).pack(side=tk.LEFT, padx=6)

        # 标准温度点输入表格
        table_frame = tk.Frame(parent)
        table_frame.pack(fill=tk.X, padx=14, pady=8)

        tk.Label(table_frame, text="标准温度 (℃)", width=16, anchor="center",
                 font=("Microsoft YaHei", 10, "bold"), bg="#E3F2FD").grid(row=0, column=0, pady=2)
        tk.Label(table_frame, text="实测温度 (℃)", width=16, anchor="center",
                 font=("Microsoft YaHei", 10, "bold"), bg="#E3F2FD").grid(row=0, column=1, pady=2)

        for i, tp in enumerate(STANDARD_TEMP_POINTS, start=1):
            tk.Label(table_frame, text=str(tp), width=10, anchor="center",
                     font=("Consolas", 11)).grid(row=i, column=0, pady=3)
            tk.Entry(table_frame, textvariable=self.point_vars[tp], width=14,
                     font=("Consolas", 11), justify="center").grid(row=i, column=1, pady=3, padx=4)

        # 填充当前温度按钮
        tk.Button(parent, text="将当前温度填入所有空白格", command=self._fill_current_temp,
                  font=("Microsoft YaHei", 9)).pack(pady=4)

        # 备注
        remark_frame = tk.Frame(parent)
        remark_frame.pack(pady=4)
        tk.Label(remark_frame, text="备注：").pack(side=tk.LEFT)
        self.multi_remarks = tk.StringVar(value="多点校准")
        tk.Entry(remark_frame, textvariable=self.multi_remarks, width=30).pack(side=tk.LEFT)

        # 保存按钮
        tk.Button(parent, text="保存并判定校准结果", command=self.save_multi,
                  width=22, bg="#FF9800", fg="white",
                  font=("Microsoft YaHei", 10, "bold")).pack(pady=10)

        # 结果显示
        self.multi_result_label = tk.Label(parent, text="", font=("Microsoft YaHei", 10),
                                           wraplength=460, justify="left")
        self.multi_result_label.pack(pady=6)

    def _fill_current_temp(self) -> None:
        """将当前通道温度填入所有空白的多点输入框。"""
        current = self.get_tcal()
        for tp, var in self.point_vars.items():
            if not var.get().strip():
                # 根据标准温度点偏移生成合理值
                var.set(f"{current + (tp - 750) * 0.05:.1f}")

    def _refresh_temp(self) -> None:
        self.temp_var.set(f"{self.get_tcal():.1f} ℃")
        self.after(1000, self._refresh_temp)

    def save_single(self) -> None:
        """保存单点快速校准记录。"""
        try:
            self.service.save_current_temperature(
                self.operator, self.get_tcal(), self.remarks.get()
            )
            messagebox.showinfo("保存成功", "单点校准记录已保存")
            self.on_saved()
            self.destroy()
        except Exception as exc:
            messagebox.showerror("保存失败", f"校准记录保存失败：{exc}")

    def save_multi(self) -> None:
        """保存多点校准记录并显示判定结果。"""
        try:
            # 解析允差
            tol_raw = self.tolerance_var.get().strip()
            if not tol_raw:
                raise ValueError("请输入允许偏差")
            tolerance = float(tol_raw)
            if tolerance <= 0 or tolerance > 100:
                raise ValueError("允许偏差应在 0～100 ℃ 之间")

            # 收集读数
            readings: dict[int, float] = {}
            empty_points = []
            for tp in STANDARD_TEMP_POINTS:
                raw = self.point_vars[tp].get().strip()
                if raw:
                    try:
                        readings[tp] = float(raw)
                    except ValueError:
                        raise ValueError(f"标准温度 {tp}℃ 的实测值「{raw}」不是有效数字")
                else:
                    empty_points.append(tp)

            if not readings:
                raise ValueError("请至少填写一个标准温度点的实测值")

            if empty_points:
                msg = f"以下标准温度点未填写，将跳过：{empty_points}"
            else:
                msg = ""

            # 保存并判定
            result = self.service.save_multi_point_calibration(
                operator=self.operator,
                readings=readings,
                remarks=self.multi_remarks.get(),
                tolerance=tolerance,
            )

            # 构建结果展示
            lines = []
            if msg:
                lines.append(f"⚠ {msg}")
            lines.append(f"允差：±{tolerance}℃")
            lines.append("─" * 30)
            for tp in STANDARD_TEMP_POINTS:
                if tp in result["detail"]:
                    d = result["detail"][tp]
                    status = "✓ 合格" if d["ok"] else "✗ 不合格"
                    lines.append(f"  {tp}℃ → 实测 {d['actual']}℃ 偏差 {d['deviation']:+.1f}℃  {status}")
                else:
                    lines.append(f"  {tp}℃ → 未填写  —")
            lines.append("─" * 30)
            if result["passed"]:
                lines.append("✅ 校准结果：全部合格")
            else:
                lines.append(f"❌ 校准结果：不合格 — 不合格点：{result['failed_points']}℃")

            self.multi_result_label.config(text="\n".join(lines), fg="#2E7D32" if result["passed"] else "#C62828")
            self.on_saved()
            messagebox.showinfo("多点校准已保存", "多点校准记录已保存至数据库")

        except ValueError as exc:
            messagebox.showerror("输入有误", str(exc))
        except Exception as exc:
            messagebox.showerror("保存失败", f"校准记录保存失败：{exc}")


class CalibrationHistoryWindow(tk.Toplevel):
    """校准历史详情窗口。"""

    def __init__(self, master: tk.Widget, service: CalibrationService) -> None:
        super().__init__(master)
        self.service = service
        self.title("校准历史记录")
        self.geometry("680x520")
        self.resizable(True, True)
        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        top = tk.Frame(self)
        top.pack(fill=tk.X, padx=12, pady=8)

        tk.Label(top, text="校准历史记录", font=("Microsoft YaHei", 13, "bold"),
                 fg="#1565C0").pack(side=tk.LEFT)
        tk.Button(top, text="刷新", command=self._refresh,
                  width=8, bg="#2196F3", fg="white").pack(side=tk.RIGHT, padx=4)

        # 列表
        columns = ("CalibrationDate", "Operator", "TemperatureData", "PassedCriteria", "Remarks")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=12)
        col_labels = {
            "CalibrationDate": "校准时间", "Operator": "操作员",
            "TemperatureData": "温度数据", "PassedCriteria": "判定",
            "Remarks": "备注",
        }
        col_widths = {"CalibrationDate": 160, "Operator": 100, "TemperatureData": 160,
                      "PassedCriteria": 60, "Remarks": 160}
        for col in columns:
            self.tree.heading(col, text=col_labels.get(col, col))
            self.tree.column(col, width=col_widths.get(col, 120), anchor="center" if col == "PassedCriteria" else "w")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 8))

        # 明细区域
        detail_frame = tk.LabelFrame(self, text="选中记录详情", padx=10, pady=8)
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        self.detail_text = tk.Text(detail_frame, height=8, font=("Consolas", 10), wrap=tk.WORD)
        self.detail_text.pack(fill=tk.BOTH, expand=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # 底部按钮
        bottom = tk.Frame(self)
        bottom.pack(fill=tk.X, padx=12, pady=(0, 10))
        tk.Button(bottom, text="关闭", command=self.destroy, width=12).pack(side=tk.RIGHT)

    def _refresh(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            records = self.service.list_records()
            for row in records:
                passed = row.get("PassedCriteria", 1)
                pass_text = "合格" if passed == 1 else "不合格"
                temp_data = row.get("TemperatureData", "")
                # 截断过长字符串做显示
                display_data = temp_data if len(temp_data) <= 50 else temp_data[:47] + "..."
                self.tree.insert("", tk.END, values=(
                    row.get("CalibrationDate", ""),
                    row.get("Operator", ""),
                    display_data,
                    pass_text,
                    row.get("Remarks", ""),
                ))
        except Exception as exc:
            messagebox.showerror("查询失败", f"获取校准记录失败：{exc}")

    def _on_select(self, event) -> None:
        selection = self.tree.selection()
        self.detail_text.delete("1.0", tk.END)
        if not selection:
            return
        values = self.tree.item(selection[0], "values")
        if not values:
            return

        # 从数据库获取完整记录
        cal_date = values[0]
        operator = values[1]
        record = self.service.get_record_detail(cal_date, operator)
        if not record:
            self.detail_text.insert("1.0", "无法获取记录详情")
            return

        # 格式化显示
        lines = []
        lines.append(f"校准时间：{record.get('CalibrationDate', '')}")
        lines.append(f"操作员：{record.get('Operator', '')}")
        lines.append(f"判定结果：{'合格' if record.get('PassedCriteria', 1) == 1 else '不合格'}")
        lines.append(f"备注：{record.get('Remarks', '')}")
        lines.append("")

        temp_data_str = record.get("TemperatureData", "")
        try:
            temp_data = __import__("json").loads(temp_data_str)
            if temp_data.get("type") == "multi_point":
                lines.append("── 多点校准明细 ──")
                lines.append(f"允许偏差：±{temp_data.get('tolerance', 'N/A')}℃")
                lines.append("")
                detail = temp_data.get("detail", {})
                for tp_str, info in sorted(detail.items(), key=lambda x: int(x[0])):
                    status = "✓ 合格" if info["ok"] else "✗ 不合格"
                    lines.append(
                        f"  {info['expected']:>4}℃ → 实测 {info['actual']:>6.1f}℃  "
                        f"偏差 {info['deviation']:>+6.1f}℃  {status}"
                    )
            else:
                tcal = temp_data.get("tcal", "N/A")
                lines.append(f"单点校准温度：{tcal}℃")
        except (ValueError, KeyError, TypeError):
            lines.append(f"原始数据：{temp_data_str}")

        self.detail_text.insert("1.0", "\n".join(lines))
