# utils.py
import sys
import json
import os

CONFIG_FILE = "settings.json"

def load_config():
    """加载配置文件"""
    try:
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        # 如果文件不存在或解析失败，返回默认配置
        return {
            "chromium_path": "",
            "headless_mode": True,
            "worker_threads": 2
        }

def save_config(config):
    """保存配置到文件"""
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)

class Logger:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.default_stdout = sys.stdout  # 记录默认的标准输出

    def write(self, message):
        if self.text_widget.winfo_exists():  # 检查控件是否存在
            self.text_widget.insert("end", message)
            self.text_widget.see("end")  # 自动滚动到最新内容
        else:
            print(f"日志控件不存在，跳过写入：{message}")

    def flush(self):
        pass  # 用于兼容 `sys.stdout` 的行为
