import tkinter as tk

class MainMenuUI(tk.Frame):
    def __init__(self, master, app_controller):
        super().__init__(master)
        self.app_controller = app_controller

        tk.Label(self, text="Main Menu", font=("Helvetica", 16)).pack(pady=20)
        tk.Button(self, text="任务列表", command=self.app_controller.show_video_tasks, width=20, height=2).pack(pady=10)
        tk.Button(self, text="用户列表", command=self.app_controller.show_user_list, width=20, height=2).pack(pady=10)
        tk.Button(self, text="用户组列表", command=self.app_controller.show_user_groups, width=20, height=2).pack(pady=10)
        tk.Button(self, text="设置", command=self.app_controller.show_settings, width=20, height=2).pack(pady=10)