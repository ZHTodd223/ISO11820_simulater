"""ISO 11820 建筑材料不燃性试验仿真系统入口。"""

from database.init_db import init_database
from ui.login_window import LoginWindow


def main() -> None:
    """初始化数据库并启动登录窗口。"""
    init_database()
    app = LoginWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
