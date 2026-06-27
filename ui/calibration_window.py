"""设备校准窗口。"""

import tkinter as tk
from tkinter import messagebox

from services.calibration_service import CalibrationService


class CalibrationWindow(tk.Toplevel):
    """记录当前校准温度。"""

    def __init__(self, master: tk.Toplevel, operator: str, get_tcal, on_saved) -> None:
        super().__init__(master)
        self.operator = operator
        self.get_tcal = get_tcal
        self.on_saved = on_saved
        self.service = CalibrationService()
        self.remarks = tk.StringVar(value="课堂演示校准")
        self.temp_var = tk.StringVar(value="")
        self.title("设备校准")
        self.geometry("360x220")
        self._build_ui()
        self._refresh_temp()

    def _build_ui(self) -> None:
        tk.Label(self, textvariable=self.temp_var, font=("Consolas", 18)).pack(pady=18)
        frame = tk.Frame(self)
        frame.pack(pady=8)
        tk.Label(frame, text="备注：").pack(side=tk.LEFT)
        tk.Entry(frame, textvariable=self.remarks, width=24).pack(side=tk.LEFT)
        tk.Button(self, text="保存校准记录", command=self.save).pack(pady=16)

    def _refresh_temp(self) -> None:
        self.temp_var.set(f"校准温度：{self.get_tcal():.1f} ℃")
        self.after(1000, self._refresh_temp)

    def save(self) -> None:
        self.service.save_current_temperature(self.operator, self.get_tcal(), self.remarks.get())
        messagebox.showinfo("成功", "校准记录已保存")
        self.on_saved()
        self.destroy()

    # TODO[E]: 支持多点校准录入和历史明细窗口。
