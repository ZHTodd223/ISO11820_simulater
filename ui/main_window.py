"""主窗口。"""

import tkinter as tk
from tkinter import messagebox, ttk

from database.db_helper import DbHelper
from services.calibration_service import CalibrationService
from services.test_controller import TestController
from ui.calibration_window import CalibrationHistoryWindow, CalibrationWindow
from ui.new_test_window import NewTestWindow
from ui.operator_manage_window import OperatorManageWindow
from ui.test_record_window import TestRecordWindow

try:
    import matplotlib
    matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "WenQuanYi Micro Hei", "Arial Unicode MS", "sans-serif"]
    matplotlib.rcParams["axes.unicode_minus"] = False
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
except ImportError:
    FigureCanvasTkAgg = None
    Figure = None

# ── 颜色方案 ──
COLOR = {
    "bg": "#F5F7FA",
    "header_bg": "#E3F2FD",
    "accent": "#1565C0",
    "btn_primary": "#2196F3",
    "btn_success": "#4CAF50",
    "btn_warning": "#FF9800",
    "btn_danger": "#F44336",
    "btn_info": "#00BCD4",
    "text_dark": "#212121",
    "text_muted": "#757575",
    "log_bg": "#263238",
    "log_fg": "#ECEFF1",
    "tree_even": "#F5F7FA",
    "tree_header": "#E3F2FD",
}


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
        self.geometry("1160x760")
        self.configure(bg=COLOR["bg"])
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self.add_message(f"系统初始化，操作员：{user['username']}")
        self.after(800, self._tick)

    def _build_ui(self) -> None:
        # ── 顶部状态栏 ──
        top = tk.Frame(self, bg=COLOR["header_bg"], height=48)
        top.pack(fill=tk.X, padx=0, pady=0)
        top.pack_propagate(False)

        inner_top = tk.Frame(top, bg=COLOR["header_bg"])
        inner_top.pack(fill=tk.BOTH, padx=16, pady=6)

        self.state_var = tk.StringVar(value="当前状态：空闲")
        self.timer_var = tk.StringVar(value="记录时间：0 s")
        tk.Label(inner_top, textvariable=self.state_var,
                 font=("Microsoft YaHei", 13, "bold"), fg=COLOR["accent"],
                 bg=COLOR["header_bg"]).pack(side=tk.LEFT, padx=8)
        tk.Label(inner_top, textvariable=self.timer_var,
                 font=("Microsoft YaHei", 10), fg=COLOR["text_muted"],
                 bg=COLOR["header_bg"]).pack(side=tk.LEFT, padx=18)

        # ── 按钮工具栏 ──
        btn_bar = tk.Frame(self, bg=COLOR["bg"])
        btn_bar.pack(fill=tk.X, padx=12, pady=(8, 0))

        btn_style = {"font": ("Microsoft YaHei", 9), "width": 10, "height": 1}

        self.btn_new = tk.Button(btn_bar, text="新建试验", command=self.open_new_test,
                                 bg=COLOR["btn_primary"], fg="white", **btn_style)
        self.btn_heat = tk.Button(btn_bar, text="开始升温", command=self.controller.start_heating,
                                  bg=COLOR["btn_warning"], fg="white", **btn_style)
        self.btn_record = tk.Button(btn_bar, text="开始记录", command=self.controller.start_recording,
                                    bg=COLOR["btn_success"], fg="white", **btn_style)
        self.btn_stop_record = tk.Button(btn_bar, text="停止记录", command=self.controller.stop_recording,
                                         bg=COLOR["btn_danger"], fg="white", **btn_style)
        self.btn_test_record = tk.Button(btn_bar, text="试验记录", command=self.open_test_record,
                                         bg="#9C27B0", fg="white", **btn_style)
        self.btn_stop_heat = tk.Button(btn_bar, text="停止升温", command=self.controller.stop_heating,
                                       bg=COLOR["btn_info"], fg="white", **btn_style)

        for btn in [self.btn_new, self.btn_heat, self.btn_record,
                     self.btn_stop_record, self.btn_test_record, self.btn_stop_heat]:
            btn.pack(side=tk.RIGHT, padx=3)

        # 管理员专有按钮
        if self.user.get("usertype") == "admin":
            self.btn_manage = tk.Button(btn_bar, text="账号管理", command=self._open_operator_manage,
                                        bg="#607D8B", fg="white", **btn_style)
            self.btn_manage.pack(side=tk.LEFT, padx=3)

        # ── 状态指示器 ──
        self.status_indicator = tk.Label(btn_bar, text="●", font=("", 14),
                                         fg="#BDBDBD", bg=COLOR["bg"])
        self.status_indicator.pack(side=tk.LEFT, padx=(4, 0))
        self.status_text = tk.Label(btn_bar, text="空闲", font=("Microsoft YaHei", 9),
                                    fg=COLOR["text_muted"], bg=COLOR["bg"])
        self.status_text.pack(side=tk.LEFT)

        # ── Tab 页签 ──
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=COLOR["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", padding=[16, 6], font=("Microsoft YaHei", 10))
        style.map("TNotebook.Tab", background=[("selected", COLOR["header_bg"])])

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=(6, 8))
        self.tab_run = tk.Frame(self.notebook, bg=COLOR["bg"])
        self.tab_history = tk.Frame(self.notebook, bg=COLOR["bg"])
        self.tab_calibration = tk.Frame(self.notebook, bg=COLOR["bg"])
        self.notebook.add(self.tab_run, text="实时试验")
        self.notebook.add(self.tab_history, text="记录查询")
        self.notebook.add(self.tab_calibration, text="设备校准")

        self._build_run_tab()
        self._build_history_tab()
        self._build_calibration_tab()
        self.update_buttons()

    def _build_run_tab(self) -> None:
        # ── 左侧温度面板 ──
        left = tk.Frame(self.tab_run, bg=COLOR["bg"])
        left.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        tk.Label(left, text="实时温度", font=("Microsoft YaHei", 11, "bold"),
                 fg=COLOR["accent"], bg=COLOR["bg"]).pack(anchor="w", pady=(0, 6))

        self.temp_vars = {}
        temp_colors = {"炉温1": "#E53935", "炉温2": "#FF6F00", "表面温": "#2E7D32",
                       "中心温": "#1565C0", "校准温": "#6A1B9A"}
        for name in ["炉温1", "炉温2", "表面温", "中心温", "校准温"]:
            var = tk.StringVar(value=f"{name}: 25.0 ℃")
            self.temp_vars[name] = var
            fg_color = temp_colors.get(name, COLOR["text_dark"])
            frame = tk.Frame(left, bg=COLOR["bg"])
            frame.pack(fill=tk.X, pady=4)
            dot = tk.Label(frame, text="●", font=("", 10), fg=fg_color, bg=COLOR["bg"])
            dot.pack(side=tk.LEFT, padx=(0, 4))
            tk.Label(frame, textvariable=var, font=("Consolas", 15), width=18,
                     anchor="w", fg=COLOR["text_dark"], bg=COLOR["bg"]).pack(side=tk.LEFT)

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

        # ── 中间曲线区域 ──
        chart_frame = tk.Frame(self.tab_run, bg="white", relief=tk.GROOVE, bd=1)
        chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6, pady=10)
        if FigureCanvasTkAgg and Figure:
            self.fig = Figure(figsize=(6, 4), dpi=100, facecolor="white")
            self.ax = self.fig.add_subplot(111)
            self.ax.set_facecolor("#FAFAFA")
            self.ax.set_ylim(0, 800)
            self.ax.set_title("实时温度曲线", fontsize=12, fontweight="bold", color=COLOR["text_dark"])
            self.ax.set_xlabel("时间 (s)", fontsize=9)
            self.ax.set_ylabel("温度 (℃)", fontsize=9)
            self.ax.grid(True, linestyle="--", alpha=0.3)
            self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        else:
            self.fig = self.ax = self.canvas = None
            tk.Label(chart_frame, text="未安装 Matplotlib，曲线区域暂不可用",
                     bg="white", fg=COLOR["text_muted"]).pack(expand=True)

        # ── 右侧消息日志 ──
        log_frame = tk.Frame(self.tab_run, bg=COLOR["log_bg"])
        log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(6, 10), pady=10)
        tk.Label(log_frame, text="  系统消息  ", font=("Microsoft YaHei", 10, "bold"),
                 fg=COLOR["log_fg"], bg=COLOR["log_bg"]).pack(anchor="w", pady=(6, 2))

        text_container = tk.Frame(log_frame, bg=COLOR["log_bg"])
        text_container.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))
        self.log_text = tk.Text(text_container, width=30, height=22,
                                bg="#37474F", fg=COLOR["log_fg"],
                                font=("Consolas", 9), wrap=tk.WORD,
                                borderwidth=0, relief=tk.FLAT,
                                insertbackground="white",
                                selectbackground="#546E7A")
        self.log_text.pack(fill=tk.BOTH, expand=True)

        scroll = tk.Scrollbar(text_container, command=self.log_text.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scroll.set)

    def _build_history_tab(self) -> None:
        # ── 搜索区域 ──
        search_frame = tk.Frame(self.tab_history, bg=COLOR["bg"])
        search_frame.pack(fill=tk.X, padx=12, pady=10)

        # Row 1: 关键字 + 操作员
        row1 = tk.Frame(search_frame, bg=COLOR["bg"])
        row1.pack(fill=tk.X, pady=3)
        tk.Label(row1, text="样品/试验编号：", width=14, anchor="e",
                 bg=COLOR["bg"], font=("Microsoft YaHei", 9)).pack(side=tk.LEFT)
        self.keyword_var = tk.StringVar()
        tk.Entry(row1, textvariable=self.keyword_var, width=18,
                 font=("Microsoft YaHei", 9)).pack(side=tk.LEFT)

        tk.Label(row1, text="操作员：", width=7, anchor="e",
                 bg=COLOR["bg"], font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=(12, 0))
        self.history_operator_var = tk.StringVar(value="")
        self.history_operator_combo = ttk.Combobox(
            row1, textvariable=self.history_operator_var, width=14, state="readonly",
            font=("Microsoft YaHei", 9),
        )
        self.history_operator_combo.pack(side=tk.LEFT, padx=4)

        # Row 2: 日期范围 + 按钮
        row2 = tk.Frame(search_frame, bg=COLOR["bg"])
        row2.pack(fill=tk.X, pady=3)
        tk.Label(row2, text="开始日期：", width=14, anchor="e",
                 bg=COLOR["bg"], font=("Microsoft YaHei", 9)).pack(side=tk.LEFT)
        self.date_from_var = tk.StringVar()
        tk.Entry(row2, textvariable=self.date_from_var, width=18,
                 font=("Microsoft YaHei", 9)).pack(side=tk.LEFT)

        tk.Label(row2, text="结束日期：", width=7, anchor="e",
                 bg=COLOR["bg"], font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=(12, 0))
        self.date_to_var = tk.StringVar()
        tk.Entry(row2, textvariable=self.date_to_var, width=18,
                 font=("Microsoft YaHei", 9)).pack(side=tk.LEFT)

        tk.Button(row2, text="查询", command=self.refresh_history, width=8,
                  bg=COLOR["btn_primary"], fg="white",
                  font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=(16, 4))
        tk.Button(row2, text="重置", command=self._reset_history_filters, width=8,
                  font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=4)

        # ── TreeView ──
        tree_container = tk.Frame(self.tab_history, bg=COLOR["bg"])
        tree_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 10))

        columns = (
            "productid", "testid", "testdate", "operator",
            "totaltesttime", "lostweight_per", "deltatf", "flag",
        )
        self.history_tree = ttk.Treeview(tree_container, columns=columns, show="headings", height=14)
        col_labels = {
            "productid": "样品编号", "testid": "试验编号", "testdate": "试验日期",
            "operator": "操作员", "totaltesttime": "总时长(s)",
            "lostweight_per": "失重率(%)", "deltatf": "ΔTF(℃)", "flag": "状态",
        }
        col_widths = {
            "productid": 130, "testid": 150, "testdate": 115, "operator": 90,
            "totaltesttime": 95, "lostweight_per": 95, "deltatf": 85, "flag": 75,
        }
        for col in columns:
            self.history_tree.heading(col, text=col_labels.get(col, col))
            self.history_tree.column(col, width=col_widths.get(col, 110), anchor="center", minwidth=60)

        # 滚动条
        vsb = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=vsb.set)
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # TreeView 样式
        style = ttk.Style()
        style.configure("Treeview", rowheight=24, font=("Microsoft YaHei", 9))
        style.map("Treeview", background=[("selected", COLOR["accent"])])

        self._load_operator_list()
        self.refresh_history()

    def _load_operator_list(self) -> None:
        """加载操作员下拉列表。"""
        try:
            ops = self.db.query_operators()
            values = [""] + [op["username"] for op in ops]
            self.history_operator_combo["values"] = values
        except Exception:
            self.history_operator_combo["values"] = [""]

    def _reset_history_filters(self) -> None:
        """重置历史查询筛选条件并刷新。"""
        self.keyword_var.set("")
        self.date_from_var.set("")
        self.date_to_var.set("")
        self.history_operator_var.set("")
        self.refresh_history()

    def _build_calibration_tab(self) -> None:
        cal_header = tk.Frame(self.tab_calibration, bg=COLOR["bg"])
        cal_header.pack(fill=tk.X, padx=14, pady=10)

        tk.Label(cal_header, text="设备校准",
                 font=("Microsoft YaHei", 12, "bold"), fg=COLOR["accent"],
                 bg=COLOR["bg"]).pack(side=tk.LEFT)

        tk.Label(cal_header, text="当前校准温度来自第 5 通道。",
                 font=("Microsoft YaHei", 9), fg=COLOR["text_muted"],
                 bg=COLOR["bg"]).pack(side=tk.LEFT, padx=12)

        btn_frame = tk.Frame(self.tab_calibration, bg=COLOR["bg"])
        btn_frame.pack(fill=tk.X, padx=14, pady=(0, 6))
        tk.Button(btn_frame, text="打开校准窗口", command=self.open_calibration,
                  width=16, bg=COLOR["btn_primary"], fg="white",
                  font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(btn_frame, text="查看校准历史", command=self.open_calibration_history,
                  width=16, bg=COLOR["btn_info"], fg="white",
                  font=("Microsoft YaHei", 9)).pack(side=tk.LEFT)

        # 校准记录列表
        list_container = tk.Frame(self.tab_calibration, bg=COLOR["bg"])
        list_container.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 10))
        self.calibration_list = tk.Text(list_container, height=14,
                                        font=("Consolas", 9), wrap=tk.WORD,
                                        bg="white", fg=COLOR["text_dark"],
                                        relief=tk.GROOVE, bd=1)
        self.calibration_list.pack(fill=tk.BOTH, expand=True)

        cal_scroll = tk.Scrollbar(list_container, command=self.calibration_list.yview)
        cal_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.calibration_list.config(yscrollcommand=cal_scroll.set)

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
        self.ax.set_facecolor("#FAFAFA")
        self.ax.set_ylim(0, 800)
        self.ax.set_title("实时温度曲线", fontsize=12, fontweight="bold", color=COLOR["text_dark"])
        self.ax.set_xlabel("时间 (s)", fontsize=9)
        self.ax.set_ylabel("温度 (℃)", fontsize=9)
        self.ax.grid(True, linestyle="--", alpha=0.3)
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
        """根据控制器返回的按钮状态字典统一设置按钮可用性。"""
        states = self.controller.get_button_states()
        self.btn_new.config(state=tk.NORMAL if states["new_test"] else tk.DISABLED)
        self.btn_heat.config(state=tk.NORMAL if states["start_heating"] else tk.DISABLED)
        self.btn_record.config(state=tk.NORMAL if states["start_recording"] else tk.DISABLED)
        self.btn_stop_record.config(state=tk.NORMAL if states["stop_recording"] else tk.DISABLED)
        self.btn_test_record.config(state=tk.NORMAL if states["test_record"] else tk.DISABLED)
        self.btn_stop_heat.config(state=tk.NORMAL if states["stop_heating"] else tk.DISABLED)

        # 更新状态指示器颜色
        state_colors = {
            "Idle": "#9E9E9E", "Preparing": "#FF9800", "Ready": "#4CAF50",
            "Recording": "#F44336", "Complete": "#2196F3",
        }
        color = state_colors.get(self.controller.state, "#9E9E9E")
        self.status_indicator.config(fg=color)
        self.status_text.config(text=self.controller.STATES.get(self.controller.state, self.controller.state),
                                fg=color)

    def open_new_test(self) -> None:
        if self.controller.needs_save:
            messagebox.showwarning("提示", "上一试验尚未保存记录，\n请先点击「试验记录」完成保存。")
            return
        NewTestWindow(self, self.controller, self.user["username"])

    def open_test_record(self) -> None:
        if self.controller.state != "Complete":
            messagebox.showinfo("提示", "试验完成后才能填写试验记录")
            return
        TestRecordWindow(self, self.controller, on_saved=self._after_record_saved)

    def open_calibration(self) -> None:
        CalibrationWindow(self, self.user["username"],
                          lambda: self.latest_data.tcal if self.latest_data else 25.0,
                          self.refresh_calibrations)

    def open_calibration_history(self) -> None:
        CalibrationHistoryWindow(self, self.calibration_service)

    def _after_record_saved(self) -> None:
        """试验保存后：刷新历史、清空缓存、保温待命。"""
        self.refresh_history()
        self.controller.record_samples.clear()
        self.controller.record_seconds = 0
        self.controller.mark_saved()          # needs_save=False, Complete→Preparing（保温）
        self.controller.current_test = None   # 清空，准备下一次试验

    def refresh_history(self) -> None:
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        for row in self.db.query_tests(
            keyword=self.keyword_var.get() if hasattr(self, "keyword_var") else "",
            date_from=self.date_from_var.get() if hasattr(self, "date_from_var") else "",
            date_to=self.date_to_var.get() if hasattr(self, "date_to_var") else "",
            operator=self.history_operator_var.get() if hasattr(self, "history_operator_var") else "",
        ):
            self.history_tree.insert("", tk.END, values=tuple(row.values()))

    def refresh_calibrations(self) -> None:
        if not hasattr(self, "calibration_list"):
            return
        self.calibration_list.delete("1.0", tk.END)
        records = self.calibration_service.list_records()
        if not records:
            self.calibration_list.insert(tk.END, "暂无校准记录")
            return
        for row in records:
            passed = "合格" if row.get("PassedCriteria", 1) == 1 else "不合格"
            temp_data = row.get("TemperatureData", "")
            if len(temp_data) > 60:
                temp_data = temp_data[:57] + "..."
            self.calibration_list.insert(
                tk.END,
                f"{row['CalibrationDate']} | {row['Operator']} | {passed} | {temp_data} | {row['Remarks']}\n"
            )

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
        if self.controller.state == "Recording":
            if not messagebox.askyesno("确认退出", "当前正在记录试验数据，退出将丢失未保存的记录。\n确定要退出吗？"):
                return
        self.master.destroy()

    def _open_operator_manage(self) -> None:
        OperatorManageWindow(self)

    # TODO[E]: 优化按钮、颜色、表格列宽和整体布局。
