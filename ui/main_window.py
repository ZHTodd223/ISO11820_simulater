"""主窗口。"""

import tkinter as tk
from tkinter import messagebox, ttk

from database.db_helper import DbHelper
from services.calibration_service import CalibrationService
from services.test_controller import TestController
from ui.calibration_window import CalibrationWindow
from ui.new_test_window import NewTestWindow
from ui.test_record_window import TestRecordWindow

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
except ImportError:
    FigureCanvasTkAgg = None
    Figure = None


class MainWindow(tk.Toplevel):
    """系统主界面。"""

    # 异常测试下拉项 -> 仿真异常模式
    _ANOMALY_MAP = {
        "正常": "none",
        "温度尖峰": "spike",
        "传感器失效": "sensor_failure",
        "超温": "overheat",
    }

    def __init__(self, master: tk.Tk, user: dict) -> None:
        super().__init__(master)
        self.user = user
        self.db = DbHelper()
        self.controller = TestController()
        self.controller.on_message = self.add_message
        self.controller.on_state_changed = lambda _state: self.update_buttons()
        self.calibration_service = CalibrationService()
        self.latest_data = None
        # (elapsed_seconds, tf1, tf2, ts, tc)
        self.chart_points: list[tuple[float, float, float, float, float]] = []
        self._chart_elapsed = 0.0

        self.title(f"ISO 11820 仿真系统 - {user['username']}")
        self.geometry("1120x720")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self.add_message(f"系统初始化，操作员：{user['username']}")
        self.after(800, self._tick)

    def _build_ui(self) -> None:
        top = tk.Frame(self)
        top.pack(fill=tk.X, padx=12, pady=8)
        self.state_var = tk.StringVar(value="当前状态：空闲")
        self.timer_var = tk.StringVar(value="记录时间：0 s")
        tk.Label(top, textvariable=self.state_var, font=("Microsoft YaHei", 13, "bold")).pack(side=tk.LEFT, padx=8)
        tk.Label(top, textvariable=self.timer_var).pack(side=tk.LEFT, padx=18)

        self.btn_new = tk.Button(top, text="新建试验", command=self.open_new_test)
        self.btn_heat = tk.Button(top, text="开始升温", command=self.controller.start_heating)
        self.btn_record = tk.Button(top, text="开始记录", command=self.controller.start_recording)
        self.btn_stop_record = tk.Button(top, text="停止记录", command=self.controller.stop_recording)
        self.btn_test_record = tk.Button(top, text="试验记录", command=self.open_test_record)
        self.btn_stop_heat = tk.Button(top, text="停止升温", command=self.controller.stop_heating)
        for btn in [self.btn_new, self.btn_heat, self.btn_record, self.btn_stop_record, self.btn_test_record, self.btn_stop_heat]:
            btn.pack(side=tk.RIGHT, padx=4)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        self.tab_run = tk.Frame(self.notebook)
        self.tab_history = tk.Frame(self.notebook)
        self.tab_calibration = tk.Frame(self.notebook)
        self.notebook.add(self.tab_run, text="实时试验")
        self.notebook.add(self.tab_history, text="记录查询")
        self.notebook.add(self.tab_calibration, text="设备校准")

        self._build_run_tab()
        self._build_history_tab()
        self._build_calibration_tab()
        self.update_buttons()

    def _build_run_tab(self) -> None:
        left = tk.Frame(self.tab_run)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)
        self.temp_vars = {}
        for name in ["炉温1", "炉温2", "表面温", "中心温", "校准温"]:
            var = tk.StringVar(value=f"{name}: 25.0 ℃")
            self.temp_vars[name] = var
            tk.Label(left, textvariable=var, font=("Consolas", 16), width=18, anchor="w").pack(pady=8)

        # 最近 10 分钟温漂显示
        self.drift_var = tk.StringVar(value="最近10分钟温漂：0.00 ℃/min")
        tk.Label(left, textvariable=self.drift_var, font=("Consolas", 11), width=18, anchor="w").pack(pady=8)

        # 温度异常测试入口
        anomaly_frame = tk.Frame(left)
        anomaly_frame.pack(fill=tk.X, pady=8)
        tk.Label(anomaly_frame, text="异常测试：").pack(side=tk.LEFT)
        self.anomaly_var = tk.StringVar(value="正常")
        self.anomaly_combo = ttk.Combobox(
            anomaly_frame,
            textvariable=self.anomaly_var,
            values=list(self._ANOMALY_MAP.keys()),
            state="readonly",
            width=12,
        )
        self.anomaly_combo.pack(side=tk.LEFT)
        self.anomaly_combo.bind("<<ComboboxSelected>>", self._on_anomaly_changed)

        chart_frame = tk.Frame(self.tab_run)
        chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)
        if FigureCanvasTkAgg and Figure:
            self.fig = Figure(figsize=(6, 4), dpi=100)
            self.ax = self.fig.add_subplot(111)
            self.ax.set_ylim(0, 800)
            self.ax.set_title("实时温度曲线")
            self.ax.set_xlabel("时间(s)")
            self.ax.set_ylabel("温度(℃)")
            self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            self.fig = self.ax = self.canvas = None
            tk.Label(chart_frame, text="未安装 Matplotlib，曲线区域暂不可用").pack(expand=True)

        log_frame = tk.Frame(self.tab_run)
        log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=8, pady=8)
        tk.Label(log_frame, text="系统消息").pack(anchor="w")
        self.log_text = tk.Text(log_frame, width=34, height=26)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _build_history_tab(self) -> None:
        search_frame = tk.Frame(self.tab_history)
        search_frame.pack(fill=tk.X, padx=8, pady=8)
        self.keyword_var = tk.StringVar()
        tk.Label(search_frame, text="样品/试验编号：").pack(side=tk.LEFT)
        tk.Entry(search_frame, textvariable=self.keyword_var, width=24).pack(side=tk.LEFT)
        tk.Button(search_frame, text="查询", command=self.refresh_history).pack(side=tk.LEFT, padx=8)

        columns = ("productid", "testid", "testdate", "operator", "totaltesttime", "lostweight_per", "deltatf", "flag")
        self.history_tree = ttk.Treeview(self.tab_history, columns=columns, show="headings")
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=120)
        self.history_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.refresh_history()

    def _build_calibration_tab(self) -> None:
        tk.Label(self.tab_calibration, text="当前校准温度来自第 5 通道。").pack(anchor="w", padx=12, pady=8)
        tk.Button(self.tab_calibration, text="打开校准窗口", command=self.open_calibration).pack(anchor="w", padx=12)
        self.calibration_list = tk.Text(self.tab_calibration, height=18)
        self.calibration_list.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        self.refresh_calibrations()

    def _tick(self) -> None:
        self.latest_data = self.controller.tick()
        d = self.latest_data
        self.temp_vars["炉温1"].set(f"炉温1: {d.tf1:.1f} ℃")
        self.temp_vars["炉温2"].set(f"炉温2: {d.tf2:.1f} ℃")
        self.temp_vars["表面温"].set(f"表面温: {d.ts:.1f} ℃")
        self.temp_vars["中心温"].set(f"中心温: {d.tc:.1f} ℃")
        self.temp_vars["校准温"].set(f"校准温: {d.tcal:.1f} ℃")
        self.state_var.set(f"当前状态：{self.controller.STATES[self.controller.state]}")
        self.timer_var.set(f"记录时间：{self.controller.record_seconds} s")
        self._chart_elapsed += self.controller.simulator.tick_seconds
        self.chart_points.append((self._chart_elapsed, d.tf1, d.tf2, d.ts, d.tc))
        # 滚动保留最近 10 分钟数据
        self.chart_points = [p for p in self.chart_points if p[0] >= self._chart_elapsed - 600]
        self.drift_var.set(f"最近10分钟温漂：{self.controller.simulator.calc_drift():.2f} ℃/min")
        # 模型层异常检测：读数越界时提示
        if d.is_anomalous() and not getattr(self, "_anomaly_alerted", False):
            self.add_message("警告：检测到异常温度读数，请检查传感器/设备")
            self._anomaly_alerted = True
        elif not d.is_anomalous():
            self._anomaly_alerted = False
        self._redraw_chart()
        self.update_buttons()
        self.after(800, self._tick)

    def _redraw_chart(self) -> None:
        if not self.ax or not self.canvas:
            return
        self.ax.clear()
        self.ax.set_ylim(0, 800)
        self.ax.set_title("实时温度曲线")
        self.ax.set_xlabel("时间(s)")
        self.ax.set_ylabel("温度(℃)")
        xs = [p[0] for p in self.chart_points]
        if xs:
            self.ax.plot(xs, [p[1] for p in self.chart_points], label="TF1")
            self.ax.plot(xs, [p[2] for p in self.chart_points], label="TF2")
            self.ax.plot(xs, [p[3] for p in self.chart_points], label="TS")
            self.ax.plot(xs, [p[4] for p in self.chart_points], label="TC")
            self.ax.legend(loc="upper left")
            # X 轴滚动显示最近 10 分钟
            x_max = xs[-1]
            self.ax.set_xlim(max(0.0, x_max - 600), x_max)
        self.canvas.draw_idle()

    def update_buttons(self) -> None:
        state = self.controller.state
        self.btn_new.config(state=tk.NORMAL if state in ("Idle", "Complete") else tk.DISABLED)
        self.btn_heat.config(state=tk.NORMAL if state == "Idle" else tk.DISABLED)
        self.btn_record.config(state=tk.NORMAL if state == "Ready" else tk.DISABLED)
        self.btn_stop_record.config(state=tk.NORMAL if state == "Recording" else tk.DISABLED)
        self.btn_test_record.config(state=tk.NORMAL if state == "Complete" else tk.DISABLED)
        self.btn_stop_heat.config(state=tk.NORMAL if state in ("Preparing", "Ready", "Complete") else tk.DISABLED)

    def open_new_test(self) -> None:
        NewTestWindow(self, self.controller, self.user["username"])

    def open_test_record(self) -> None:
        if self.controller.state != "Complete":
            messagebox.showinfo("提示", "试验完成后才能填写试验记录")
            return
        TestRecordWindow(self, self.controller, on_saved=self._after_record_saved)

    def open_calibration(self) -> None:
        CalibrationWindow(self, self.user["username"], lambda: self.latest_data.tcal if self.latest_data else 25.0, self.refresh_calibrations)

    def _after_record_saved(self) -> None:
        self.refresh_history()
        self.controller.current_test = None
        self.controller.record_samples.clear()
        self.controller.record_seconds = 0
        self.controller.stop_heating()

    def refresh_history(self) -> None:
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        for row in self.db.query_tests(self.keyword_var.get() if hasattr(self, "keyword_var") else ""):
            self.history_tree.insert("", tk.END, values=tuple(row.values()))

    def refresh_calibrations(self) -> None:
        if not hasattr(self, "calibration_list"):
            return
        self.calibration_list.delete("1.0", tk.END)
        for row in self.calibration_service.list_records():
            self.calibration_list.insert(tk.END, f"{row['CalibrationDate']}  {row['Operator']}  {row['TemperatureData']}  {row['Remarks']}\n")

    def add_message(self, message: str) -> None:
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def _on_anomaly_changed(self, _event=None) -> None:
        """切换温度异常测试模式。"""
        label = self.anomaly_var.get()
        mode = self._ANOMALY_MAP.get(label, "none")
        self.controller.simulator.set_anomaly_mode(mode)
        self.add_message(f"异常测试模式：{label}")

    def _on_close(self) -> None:
        self.master.destroy()

    # TODO[E]: 优化按钮、颜色、表格列宽和整体布局。
