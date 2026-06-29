"""登录窗口。"""

import json
import tkinter as tk
from tkinter import messagebox, ttk

from database.db_helper import DbHelper
from ui.main_window import MainWindow
from utils.path_utils import app_base_dir


LOGIN_SETTINGS_PATH = app_base_dir() / "data" / "login_settings.json"


class LoginWindow(tk.Tk):
    """用户名 + 密码登录窗口。"""

    def __init__(self) -> None:
        super().__init__()
        self.title("ISO 11820 登录")
        self.geometry("380x285")
        self.resizable(False, False)
        self.db = DbHelper()
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.remember_password_var = tk.BooleanVar(value=False)
        self.login_settings = self._load_login_settings()
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
        self.username_combo.bind("<<ComboboxSelected>>", lambda _event: self._on_username_changed())
        self._load_usernames()

        # 密码
        pwd_frame = tk.Frame(self)
        pwd_frame.pack(pady=8)
        tk.Label(pwd_frame, text="密　码：").pack(side=tk.LEFT)
        tk.Entry(pwd_frame, textvariable=self.password_var, show="*", width=18).pack(side=tk.LEFT)

        tk.Checkbutton(
            self,
            text="保存密码",
            variable=self.remember_password_var,
        ).pack(pady=(0, 4))

        tk.Button(self, text="登录", width=18, command=self._login).pack(pady=8)

    def _load_usernames(self) -> None:
        """从数据库加载操作员用户名列表。"""
        try:
            ops = self.db.query_operators()
            usernames = [op["username"] for op in ops]
            self.username_combo["values"] = usernames
            if usernames:
                index = self._preferred_username_index(usernames)
                self.username_combo.current(index)
                self._on_username_changed()
        except Exception:
            self.username_combo["values"] = ["admin", "experimenter"]
            self.username_combo.current(0)
            self._on_username_changed()

    def _preferred_username_index(self, usernames: list[str]) -> int:
        last_username = self.login_settings.get("last_username", "")
        if last_username in usernames:
            return usernames.index(last_username)
        return 0

    def _on_username_changed(self) -> None:
        """切换用户时同步回填该用户保存过的密码。"""
        username = self.username_var.get().strip()
        saved_passwords = self.login_settings.get("saved_passwords", {})
        saved_password = saved_passwords.get(username, "")
        self.password_var.set(saved_password)
        self.remember_password_var.set(bool(saved_password))

    def _login(self) -> None:
        username = self.username_var.get().strip()
        if not username:
            messagebox.showerror("登录失败", "请选择用户名")
            return
        user = self.db.login(username, self.password_var.get())
        if not user:
            messagebox.showerror("登录失败", "密码错误，请重新输入")
            return

        self._save_login_settings(username, self.password_var.get())
        self.withdraw()
        MainWindow(master=self, user=user)

    def _load_login_settings(self) -> dict:
        try:
            with LOGIN_SETTINGS_PATH.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return {"last_username": "", "saved_passwords": {}}
        if not isinstance(data, dict):
            return {"last_username": "", "saved_passwords": {}}
        data.setdefault("last_username", "")
        data.setdefault("saved_passwords", {})
        return data

    def _save_login_settings(self, username: str, password: str) -> None:
        self.login_settings["last_username"] = username
        saved_passwords = self.login_settings.setdefault("saved_passwords", {})
        if self.remember_password_var.get():
            saved_passwords[username] = password
        else:
            saved_passwords.pop(username, None)

        try:
            LOGIN_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
            with LOGIN_SETTINGS_PATH.open("w", encoding="utf-8") as f:
                json.dump(self.login_settings, f, ensure_ascii=False, indent=2)
        except OSError as exc:
            messagebox.showwarning("保存密码失败", f"登录成功，但保存密码设置失败：{exc}")
