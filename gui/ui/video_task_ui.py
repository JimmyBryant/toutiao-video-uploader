import tkinter as tk
from tkinter import ttk, messagebox, Text
from database import fetch_all_users, fetch_user_by_id
from database import fetch_all_user_groups, fetch_user_group_by_id, fetch_user_group_members_by_id
from database import add_video_task,  fetch_all_video_tasks, fetch_video_task_by_id, update_video_task_status, fetch_pending_video_tasks, update_video_task
import datetime
import threading
import queue
import importlib
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
import json
from utils import Logger, load_config
import sys
import os
import asyncio
from threading import Lock

# 全局任务队列
task_queue = queue.Queue()
scheduler_thread = None  # 全局变量，存储调度器线程
scheduler_event = threading.Event()  # 全局事件，用于控制线程停止
is_scheduler_running = False  # 定时任务状态
global_stop_flag = threading.Event()  # 添加全局停止标志

class TaskManager:
    def __init__(self):
        self.running_tasks = {}
        self.lock = Lock()

    def is_task_running(self, task_id): 
        print(f"检查任务 {task_id} 是否在运行")
        return task_id in self.running_tasks

    def add_task(self, task_id, task):
        with self.lock:
            task_running = self.is_task_running(task_id)
            if task_running:
                raise ValueError(f"任务 {task_id} 已经在运行中，无法重复添加。")
            self.running_tasks[task_id] = task
            print(f"任务 {task_id} 已添加到 running_tasks")

    def remove_task(self, task_id):
        with self.lock:
            self.running_tasks.pop(task_id, None)

    def get_task_by_id(self, task_id):
        with self.lock:
            return self.running_tasks.get(task_id)

    
task_manager = TaskManager()

async def process_task_async(task):
    """
    处理单个视频任务。根据平台动态调用对应的 upload_video 函数（异步）。
    """
    task_id, video_title, video_desc, video_path, cover_path, video_tags, user_group_id, user_id, scheduled_time, status = task

    if task_manager.is_task_running(task_id):
        print(f"任务 {task_id} 已在运行，跳过执行。")
        return
    
    task_manager.add_task(task_id, asyncio.current_task())

    print(f"添加任务到task manager {task_id}...")

    # 确定用户列表
    if user_group_id:
        # 获取用户组中的所有用户
        users = fetch_user_group_members_by_id(user_group_id)

    elif user_id:
        # 单个用户任务
        user = fetch_user_by_id(user_id)
        users = [user] if user else []
    else:
        print(f"Task {task_id} 无法找到用户信息，跳过。")
        return

    # 遍历用户列表，上传视频
    for user in users:
        user_id, platform, username, login_info = user
        print(f"处理用户 {username}({platform}) 的任务 {task_id}...")

        try:
            storage_state = json.loads(login_info)  # 假设 login_info 存储的是 JSON 格式的 Cookie 字符串
            config = load_config()
            headless_mode = config.get("headless_mode", True)  # 设置一个默认值以防止异常
            chromium_path = config.get("chromium_path", "")
            
            # 使用异步 Playwright 浏览器上下文
            async with async_playwright() as p:
                # 浏览器启动参数
                launch_args = {
                    "headless": headless_mode,
                    "args": [
                        "--disable-blink-features=AutomationControlled",
                        "--disable-infobars",
                        "--disable-extensions"
                    ]
                }
                if chromium_path:
                    if not os.path.isfile(chromium_path):
                        raise FileNotFoundError(f"Chromium 可执行文件未找到：{chromium_path}")
                    launch_args["executable_path"] = chromium_path

                browser = await p.chromium.launch(**launch_args)
                context = await browser.new_context(
                    storage_state=storage_state,
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
                )
                # 这里可以传入 cookies 或自定义逻辑
                platform_module = importlib.import_module(f"platforms.{platform.lower()}")
                await platform_module.upload_video(task, context)  # 使用异步上传视频
                await browser.close()
                update_video_task_status(task[0], 2)  # 成功后更新状态
        except ModuleNotFoundError:
            print(f"平台 {platform} 不支持，跳过用户 {username} 的任务。")
            raise
        except Exception as e:
            update_video_task_status(task[0], 3)  # 失败后更新状态
            print(f"任务 {task_id} 上传到 {platform} 用户 {username} 失败：{e}")
            raise
        finally:
            print(f"任务 {task_id} 已完成。")
            task_manager.remove_task(task_id)            
# 包装器函数：从同步调用转换为异步调用
def process_task(task):
    task_obj = asyncio.create_task(process_task_async(task))
    task_obj.add_done_callback(handle_task_result)

def handle_task_result(task):
    try:
        task.result()  # 如果任务执行中有异常，会在这里抛出
    except Exception as e:
        print(f"处理任务时发生错误：{e}")    

# def process_task(task):
#     """
#     处理单个视频任务。
#     根据平台动态调用对应的 upload_video 函数。
#     """
#     task_id, video_title, video_desc, video_path, cover_path, video_tags, user_group_id, user_id, scheduled_time, status = task

#     # 确定用户列表
#     if user_group_id:
#         # 获取用户组中的所有用户
#         users = fetch_user_group_members_by_id(user_group_id)
#     elif user_id:
#         # 单个用户任务
#         user = fetch_user_by_id(user_id)
#         users = [user] if user else []
#     else:
#         print(f"Task {task_id} 无法找到用户信息，跳过。")
#         return

#     # 遍历用户列表，上传视频
#     for user in users:
#         user_id, platform, username, login_info = user
#         print(f"处理用户 {username}({platform}) 的任务 {task_id}...")

#         try:
#             storage_state = json.loads(login_info)  # 假设 login_info 存储的是 JSON 格式的 Cookie 字符串
#             config = load_config()
#             headless_mode = config.get("headless_mode", True)  # 设置一个默认值以防止异常
#             chromium_path = config.get("chromium_path", "")
#             # 使用独立的 Playwright 浏览器上下文
#             with sync_playwright() as p:
#                 # 浏览器启动参数
#                 launch_args = {
#                     "headless": headless_mode,
#                     "args": [
#                         "--disable-blink-features=AutomationControlled",
#                         "--disable-infobars",
#                         "--disable-extensions"
#                     ]
#                 }
#                 if chromium_path:
#                     if not os.path.isfile(chromium_path):
#                         raise FileNotFoundError(f"Chromium 可执行文件未找到：{chromium_path}")
#                     launch_args["executable_path"] = chromium_path
#                 browser = p.chromium.launch(launch_args)
#                 context = browser.new_context(
#                     storage_state=storage_state,
#                     user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
#                 )
#                 # 这里可以传入 cookies 或自定义逻辑
#                 platform_module = importlib.import_module(f"platforms.{platform.lower()}")
#                 platform_module.upload_video(task, context)
#                 browser.close()

#         except ModuleNotFoundError:
#             print(f"平台 {platform} 不支持，跳过用户 {username} 的任务。")
#             raise
#         except Exception as e:
#             print(f"任务 {task_id} 上传到 {platform} 用户 {username} 失败：{e}")
#             raise

def worker():
    """
    任务队列的工作线程。
    """
    while not global_stop_flag.is_set():  # 检查全局停止标志
        try:
            task = task_queue.get(timeout=1)  # 从队列中获取任务
            if task is None:
                break  # 如果队列中是 None，则退出线程
            task_id = task[0]
            print(f"[线程 {threading.current_thread().name}] 正在处理任务 {task_id}")
            update_video_task_status(task_id, 1)  # 更新任务状态为执行中
            try:
                # process_task(task)  # 执行任务
                # 创建新的事件循环并运行异步任务
                loop = asyncio.new_event_loop()  # 创建新的事件循环
                asyncio.set_event_loop(loop)  # 设置当前线程的事件循环
                loop.run_until_complete(process_task_async(task))  # 执行异步任务                
                update_video_task_status(task_id, 2)  # 更新任务状态为已完成
                print(f"任务 {task_id} 已完成。")
            except Exception as e:
                update_video_task_status(task_id, 3)  # 更新任务状态为出错
                print(f"任务 {task_id} 出现错误：{e}")
            finally:
                task_queue.task_done()  # 标记任务完成
        except queue.Empty:
            continue  # 如果队列为空，等待下一次任务

    print(f"[线程 {threading.current_thread().name}] 退出。")


def task_scheduler():
    """
    主线程任务调度器：定时检查数据库中的任务，并将其添加到队列。
    """
    print("任务调度器启动...")
    while not global_stop_flag.is_set():  # 检查全局停止标志
        try:
            print("检查未发布的任务...")
            pending_tasks = fetch_pending_video_tasks()  # 获取未执行的任务
            print(f"找到 {len(pending_tasks)} 个未发布的任务。")
            
            for task in pending_tasks:
                if global_stop_flag.is_set():  # 检查全局停止标志
                    break
                task_queue.put(task)  # 将任务加入队列
            print("任务已加入队列，等待执行。")

        except Exception as e:
            print(f"任务调度器出现错误: {e}")

        # 每隔 10 秒检查一次
        scheduler_event.wait(10)

    print("任务调度器已停止。")



class VideoTaskUI(tk.Frame):
    def __init__(self, master, app_controller):
        super().__init__(master)
        self.app_controller = app_controller
        self.loop_lock = Lock()
        self.async_loop = None
        self._start_async_loop()

    def _start_async_loop(self):
        """启动后台异步事件循环"""
        def run_async_loop():
            loop = asyncio.new_event_loop()
            with self.loop_lock:  # 确保线程安全
                self.async_loop = loop
            asyncio.set_event_loop(loop)
            loop.run_forever()

        threading.Thread(target=run_async_loop, daemon=True).start() 
    def show_video_tasks(self):
        """显示所有视频发布任务的界面"""
        main_frame = self
        tasks = []
        def refresh_tasks():
            """刷新任务列表"""
            nonlocal tasks  # 使用外层的 `tasks`
            for item in task_tree.get_children():
                task_tree.delete(item)

            tasks = fetch_all_video_tasks()
            # 状态映射表
            status_map = {
                0: "未执行",
                1: "执行中",
                2: "已完成",
                3: "出错了",
            }
            index = 0
            for task in tasks:
                index += 1
                # 获取 user 和 user_group 的名称
                user = fetch_user_by_id(task[7])
                if user:
                    user_id, platform, username, *_ = user
                    user_name = f'{username}({platform})'
                else:
                    user_name = 'None'

                user_group_data = fetch_user_group_by_id(task[6])
                user_group_name = user_group_data['group_name'] if user_group_data else "None"

                # 转换任务状态为中文描述
                task_data = list(task)
                task_data[9] = status_map.get(task_data[9], "未知状态")  # 将 status 转换为中文
                # 插入到任务表中
                task_tree.insert("", "end", values=(task_data[0], task_data[1], user_group_name, user_name, task_data[8], task_data[9]))

        def show_log():
            """显示日志"""
            log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        def hide_log():
            """隐藏日志"""
            log_frame.pack_forget()

        def start_task():
            """手动启动选中的任务"""
            selected_item = task_tree.selection()
            if not selected_item:
                messagebox.showerror("错误", "请选择一个任务")
                return

            task_id = int(task_tree.item(selected_item, "values")[0])  # 从 TreeView 获取任务 ID
            task = next((t for t in tasks if t[0] == task_id), None)  # 根据 ID 获取任务

            if not task:
                messagebox.showerror("错误", "未找到对应任务")
                return
            
            if task_manager.is_task_running(task_id):
                messagebox.showinfo("提示", "该任务已经在运行中。")
                return  
                    
            if task[9] == 0:  # 未执行 -> 执行中
                try:
                    print(f"任务 {task[0]} 已手动启动。")
                    update_video_task_status(task[0], 1)  # 更新任务状态为执行中
                    print(f"事件循环是否运行：{self.async_loop.is_running()}")
                    # 调用异步任务
                    with self.loop_lock:
                        if self.async_loop is None:
                            raise RuntimeError("异步事件循环尚未初始化")
                        # 定义任务完成后的回调函数
                        def task_done_callback(fut):
                            refresh_tasks()
                            print(f"任务 {task_id} 已完，状态更新")

                        # 提交任务到事件循环
                        def submit_task():
                            async_task = self.async_loop.create_task(process_task_async(task))
                            async_task.add_done_callback(task_done_callback)
                            print(f"任务 {task_id} 已提交到事件循环。")

                        # 安全提交任务到事件循环
                        self.async_loop.call_soon_threadsafe(submit_task)
                        
                except Exception as e:
                    # 捕获任务失败的异常并更新状态为“出错”
                    update_video_task_status(task[0], 3)
                    print(f"任务 {task[0]} 执行失败：{e}")
                    messagebox.showerror("任务执行失败", f"任务 {task_id} 执行失败，错误：{e}")
            else:
                messagebox.showinfo("提示", "该任务无法启动（状态不符合）。")

            refresh_tasks()

        def edit_video_task():
            selected_item = task_tree.selection()
            if not selected_item:
                messagebox.showerror("错误", "请选择一个任务")
                return

            task_id = int(task_tree.item(selected_item, "values")[0])  # 从 TreeView 获取任务 ID
            print(f"编辑任务 {task_id}")
            self.app_controller.show_edit_video_task(task_id)
        def stop_task():
            """手动停止选中的任务"""
            selected_item = task_tree.selection()
            if not selected_item:
                messagebox.showerror("错误", "请选择一个任务")
                return

            task_id = int(task_tree.item(selected_item, "values")[0])  # 从 TreeView 获取任务 ID
            task = next((t for t in tasks if t[0] == task_id), None)  # 根据 ID 获取任务

            if not task:
                messagebox.showerror("错误", "未找到对应任务")
                return

            if task[9] == 1:  # 执行中 -> 未执行
                try:
                    # 停止异步任务
                    with self.loop_lock:
                        if self.async_loop is None:
                            raise RuntimeError("异步事件循环尚未初始化")
                        
                        # 检查任务是否在 running_tasks 中
                        if task_manager.is_task_running(task_id):
                            running_task = task_manager.get_task_by_id(task_id)
                            try:
                                running_task.cancel()  # 尝试取消任务
                                print(f"任务 {task_id} 正在取消...")
                            except Exception as e:
                                print(f"取消任务 {task_id} 时出错：{e}")
                                raise
                            finally:
                                # 确保任务从字典中移除
                                task_manager.remove_task(task_id)
                                print(f"任务 {task_id} 已从运行列表中移除。")
                        else:
                            raise RuntimeError(f"任务 {task_id} 未在运行状态")
                        
                        print(f"任务 {task_id} 已手动停止。")
                        update_video_task_status(task_id, 0)  # 更新任务状态为已停止

                except Exception as e:
                    # 捕获任务停止失败的异常
                    print(f"任务 {task_id} 停止失败：{e}")
                    messagebox.showerror("任务停止失败", f"任务 {task_id} 停止失败，错误：{e}")
            else:
                messagebox.showinfo("提示", "该任务无法停止（状态不符合）。")

            refresh_tasks()


        # def toggle_scheduler():
        #     """启动或关闭定时任务"""
        #     global scheduler_thread, is_scheduler_running

        #     if not is_scheduler_running:
        #         # 启动定时任务
        #         is_scheduler_running = True
        #         scheduler_event.clear()  # 清除停止标志
        #         scheduler_thread = threading.Thread(target=task_scheduler, daemon=True)
        #         scheduler_thread.start()
        #         scheduler_button.config(text="关闭定时任务")
        #         print("定时任务已启动。")
        #     else:
        #         # 停止定时任务
        #         is_scheduler_running = False
        #         scheduler_event.set()  # 设置停止标志
        #         scheduler_thread = None  # 释放线程引用
        #         scheduler_button.config(text="启动定时任务")
        #         print("定时任务已关闭。")
        def toggle_scheduler():
            """
            切换调度器的运行状态：
            - 如果调度器正在运行，则停止调度器。
            - 如果调度器未运行，则启动调度器和工作线程。
            """
            global is_scheduler_running, scheduler_thread

            if is_scheduler_running:
                # 停止调度器和任务
                is_scheduler_running = False
                global_stop_flag.set()  # 设置全局停止标志
                scheduler_event.set()  # 设置停止调度标志
                while not task_queue.empty():
                    try:
                        task_queue.get_nowait()  # 清空任务队列
                        task_queue.task_done()
                    except queue.Empty:
                        break
                print("正在停止所有任务...")
                scheduler_thread.join()  # 等待调度器线程结束
                scheduler_button.config(text="开启定时任务")
                print("任务调度器已停止。")
            else:
                # 启动调度器
                is_scheduler_running = True
                global_stop_flag.clear()  # 清除全局停止标志
                scheduler_event.clear()

                # 启动调度器线程
                scheduler_thread = threading.Thread(target=task_scheduler, daemon=True)
                scheduler_thread.start()

                # 启动工作线程
                for i in range(self.config.worker_count):  # 启动多个线程
                    worker_thread = threading.Thread(target=worker, daemon=True, name=f"Worker-{i+1}")
                    worker_thread.start()
                scheduler_button.config(text="关闭定时任务")
                print("任务调度器和工作线程已启动。")

        # 标题
        tk.Label(main_frame, text="视频任务列表", font=("Arial", 16)).pack(pady=10)

        # 设置区域
        settings_frame = tk.Frame(main_frame)
        settings_frame.pack(pady=10, fill="x")

        # 新建用户
        tk.Button(settings_frame, text="新建用户组", command=self.app_controller.show_add_user_group).pack(side="right", padx=10)
        tk.Button(settings_frame, text="新建用户", command=self.app_controller.show_add_user).pack(side="right", padx=10)

        # 定义显示的列
        columns = ("id", "video_title", "user_group", "user", "scheduled_time", "status")
        column_titles = {
            "id": "ID",
            "video_title": "视频标题",
            "user_group": "用户组",
            "user": "用户",
            "scheduled_time": "预约时间",
            "status": "状态",
        }

        # 创建 Treeview 控件
        task_tree = ttk.Treeview(main_frame, columns=columns, show="headings")

        for col in columns:
            task_tree.heading(col, text=column_titles[col])  # 设置列标题为中文
            task_tree.column(col, width=120, anchor="center")  # 设置列宽和对齐方式

        task_tree.pack(fill="both", expand=True)

        # 日志区域
        log_frame = tk.Frame(main_frame)
        log_frame.pack(pady=10, fill="both", expand=True)

        tk.Label(log_frame, text="任务日志", font=("Arial", 12)).pack(anchor="w", padx=10)
        log_text = tk.Text(log_frame, height=10, state="normal")
        log_text.pack(fill="both", expand=True, padx=10, pady=5)
        # 默认隐藏日志区域
        # log_frame.pack_forget()
        # 定义日志功能
        sys.stdout = Logger(log_text)  # 重定向标准输出

        # 按钮区域
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=10, fill="x")

        # 手动启动任务按钮
        tk.Button(button_frame, text="开始任务", command=start_task).pack(side="left", padx=5)
        # 手动停止任务按钮
        tk.Button(button_frame, text="停止任务", command=stop_task).pack(side="left", padx=5)

        # 定时任务控制按钮
        scheduler_button = tk.Button(button_frame, text="启动定时任务", command=toggle_scheduler)
        scheduler_button.pack(side="left", padx=5)

        
        # 返回主页按钮
        tk.Button(button_frame, text="返回主页", command=self.app_controller.show_main_menu).pack(side="right", padx=5)
        tk.Button(button_frame, text="刷新", command=refresh_tasks).pack(side="right", padx=5)
        tk.Button(button_frame, text="修改任务", command=edit_video_task).pack(side="right", padx=5)
        tk.Button(button_frame, text="新建任务", command=self.app_controller.show_create_video_task).pack(side="right", padx=5)

        # 初始化任务列表
        refresh_tasks()
    def show_create_video_task(self):
        """显示创建视频发布任务界面"""
        main_frame = self
        # 获取用户和用户组
        users = fetch_all_users()  # [{'id': 1, 'platform': '...', 'username': '...', 'login_info': '...'}, ...]
        user_groups = fetch_all_user_groups()  # [{'id': 1, 'group_name': '...'}, ...]

        # 映射用户的 label -> value
        user_map = {f"{user[2]}({user[1]})": user[0] for user in users}  # 用户名为键，用户 ID 为值
        user_labels = list(user_map.keys())  # 用户名标签列表

        user_group_map = {group[1]: group[0] for group in user_groups}  # 用户组名为键，用户组 ID 为值
        user_group_labels = list(user_group_map.keys())  # 用户组名列表

        # 用户与用户组的选择
        selection_var = tk.StringVar(value="user")  # 默认选择用户

        # 标题
        tk.Label(main_frame, text="创建视频发布任务", font=("Arial", 16)).pack(pady=10)

        # 创建表单区域
        form_frame = tk.Frame(main_frame)
        form_frame.pack(pady=10, padx=20)

        # 视频标题
        tk.Label(form_frame, text="视频标题:", anchor="w", width=15).grid(row=0, column=0, pady=5, sticky="w")
        title_entry = tk.Entry(form_frame, width=50)
        title_entry.grid(row=0, column=1, pady=5, sticky="ew")

        # 视频文件路径
        tk.Label(form_frame, text="视频文件路径:").grid(row=1, column=0, sticky="w", pady=5)
        video_path_entry = tk.Entry(form_frame, width=50)
        video_path_entry.grid(row=1, column=1, pady=5)

        # 视频封面路径
        tk.Label(form_frame, text="视频封面路径:", anchor="w", width=15).grid(row=2, column=0, pady=5, sticky="w")
        cover_path_entry = tk.Entry(form_frame, width=50)
        cover_path_entry.grid(row=2, column=1, pady=5)

        # 视频标签
        tk.Label(form_frame, text="视频标签 (逗号分隔):").grid(row=3, column=0, sticky="w", pady=5)
        tags_entry = tk.Entry(form_frame, width=50)
        tags_entry.grid(row=3, column=1, pady=5)

        # 视频简介
        tk.Label(form_frame, text="视频简介:", anchor="w", width=15).grid(row=4, column=0, pady=5, sticky="w")
        description_textarea = tk.Text(form_frame, height=5, width=30)
        description_textarea.grid(row=4, column=1, pady=5, sticky="ew")

        # 用户或用户组选择
        tk.Label(form_frame, text="选择用户或用户组:").grid(row=5, column=0, sticky="nw", pady=5)
        selection_var = tk.StringVar(value="user")  # 默认值为用户
        user_radio = tk.Radiobutton(form_frame, text="用户", variable=selection_var, value="user", command=lambda: toggle_selection())
        user_group_radio = tk.Radiobutton(form_frame, text="用户组", variable=selection_var, value="user_group", command=lambda: toggle_selection())
        user_radio.grid(row=5, column=1, sticky="w")
        user_group_radio.grid(row=5, column=2, sticky="w")

        # 用户下拉框
        user_frame = tk.Frame(form_frame)
        user_frame.grid(row=6, column=1, pady=5)
        user_combobox = ttk.Combobox(user_frame, state="readonly", width=30, values=user_labels)
        user_combobox.pack(side="left")
        tk.Button(user_frame, text="新建用户", command=self.app_controller.show_add_user).pack(side="left")

        # 用户组下拉框（默认隐藏）
        user_group_frame = tk.Frame(form_frame)
        user_group_frame.grid(row=6, column=1, pady=5)
        user_group_combobox = ttk.Combobox(user_group_frame, state="readonly", width=30, values=user_group_labels)
        user_group_combobox.pack(side="left")
        tk.Button(user_group_frame, text="新建用户组", command=self.app_controller.show_add_user_group).pack(side="left")
        user_group_frame.grid_remove()

        # 切换显示逻辑
        def toggle_selection():
            if selection_var.get() == "user":
                user_frame.grid()
                user_group_frame.grid_remove()
            else:
                user_frame.grid_remove()
                user_group_frame.grid()

        # 预约发布时间
        tk.Label(form_frame, text="预约发布时间:", anchor="w", width=15).grid(row=7, column=0, pady=5, sticky="w")
        # 当前日期和时间
        now = datetime.datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_hour = now.strftime("%H")  # 小时（两位数）
        current_minute = now.strftime("%M")  # 分钟（两位数）
        # 日期输入框
        date_entry = tk.Entry(form_frame, width=20)
        date_entry.insert(0, current_date)  # 默认值为当前日期
        date_entry.grid(row=7, column=1, pady=5, sticky="w")

        # 小时选择器
        tk.Label(form_frame, text="小时:").grid(row=7, column=2, pady=5, sticky="w")
        hour_entry = ttk.Combobox(form_frame, width=5, values=[f"{i:02}" for i in range(24)], state="readonly")
        hour_entry.set(current_hour)  # 默认值为当前小时
        hour_entry.grid(row=7, column=3, pady=5, padx=(0, 5))

        # 分钟选择器
        tk.Label(form_frame, text="分钟:").grid(row=7, column=4, pady=5, sticky="w")
        minute_entry = ttk.Combobox(form_frame, width=5, values=[f"{i:02}" for i in range(60)], state="readonly")
        minute_entry.set(current_minute)  # 默认值为当前分钟
        minute_entry.grid(row=7, column=5, pady=5)

        # 底部按钮区域
        bottom_frame = tk.Frame(main_frame)
        bottom_frame.pack(pady=10)

        def save_task():
            video_title = title_entry.get()
            video_desc = description_textarea.get("1.0", "end").strip()
            video_path = video_path_entry.get()
            cover_path = cover_path_entry.get()
            video_tags = tags_entry.get()
            scheduled_date = date_entry.get()
            scheduled_hour = hour_entry.get()
            scheduled_minute = minute_entry.get()

            if not video_title or not video_path or not scheduled_date or not scheduled_hour or not scheduled_minute:
                messagebox.showerror("错误", "请填写所有必填字段")
                return

            # 根据选择获取值
            if selection_var.get() == "user":
                selected_label = user_combobox.get()
                if not selected_label:
                    messagebox.showerror("错误", "请选择一个用户")
                    return
                selected_value = user_map[selected_label]  # 获取用户 ID
                user_group_id = None
                user_id = selected_value
            else:
                selected_label = user_group_combobox.get()
                if not selected_label:
                    messagebox.showerror("错误", "请选择一个用户组")
                    return
                selected_value = user_group_map[selected_label]  # 获取用户组 ID
                user_group_id = selected_value
                user_id = None
            
            # 拼接完整的预约时间
            scheduled_time = f"{scheduled_date} {scheduled_hour}:{scheduled_minute}:00"
            add_video_task(
                video_title= video_title,video_desc= video_desc,video_path= video_path,cover_path= cover_path,video_tags= video_tags,
                user_group_id= user_group_id,user_id= user_id,scheduled_time=
                f"{scheduled_time}"
            )

            messagebox.showinfo("成功", "视频任务已创建")
            self.app_controller.show_video_tasks()

        tk.Button(bottom_frame, text="创建任务", width=20, height=2, command=save_task).pack(side="left", padx=10)
        tk.Button(bottom_frame, text="返回", width=20, height=2, command=self.app_controller.show_main_menu).pack(side="left", padx=10)
    def show_edit_video_task(self, task_id):
        """显示修改视频发布任务的界面"""
        main_frame = self

        # 从数据库中获取任务信息
        task = fetch_video_task_by_id(task_id)
        if not task:
            messagebox.showerror("错误", "未找到该任务")
            self.app_controller.show_video_tasks()
            return

        # 解包任务信息
        task_id, video_title, video_desc, video_path, cover_path, video_tags, user_group_id, user_id, scheduled_time, status = task

        # 获取用户和用户组信息
        users = fetch_all_users()
        user_groups = fetch_all_user_groups()

        # 映射用户的 label -> value
        user_map = {f"{user[2]}({user[1]})": user[0] for user in users}
        user_labels = list(user_map.keys())

        user_group_map = {group[1]: group[0] for group in user_groups}  # 用户组名为键，用户组 ID 为值
        user_group_labels = list(user_group_map.keys())

        # 用户与用户组的选择
        selection_var = tk.StringVar(value="user" if user_id else "user_group")

        # 标题
        tk.Label(main_frame, text="修改视频发布任务", font=("Arial", 16)).pack(pady=10)

        # 创建表单区域
        form_frame = tk.Frame(main_frame)
        form_frame.pack(pady=10, padx=20)

        # 视频标题
        tk.Label(form_frame, text="视频标题:", anchor="w", width=15).grid(row=0, column=0, pady=5, sticky="w")
        title_entry = tk.Entry(form_frame, width=50)
        title_entry.insert(0, video_title)
        title_entry.grid(row=0, column=1, pady=5, sticky="ew")

        # 视频文件路径
        tk.Label(form_frame, text="视频文件路径:").grid(row=1, column=0, sticky="w", pady=5)
        video_path_entry = tk.Entry(form_frame, width=50)
        video_path_entry.insert(0, video_path)
        video_path_entry.grid(row=1, column=1, pady=5)

        # 视频封面路径
        tk.Label(form_frame, text="视频封面路径:", anchor="w", width=15).grid(row=2, column=0, pady=5, sticky="w")
        cover_path_entry = tk.Entry(form_frame, width=50)
        cover_path_entry.insert(0, cover_path)
        cover_path_entry.grid(row=2, column=1, pady=5)

        # 视频标签
        tk.Label(form_frame, text="视频标签 (逗号分隔):").grid(row=3, column=0, sticky="w", pady=5)
        tags_entry = tk.Entry(form_frame, width=50)
        tags_entry.insert(0, video_tags)
        tags_entry.grid(row=3, column=1, pady=5)

        # 视频简介
        tk.Label(form_frame, text="视频简介:", anchor="w", width=15).grid(row=4, column=0, pady=5, sticky="w")
        description_textarea = tk.Text(form_frame, height=5, width=30)
        description_textarea.insert("1.0", video_desc)
        description_textarea.grid(row=4, column=1, pady=5, sticky="ew")

        # 用户或用户组选择
        tk.Label(form_frame, text="选择用户或用户组:").grid(row=5, column=0, sticky="nw", pady=5)
        user_radio = tk.Radiobutton(form_frame, text="用户", variable=selection_var, value="user", command=lambda: toggle_selection())
        user_group_radio = tk.Radiobutton(form_frame, text="用户组", variable=selection_var, value="user_group", command=lambda: toggle_selection())
        user_radio.grid(row=5, column=1, sticky="w")
        user_group_radio.grid(row=5, column=2, sticky="w")

        # 用户下拉框
        user_frame = tk.Frame(form_frame)
        user_frame.grid(row=6, column=1, pady=5)
        user_combobox = ttk.Combobox(user_frame, state="readonly", width=30, values=user_labels)
        if user_id:
            selected_user_label = next((label for label, id_ in user_map.items() if id_ == user_id), None)
            user_combobox.set(selected_user_label)
        user_combobox.pack(side="left")
        tk.Button(user_frame, text="新建用户", command=self.app_controller.show_add_user).pack(side="left")

        # 用户组下拉框（默认隐藏）
        user_group_frame = tk.Frame(form_frame)
        user_group_frame.grid(row=6, column=1, pady=5)
        user_group_combobox = ttk.Combobox(user_group_frame, state="readonly", width=30, values=user_group_labels)
        if user_group_id:
            selected_user_group_label = next((label for label, id_ in user_group_map.items() if id_ == user_group_id), None)
            user_group_combobox.set(selected_user_group_label)
        user_group_combobox.pack(side="left")
        tk.Button(user_group_frame, text="新建用户组", command=self.app_controller.show_add_user_group).pack(side="left")
        if user_id:
            user_group_frame.grid_remove()

        # 切换显示逻辑
        def toggle_selection():
            if selection_var.get() == "user":
                user_frame.grid()
                user_group_frame.grid_remove()
            else:
                user_frame.grid_remove()
                user_group_frame.grid()

        # 任务状态编辑
        status_map = {0: "未执行", 1: "执行中", 2: "已完成", 3: "出错了"}
        status_reverse_map = {v: k for k, v in status_map.items()}
        tk.Label(form_frame, text="任务状态:", anchor="w", width=15).grid(row=7, column=0, pady=5, sticky="w")
        status_combobox = ttk.Combobox(form_frame, state="readonly", values=list(status_map.values()), width=30)
        status_combobox.set(status_map.get(status, "未知状态"))
        status_combobox.grid(row=7, column=1, pady=5, sticky="w")

        # 底部按钮区域
        bottom_frame = tk.Frame(main_frame)
        bottom_frame.pack(pady=10)

        def save_task():
            """保存修改后的任务"""
            new_video_title = title_entry.get()
            new_video_desc = description_textarea.get("1.0", "end").strip()
            new_video_path = video_path_entry.get()
            new_cover_path = cover_path_entry.get()
            new_video_tags = tags_entry.get()
            new_status = status_reverse_map.get(status_combobox.get(), status)

            # 获取选择的用户或用户组
            if selection_var.get() == "user":
                selected_label = user_combobox.get()
                if not selected_label:
                    messagebox.showerror("错误", "请选择一个用户")
                    return
                selected_user_id = user_map.get(selected_label)
                selected_user_group_id = None
            else:
                selected_label = user_group_combobox.get()
                if not selected_label:
                    messagebox.showerror("错误", "请选择一个用户组")
                    return
                selected_user_group_id = user_group_map.get(selected_label)
                selected_user_id = None

            # 更新任务
            update_video_task(
                task_id,
                new_video_title,
                new_video_desc,
                new_video_path,
                new_cover_path,
                new_video_tags,
                selected_user_group_id,
                selected_user_id,
                scheduled_time,
                new_status,
            )
            print('新状态',new_status)

            messagebox.showinfo("成功", "任务已更新")
            self.app_controller.show_video_tasks()

        tk.Button(bottom_frame, text="保存修改", width=20, height=2, command=save_task).pack(side="left", padx=10)
        tk.Button(bottom_frame, text="返回", width=20, height=2, command=self.app_controller.show_video_tasks).pack(side="left", padx=10)
