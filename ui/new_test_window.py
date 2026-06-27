"""新建试验窗口。"""

import tkinter as tk
from datetime import datetime
from tkinter import messagebox

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
        self.geometry("420x420")
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
        self._build_ui()

    def _build_ui(self) -> None:
        labels = [
            ("样品编号", "productid"),
            ("试验编号", "testid"),
            ("样品名称", "productname"),
            ("规格型号", "specific"),
            ("直径(mm)", "diameter"),
            ("高度(mm)", "height"),
            ("试验前质量(g)", "preweight"),
            ("环境温度(℃)", "ambtemp"),
            ("环境湿度(%)", "ambhumi"),
        ]
        form = tk.Frame(self)
        form.pack(padx=18, pady=18, fill=tk.BOTH)
        for row, (label, key) in enumerate(labels):
            tk.Label(form, text=label, width=14, anchor="e").grid(row=row, column=0, pady=5)
            tk.Entry(form, textvariable=self.vars[key], width=24).grid(row=row, column=1, pady=5)
        tk.Button(self, text="创建试验", command=self.create_test, width=18).pack(pady=12)

    def create_test(self) -> None:
        try:
            record = TestRecord(
                productid=self.vars["productid"].get().strip(),
                testid=self.vars["testid"].get().strip(),
                productname=self.vars["productname"].get().strip(),
                specific=self.vars["specific"].get().strip(),
                diameter=float(self.vars["diameter"].get()),
                height=float(self.vars["height"].get()),
                operator=self.operator,
                preweight=float(self.vars["preweight"].get()),
                ambtemp=float(self.vars["ambtemp"].get()),
                ambhumi=float(self.vars["ambhumi"].get()),
            )
            self.db.insert_new_test(record)
            self.controller.set_current_test(record)
            messagebox.showinfo("成功", "试验已创建，可以开始升温")
            self.destroy()
        except Exception as exc:
            messagebox.showerror("创建失败", str(exc))

    # TODO[E]: 增加标准 60 分钟 / 自定义分钟选择。
