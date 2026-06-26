"""登录窗口。"""

import tkinter as tk
from tkinter import messagebox, ttk

from database.db_helper import DbHelper
from ui.main_window import MainWindow


class LoginWindow(tk.Tk):
    """用户名 + 密码登录窗口。"""

    def __init__(self) -> None:
        super().__init__()
        self.title("ISO 11820 登录")
        self.geometry("360x250")
        self.resizable(False, False)
        self.db = DbHelper()
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar(value="123456")
        self._build_ui()

    def _build_ui(self) -> None:
        tk.Label(
            self, text="ISO 11820 建筑材料不燃性试验仿真系统",
            font=("Microsoft YaHei", 11, "bold"),
        ).pack(pady=18)

        # 用户名（下拉框从数据库加载）
        user_frame = tk.Frame(self)
        user_frame.pack(pady=8)
        tk.Label(user_frame, text="用户名：").pack(side=tk.LEFT)
        self.username_combo = ttk.Combobox(
            user_frame, textvariable=self.username_var, width=18, state="readonly"
        )
        self.username_combo.pack(side=tk.LEFT)
        self._load_usernames()

        # 密码
        pwd_frame = tk.Frame(self)
        pwd_frame.pack(pady=8)
        tk.Label(pwd_frame, text="密　码：").pack(side=tk.LEFT)
        tk.Entry(pwd_frame, textvariable=self.password_var, show="*", width=18).pack(side=tk.LEFT)

        tk.Button(self, text="登录", width=16, command=self._login).pack(pady=12)

    def _load_usernames(self) -> None:
        """从数据库加载操作员用户名列表。"""
        try:
            ops = self.db.query_operators()
            usernames = [op["username"] for op in ops]
            self.username_combo["values"] = usernames
            if usernames:
                self.username_combo.current(0)
        except Exception:
            self.username_combo["values"] = ["admin", "experimenter"]
            self.username_combo.current(0)

    def _login(self) -> None:
        username = self.username_var.get().strip()
        if not username:
            messagebox.showerror("登录失败", "请选择用户名")
            return
        user = self.db.login(username, self.password_var.get())
        if not user:
            messagebox.showerror("登录失败", "密码错误，请重新输入")
            return

        self.withdraw()
        MainWindow(master=self, user=user)
