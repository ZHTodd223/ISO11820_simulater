"""操作员账号管理窗口。"""

import tkinter as tk
from tkinter import messagebox, ttk

from database.db_helper import DbHelper


class OperatorManageWindow(tk.Toplevel):
    """管理员维护操作员账号——增、删、改密码。"""

    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master)
        self.db = DbHelper()
        self.title("操作员账号管理")
        self.geometry("600x430")
        self.resizable(False, False)

        self._build_ui()
        self._refresh_list()

    def _build_ui(self) -> None:
        # ── 列表区域 ──
        list_frame = tk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(12, 6))

        columns = ("userid", "username", "usertype")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        self.tree.heading("userid", text="用户ID")
        self.tree.heading("username", text="用户名")
        self.tree.heading("usertype", text="角色")
        self.tree.column("userid", width=80, anchor="center")
        self.tree.column("username", width=230)
        self.tree.column("usertype", width=140, anchor="center")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_operator_selected)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # ── 表单 ──
        form_frame = tk.LabelFrame(self, text="新增 / 修改", padx=12, pady=8)
        form_frame.pack(fill=tk.X, padx=12, pady=(0, 6))

        row1 = tk.Frame(form_frame)
        row1.pack(fill=tk.X, pady=3)
        tk.Label(row1, text="用户名：", width=10, anchor="e").pack(side=tk.LEFT)
        self.username_var = tk.StringVar()
        tk.Entry(row1, textvariable=self.username_var, width=24).pack(side=tk.LEFT, padx=4)

        tk.Label(row1, text="角色：", width=8, anchor="e").pack(side=tk.LEFT)
        self.usertype_var = tk.StringVar(value="operator")
        ttk.Combobox(
            row1,
            textvariable=self.usertype_var,
            values=("operator", "admin"),
            state="readonly",
            width=12,
        ).pack(side=tk.LEFT, padx=4)

        row2 = tk.Frame(form_frame)
        row2.pack(fill=tk.X, pady=3)
        tk.Label(row2, text="密码：", width=10, anchor="e").pack(side=tk.LEFT)
        self.pwd_var = tk.StringVar()
        tk.Entry(row2, textvariable=self.pwd_var, show="*", width=24).pack(side=tk.LEFT, padx=4)

        # ── 按钮 ──
        btn_frame = tk.Frame(form_frame)
        btn_frame.pack(fill=tk.X, pady=(6, 0))
        tk.Button(btn_frame, text="新增操作员", command=self._add_operator, width=16).pack(
            side=tk.LEFT, padx=6
        )
        tk.Button(btn_frame, text="修改密码", command=self._change_password, width=16).pack(
            side=tk.LEFT, padx=6
        )
        tk.Button(btn_frame, text="删除选中", command=self._delete_operator, width=16).pack(
            side=tk.LEFT, padx=6
        )

        # ── 底部 ──
        tk.Button(self, text="刷新列表", command=self._refresh_list, width=16).pack(
            side=tk.LEFT, padx=12, pady=6
        )
        tk.Button(self, text="关闭", command=self.destroy, width=16).pack(
            side=tk.RIGHT, padx=12, pady=6
        )

    def _refresh_list(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            for op in self.db.query_operators():
                self.tree.insert(
                    "", tk.END,
                    values=(op["userid"], op["username"], op["usertype"]),
                )
        except Exception as exc:
            messagebox.showerror("查询失败", str(exc))

    def _on_operator_selected(self, _event=None) -> None:
        """选中账号时回显用户名和角色，密码等待重新输入。"""
        selection = self.tree.selection()
        if not selection:
            return
        values = self.tree.item(selection[0], "values")
        if len(values) < 3:
            return
        self.username_var.set(values[1])
        self.usertype_var.set(values[2])
        self.pwd_var.set("")

    def _add_operator(self) -> None:
        username = self.username_var.get().strip()
        pwd = self.pwd_var.get().strip()
        usertype = self.usertype_var.get()
        if not username:
            messagebox.showwarning("提示", "请输入用户名")
            return
        if not pwd:
            messagebox.showwarning("提示", "请输入密码")
            return
        try:
            self.db.add_operator(username, pwd, usertype)
            messagebox.showinfo("成功", f"操作员 '{username}' 已添加")
            self._refresh_list()
            self.username_var.set("")
            self.pwd_var.set("")
        except ValueError as exc:
            messagebox.showerror("添加失败", str(exc))

    def _change_password(self) -> None:
        username = self.username_var.get().strip()
        new_pwd = self.pwd_var.get().strip()
        if not username:
            messagebox.showwarning("提示", "请先输入用户名")
            return
        if not new_pwd:
            messagebox.showwarning("提示", "请输入新密码")
            return
        try:
            self.db.update_operator_password(username, new_pwd)
            messagebox.showinfo("成功", f"用户 '{username}' 的密码已修改")
            self.pwd_var.set("")
        except ValueError as exc:
            messagebox.showerror("修改失败", str(exc))

    def _delete_operator(self) -> None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先在列表中选中一个操作员")
            return
        values = self.tree.item(selection[0], "values")
        username = values[1]
        if not messagebox.askyesno("确认删除", f"确定要删除操作员 '{username}' 吗？"):
            return
        try:
            self.db.delete_operator(username)
            messagebox.showinfo("成功", f"操作员 '{username}' 已删除")
            self._refresh_list()
        except ValueError as exc:
            messagebox.showerror("删除失败", str(exc))
