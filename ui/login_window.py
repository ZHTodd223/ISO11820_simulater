"""登录窗口。"""

import tkinter as tk
from tkinter import messagebox

from database.db_helper import DbHelper
from ui.main_window import MainWindow


class LoginWindow(tk.Tk):
    """角色选择 + 密码登录窗口。"""

    def __init__(self) -> None:
        super().__init__()
        self.title("ISO 11820 登录")
        self.geometry("360x230")
        self.resizable(False, False)
        self.db = DbHelper()
        self.role_var = tk.StringVar(value="admin")
        self.password_var = tk.StringVar(value="123456")
        self._build_ui()

    def _build_ui(self) -> None:
        tk.Label(self, text="ISO 11820 建筑材料不燃性试验仿真系统", font=("Microsoft YaHei", 11, "bold")).pack(pady=18)
        role_frame = tk.Frame(self)
        role_frame.pack(pady=8)
        tk.Radiobutton(role_frame, text="管理员", variable=self.role_var, value="admin").pack(side=tk.LEFT, padx=12)
        tk.Radiobutton(role_frame, text="试验员", variable=self.role_var, value="experimenter").pack(side=tk.LEFT, padx=12)

        pwd_frame = tk.Frame(self)
        pwd_frame.pack(pady=8)
        tk.Label(pwd_frame, text="密码：").pack(side=tk.LEFT)
        tk.Entry(pwd_frame, textvariable=self.password_var, show="*", width=18).pack(side=tk.LEFT)

        tk.Button(self, text="登录", width=16, command=self._login).pack(pady=16)

    def _login(self) -> None:
        username = self.role_var.get()
        user = self.db.login(username, self.password_var.get())
        if not user:
            messagebox.showerror("登录失败", "密码错误，请重新输入")
            return

        self.withdraw()
        MainWindow(master=self, user=user)

    # TODO[A]: 允许管理员在数据库中维护操作员账号。
