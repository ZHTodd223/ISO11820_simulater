"""新建试验窗口。"""

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from database.db_helper import DbHelper
from models.test_record import TestRecord
from services.test_controller import TestController


class NewTestWindow(tk.Toplevel):
    """填写样品信息并创建试验。"""

    def __init__(self, master: tk.Toplevel, controller: TestController, operator: str) -> None:
        super().__init__(master)
        self.controller = controller
        self.operator = operator
        self.db = DbHelper()
        self.title("新建试验")
        self.geometry("460x520")
        self.resizable(False, False)
        self.vars = {
            "productid": tk.StringVar(value=datetime.now().strftime("P%Y%m%d%H%M")),
            "testid": tk.StringVar(value=datetime.now().strftime("%Y%m%d-%H%M%S")),
            "productname": tk.StringVar(value="岩棉隔热板"),
            "specific": tk.StringVar(value="100x50x25mm"),
            "diameter": tk.StringVar(value="50"),
            "height": tk.StringVar(value="50"),
            "preweight": tk.StringVar(value="100.0"),
            "ambtemp": tk.StringVar(value="25.0"),
            "ambhumi": tk.StringVar(value="50.0"),
        }
        # 时长模式：standard_60min / fixed / manual
        self.duration_mode = tk.StringVar(value="standard_60min")
        self.custom_minutes = tk.StringVar(value="30")
        self._build_ui()

    def _build_ui(self) -> None:
        form = tk.Frame(self)
        form.pack(padx=18, pady=(18, 8), fill=tk.BOTH)

        labels = [
            ("样品编号", "productid"),
            ("试验编号", "testid"),
            ("样品名称", "productname"),
            ("规格型号", "specific"),
            ("直径 (mm)", "diameter"),
            ("高度 (mm)", "height"),
            ("试验前质量 (g)", "preweight"),
            ("环境温度 (℃)", "ambtemp"),
            ("环境湿度 (%)", "ambhumi"),
        ]
        for row, (label, key) in enumerate(labels):
            tk.Label(form, text=label, width=15, anchor="e").grid(row=row, column=0, pady=4, sticky="e")
            tk.Entry(form, textvariable=self.vars[key], width=26).grid(row=row, column=1, pady=4, padx=(6, 0))

        # ── 时长模式选择 ──
        duration_frame = tk.LabelFrame(self, text="记录时长", padx=12, pady=8)
        duration_frame.pack(fill=tk.X, padx=18, pady=(4, 0))

        radio_row = tk.Frame(duration_frame)
        radio_row.pack(fill=tk.X)
        tk.Radiobutton(radio_row, text="标准 60 分钟", variable=self.duration_mode,
                       value="standard_60min", command=self._on_duration_changed).pack(side=tk.LEFT, padx=4)
        tk.Radiobutton(radio_row, text="固定时长", variable=self.duration_mode,
                       value="fixed", command=self._on_duration_changed).pack(side=tk.LEFT, padx=12)
        tk.Radiobutton(radio_row, text="手动停止", variable=self.duration_mode,
                       value="manual", command=self._on_duration_changed).pack(side=tk.LEFT, padx=12)

        custom_row = tk.Frame(duration_frame)
        custom_row.pack(fill=tk.X, pady=(6, 0))
        tk.Label(custom_row, text="固定时长 (分钟)：").pack(side=tk.LEFT)
        self.custom_entry = tk.Entry(custom_row, textvariable=self.custom_minutes, width=10, state=tk.DISABLED)
        self.custom_entry.pack(side=tk.LEFT, padx=6)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=12)
        tk.Button(btn_frame, text="创建试验", command=self.create_test, width=18,
                  bg="#2196F3", fg="white", font=("Microsoft YaHei", 10, "bold")).pack()

    def _on_duration_changed(self) -> None:
        """切换时长模式时更新自定义输入框状态。"""
        if self.duration_mode.get() == "fixed":
            self.custom_entry.config(state=tk.NORMAL)
        else:
            self.custom_entry.config(state=tk.DISABLED)

    def _validate_fields(self) -> dict:
        """验证所有输入字段，返回清理后的数据字典。失败时抛出 ValueError。"""
        errors = []
        cleaned = {}

        # 样品编号
        productid = self.vars["productid"].get().strip()
        if not productid:
            errors.append("样品编号不能为空")
        cleaned["productid"] = productid

        # 试验编号
        testid = self.vars["testid"].get().strip()
        if not testid:
            errors.append("试验编号不能为空")
        cleaned["testid"] = testid

        # 样品名称
        productname = self.vars["productname"].get().strip()
        if not productname:
            errors.append("样品名称不能为空")
        cleaned["productname"] = productname

        # 规格型号
        specific = self.vars["specific"].get().strip()
        if not specific:
            errors.append("规格型号不能为空")
        cleaned["specific"] = specific

        # 数值字段验证
        numeric_fields = [
            ("直径 (mm)", "diameter", 1, 500),
            ("高度 (mm)", "height", 1, 500),
            ("试验前质量 (g)", "preweight", 0.1, 9999),
            ("环境温度 (℃)", "ambtemp", -20, 60),
            ("环境湿度 (%)", "ambhumi", 0, 100),
        ]
        for label, key, lo, hi in numeric_fields:
            raw = self.vars[key].get().strip()
            if not raw:
                errors.append(f"{label}不能为空")
                continue
            try:
                val = float(raw)
            except ValueError:
                errors.append(f"{label}必须为有效数字，当前输入为「{raw}」")
                continue
            if val < lo or val > hi:
                errors.append(f"{label}应在 {lo}～{hi} 之间，当前为 {val}")
            cleaned[key] = val

        # 固定时长验证
        if self.duration_mode.get() == "fixed":
            raw_min = self.custom_minutes.get().strip()
            if not raw_min:
                errors.append("固定时长不能为空")
            else:
                try:
                    custom_val = int(raw_min)
                except ValueError:
                    errors.append(f"固定时长必须为整数，当前输入为「{raw_min}」")
                else:
                    if custom_val < 1 or custom_val > 1440:
                        errors.append(f"固定时长应在 1～1440 分钟之间，当前为 {custom_val}")

        if errors:
            raise ValueError("请修正以下问题：\n" + "\n".join(f"  • {e}" for e in errors))
        return cleaned

    def create_test(self) -> None:
        try:
            cleaned = self._validate_fields()
            record = TestRecord(
                productid=cleaned["productid"],
                testid=cleaned["testid"],
                productname=cleaned["productname"],
                specific=cleaned["specific"],
                diameter=cleaned["diameter"],
                height=cleaned["height"],
                operator=self.operator,
                preweight=cleaned["preweight"],
                ambtemp=cleaned["ambtemp"],
                ambhumi=cleaned["ambhumi"],
            )
            self.db.insert_new_test(record)
            self.controller.set_current_test(record)

            # 设置试验时长模式（使用 B 成员的 API）
            mode = self.duration_mode.get()
            if mode == "fixed":
                target_seconds = int(self.custom_minutes.get()) * 60
                self.controller.set_duration_mode("fixed", target_seconds)
            else:
                self.controller.set_duration_mode(mode)

            mode_text = {"standard_60min": "标准 60 分钟", "fixed": f"固定 {self.custom_minutes.get()} 分钟", "manual": "手动停止"}
            messagebox.showinfo("创建成功", f"试验已创建，时长模式：{mode_text[mode]}\n可以开始升温")
            self.destroy()
        except ValueError as exc:
            messagebox.showerror("输入有误", str(exc))
        except Exception as exc:
            messagebox.showerror("创建失败", f"数据库操作失败：{exc}")
