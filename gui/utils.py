# utils.py
import sys


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
