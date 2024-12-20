import tkinter as tk
from app_controller import AppController
from database import initialize_database
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Auto Video Uploader")
        self.geometry("900x600")
        # 初始化数据库
        initialize_database()
        # 初始化控制器
        self.app_controller = AppController(self)
        self.app_controller.show_main_menu()

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()