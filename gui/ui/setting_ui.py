import tkinter as tk
from tkinter import ttk, messagebox, Text
from utils import load_config, save_config

class SettingUI(tk.Frame):
    def __init__(self, master, app_controller):
        super().__init__(master)
        self.app_controller = app_controller
        self.config = load_config()
        self.create_widgets()

    def create_widgets(self):
        # 设置区域
        settings_frame = tk.Frame(self)
        settings_frame.pack(pady=10, fill="x")

        # Chromium 浏览器路径
        tk.Label(settings_frame, text="Chromium浏览器路径").pack(side="top", padx=5)
        self.chromium_path_var = tk.StringVar(value=self.config["chromium_path"])
        chromium_path_entry = ttk.Entry(settings_frame, textvariable=self.chromium_path_var, width=50)
        chromium_path_entry.pack(side="top", padx=5)

        # Headless 模式
        tk.Label(settings_frame, text="Headless 模式:").pack(side="top", padx=5)
        self.headless_var = tk.BooleanVar(value=self.config["headless_mode"])
        headless_checkbox = tk.Checkbutton(
            settings_frame,
            variable=self.headless_var,
        )
        headless_checkbox.pack(side="top", padx=5)

        # 工作线程数量
        tk.Label(settings_frame, text="工作线程数量:").pack(side="top", padx=5)
        self.worker_threads_var = tk.IntVar(value=self.config["worker_threads"])
        worker_threads_entry = ttk.Entry(
            settings_frame,
            textvariable=self.worker_threads_var,
            width=5
        )
        worker_threads_entry.pack(side="top", padx=5)

        button_frame = tk.Frame(settings_frame)
        button_frame.pack(side="top", pady=5, padx=10)
        # 保存和返回按钮
        save_button = tk.Button(
            button_frame,
            text="保存设置",
            command=self.save_settings
        )
        save_button.pack(side="left", padx=5)

        return_button = tk.Button(
            button_frame,
            text="返回",
            command=self.app_controller.show_main_menu
        )
        return_button.pack(side="left", padx=5)

    def update_headless_mode(self):
        """更新 headless 模式"""
        self.config["headless_mode"] = self.headless_var.get()

    def save_settings(self):
        """保存设置"""
        # 更新配置字典中的值
        self.config["chromium_path"] = self.chromium_path_var.get()
        self.config["headless_mode"] = self.headless_var.get()
        self.config["worker_threads"] = self.worker_threads_var.get()
        
        # 保存到配置文件
        save_config(self.config)
        # 显示保存成功提示
        tk.messagebox.showinfo("保存成功", "设置已保存！")