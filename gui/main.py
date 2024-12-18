import tkinter as tk
from tkinter import ttk, messagebox, Text
from playwright.sync_api import sync_playwright
from database import initialize_database,fetch_all_users, add_user,update_user, delete_user_by_id,fetch_user_by_id
from database import update_user_group, add_user_group, update_user_group, fetch_all_user_groups,fetch_user_group_members_by_id, fetch_group_members,delete_user_group,  fetch_user_group_by_id
from database import add_video_task, delete_video_task, fetch_all_video_tasks, fetch_video_task_by_id, update_video_task_status, fetch_pending_video_tasks
import time
import datetime
import threading
import importlib
def save_user(platform, username, login_info):
    """保存用户逻辑，调用数据库操作函数"""
    # 检查输入是否完整
    if not platform or not username or not login_info:
        messagebox.showwarning("警告", "请确保所有信息已填写完整！")
        return

    try:
        # 调用数据库操作函数
        add_user(platform, username, login_info)
        # 保存成功提示
        messagebox.showinfo("保存成功", "用户信息已成功保存！")
    except Exception as e:
        messagebox.showerror("错误", str(e))


# 定义按钮颜色字典
COLORS = {
    "default": "#dcdcdc",  # 默认颜色（灰色）
    "primary": "#4CAF50",  # 主按钮颜色（绿色）
    "success": "#28a745",  # 成功按钮颜色（绿色）
    "info": "#17a2b8",     # 信息按钮颜色（蓝色）
    "danger": "#dc3545",   # 危险按钮颜色（红色）
    "warning": "#ffc107",  # 警告按钮颜色（黄色）
    "light": "#f8f9fa",    # 亮色按钮颜色（浅灰色）
    "dark": "#343a40"      # 黑色按钮颜色
}

def create_button(parent, text, btn_type="default", command=None):
    """根据按钮类型设置不同的样式"""
    # 设置颜色字典
    colors = {
        "default": {"bg": "#e0e0e0", "fg": "#000000", "hover_bg": "#d6d6d6", "relief": "raised"},  # 灰色
        "primary": {"bg": "#0d6efd", "fg": "#ffffff", "hover_bg": "#0a58ca", "relief": "raised"},  # 蓝色
        "success": {"bg": "#198754", "fg": "#ffffff", "hover_bg": "#146c43", "relief": "raised"},  # 绿色
        "info": {"bg": "#0dcaf0", "fg": "#ffffff", "hover_bg": "#0aa2c0", "relief": "raised"},    # 天蓝色
        "danger": {"bg": "#dc3545", "fg": "#ffffff", "hover_bg": "#b02a37", "relief": "raised"},  # 红色
    }

    # 获取按钮类型对应的颜色
    button_style = colors.get(btn_type, colors["default"])

    # 创建按钮
    button = tk.Button(
        parent, 
        text=text, 
        bg=button_style["bg"], 
        fg=button_style["fg"], 
        relief=button_style["relief"], 
        padx=10, pady=5, 
        command=command
    )

    # 定义悬停效果
    def on_enter(event):
        button.config(bg=button_style["hover_bg"])

    def on_leave(event):
        button.config(bg=button_style["bg"])

    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)

    return button


# 打开对应平台的登录页面
def open_login_page(platform, get_login_button, save_cookie_button, browser_dict):
    login_urls = {
        "Bilibili": "https://www.bilibili.com",
        "Toutiao": "https://www.toutiao.com",
        "Douyin": "https://www.douyin.com",
        "YouTube": "https://www.youtube.com",
        "TikTok": "https://www.tiktok.com"
    }

    if platform not in login_urls:
        messagebox.showerror("错误", f"不支持的平台：{platform}")
        return

    login_url = login_urls[platform]

    try:
        # 启动 Playwright 浏览器
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=False, args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--disable-extensions"
        ])
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        # 修改 navigator.webdriver 属性
        page.evaluate("() => { Object.defineProperty(navigator, 'webdriver', { get: () => undefined }) }")

        page.goto(login_url)

        # 暂存浏览器对象
        browser_dict["playwright"] = playwright
        browser_dict["browser"] = browser
        browser_dict["page"] = page

        # 切换按钮状态
        get_login_button.config(state="disabled", text="更新登录信息")
        save_cookie_button.config(state="normal")
    except Exception as e:
        messagebox.showerror("错误", f"无法打开登录页面：{e}")

# 保存 Cookie 信息并关闭浏览器
def save_cookies(browser_dict, save_cookie_button, get_login_button, username_entry, cookie_textarea):
    try:
        if "page" in browser_dict:
            page = browser_dict["page"]
            cookies = page.context.cookies()
            username_entry.login_info = str(cookies)  # 暂存登录信息
            # 关闭浏览器
            browser_dict["browser"].close()
            browser_dict["playwright"].stop()
            # 清除浏览器对象
            browser_dict.clear()

            # 切换按钮状态
            save_cookie_button.config(state="disabled")
            get_login_button.config(state="normal")
            messagebox.showinfo("成功", "Cookies 已成功保存！")

            # 更新 TextArea 的内容
            cookie_textarea.config(state="normal")  # 解锁 Text 框
            cookie_textarea.delete("1.0", "end")    # 清空内容
            cookie_textarea.insert("1.0", cookies) # 插入 Cookie 数据
            cookie_textarea.config(state="disabled")  # 设置为只读
    except Exception as e:
        messagebox.showerror("错误", f"保存 Cookies 时出错：{e}")

def custom_entry(parent):
    """创建带黑色边框、白色背景的圆角输入框"""
    style = ttk.Style()
    style.configure("Custom.TEntry", 
                    bordercolor="black", 
                    relief="flat", 
                    background="white",
                    padding=5)
    
    entry = ttk.Entry(parent, style="Custom.TEntry")
    return entry


# Tkinter 界面功能
def show_main_menu():
    """显示主界面，提供中文的三个功能按钮"""
    # show_video_tasks()
    clear_frame()
    tk.Label(main_frame, text="主界面", font=("Arial", 16)).pack(pady=20)
    tk.Button(main_frame, text="发布视频", command=show_create_video_task, width=20, height=2).pack(pady=10)
    tk.Button(main_frame, text="查看任务", command=show_video_tasks, width=20, height=2).pack(pady=10)
    tk.Button(main_frame, text="用户列表", command=show_user_list, width=20, height=2).pack(pady=10)
    tk.Button(main_frame, text="用户组", command=show_user_groups, width=20, height=2).pack(pady=10)

def show_video_tasks():
    """显示所有视频发布任务的界面"""
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

        if task[9] == 0:  # 未执行 -> 执行中
            update_video_task_status(task[0], 1)  # 更新任务状态为执行中
            process_task(task)  # 执行任务逻辑
            print(f"任务 {task[0]} 已手动启动。")
        else:
            messagebox.showinfo("提示", "该任务无法启动（状态不符合）。")

        refresh_tasks()


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
            update_video_task_status(task[0], 0)  # 更新任务状态为未执行
            print(f"任务 {task[0]} 已手动停止。")
        else:
            messagebox.showinfo("提示", "该任务无法停止（状态不符合）。")

        refresh_tasks()


    def toggle_scheduler():
        """启动或关闭定时任务"""
        global scheduler_thread, is_scheduler_running

        if not is_scheduler_running:
            # 启动定时任务
            is_scheduler_running = True
            scheduler_event.clear()  # 清除停止标志
            scheduler_thread = threading.Thread(target=task_scheduler, daemon=True)
            scheduler_thread.start()
            scheduler_button.config(text="关闭定时任务")
            print("定时任务已启动。")
        else:
            # 停止定时任务
            is_scheduler_running = False
            scheduler_event.set()  # 设置停止标志
            scheduler_thread = None  # 释放线程引用
            scheduler_button.config(text="启动定时任务")
            print("定时任务已关闭。")

    clear_frame()
    # 标题
    tk.Label(main_frame, text="视频任务列表", font=("Arial", 16)).pack(pady=10)

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

    # 按钮区域
    button_frame = tk.Frame(main_frame)
    button_frame.pack(pady=10, fill="x")

    # 手动启动任务按钮
    tk.Button(button_frame, text="手动启动任务", command=start_task).pack(side="left", padx=5)
    # 手动停止任务按钮
    tk.Button(button_frame, text="手动停止任务", command=stop_task).pack(side="left", padx=5)

    # 定时任务控制按钮
    scheduler_button = tk.Button(button_frame, text="启动定时任务", command=toggle_scheduler)
    scheduler_button.pack(side="left", padx=5)


    # 返回主页按钮
    tk.Button(button_frame, text="返回主页", command=show_main_menu).pack(side="right", padx=5)
    tk.Button(button_frame, text="刷新", command=refresh_tasks).pack(side="right", padx=5)
    tk.Button(button_frame, text="新建任务", command=show_create_video_task).pack(side="right", padx=5)

    # 初始化任务列表
    refresh_tasks()


def show_create_video_task():
    """显示创建视频发布任务界面"""
    clear_frame()
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
    title_entry = custom_entry(form_frame)
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
    tk.Button(user_frame, text="新建用户", command=show_add_user).pack(side="left")

    # 用户组下拉框（默认隐藏）
    user_group_frame = tk.Frame(form_frame)
    user_group_frame.grid(row=6, column=1, pady=5)
    user_group_combobox = ttk.Combobox(user_group_frame, state="readonly", width=30, values=user_group_labels)
    user_group_combobox.pack(side="left")
    tk.Button(user_group_frame, text="新建用户组", command=show_add_user_group).pack(side="left")
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
        show_video_tasks()

    tk.Button(bottom_frame, text="创建任务", width=20, height=2, command=save_task).pack(side="left", padx=10)
    tk.Button(bottom_frame, text="返回", width=20, height=2, command=show_main_menu).pack(side="left", padx=10)

def show_user_groups():
    """用户组管理界面"""
    clear_frame()
    tk.Label(main_frame, text="用户组管理", font=("Arial", 16)).pack(pady=10)

    # 用户组列表区域
    group_frame = tk.Frame(main_frame)
    group_frame.pack(pady=10, fill="x")

    columns = ("ID","组名", "用户数量")
    group_tree = ttk.Treeview(group_frame, columns=columns, show="headings")
    group_tree.heading("ID", text="ID")
    group_tree.heading("组名", text="组名")
    group_tree.heading("用户数量", text="用户数量")
    # 获取所有用户组并填充列表
    groups = fetch_all_user_groups()
    for group in groups:
        group_id, group_name = group
        members = fetch_group_members(group_id)
        # 将成员的用户名提取为字符串
        members_str = ", ".join([f"{member[2]}({member[1]})" for member in members])  # 假设第2列是用户名
        group_tree.insert("", "end", values=(group_id, group_name, members_str))

    group_tree.pack(fill="both", expand=True)

    # 按钮功能
    def add_group():
        show_add_user_group()

    def edit_group():
        selected_item = group_tree.selection()
        if not selected_item:
            messagebox.showwarning("警告", "请选择一个用户组进行编辑！")
            return
        group_id = group_tree.item(selected_item, "values")[0]  # 假设第0列是组ID
        show_edit_user_group(group_id)

    def delete_group():
        selected_item = group_tree.selection()
        if not selected_item:
            messagebox.showwarning("警告", "请选择一个用户组进行删除！")
            return
        group_id = group_tree.item(selected_item, "values")[0]  # 假设第0列是组ID
        if messagebox.askyesno("确认", "确定删除该用户组吗？"):
            delete_user_group(group_id)
            show_user_groups()

    # 底部按钮区域
    bottom_frame = tk.Frame(main_frame)
    bottom_frame.pack(pady=10)

    create_button(bottom_frame, "添加用户组", "default", command=add_group).pack(side="left", padx=10)
    create_button(bottom_frame, "编辑用户组", "default", command=edit_group).pack(side="left", padx=10)
    create_button(bottom_frame, "删除用户组", "default", command=delete_group).pack(side="left", padx=10)
    create_button(bottom_frame, "返回主菜单", "default", command=show_main_menu).pack(side="left", padx=10)
def show_add_user_group():
    """显示添加用户组界面"""
    clear_frame()
    tk.Label(main_frame, text="添加用户组", font=("Arial", 16)).pack(pady=10)

    # 用户组表单
    form_frame = tk.Frame(main_frame)
    form_frame.pack(pady=10, padx=20)

    # 用户组名称输入
    tk.Label(form_frame, text="用户组名称:", anchor="w", width=15).grid(row=0, column=0, pady=5, sticky="w")
    group_name_entry = custom_entry(form_frame)
    group_name_entry.grid(row=0, column=1, pady=5, sticky="ew")

    # 用户多选框
    tk.Label(form_frame, text="选择用户:", anchor="w", width=15).grid(row=1, column=0, pady=5, sticky="w")
    users_listbox = tk.Listbox(form_frame, selectmode="multiple", height=10, width=30)
    users_listbox.grid(row=1, column=1, pady=5, sticky="ew")

    # 加载用户数据
    users = fetch_all_users()
    for user in users:
        user_id, platform, username, *_ = user
        users_listbox.insert(tk.END, f"{username} ({platform})")

    # 底部按钮区域
    bottom_frame = tk.Frame(main_frame)
    bottom_frame.pack(pady=10)

    # 保存用户组按钮
    create_button(
        bottom_frame, "创建用户组",
        "default",
        command=lambda: add_user_group_and_refresh(group_name_entry, users_listbox, users)
    ).pack(side="left", padx=10)

    # 返回按钮
    create_button(
        bottom_frame, "返回",
        "default",
        command=show_user_groups
    ).pack(side="left", padx=10)


def add_user_group_and_refresh(group_name_entry, users_listbox, users):
    """保存用户组并刷新界面"""
    group_name = group_name_entry.get().strip()
    selected_indices = users_listbox.curselection()
    selected_users = [users[i][0] for i in selected_indices]  # 获取选中用户的ID

    if not group_name:
        messagebox.showerror("错误", "用户组名称不能为空")
        return
    if not selected_users:
        messagebox.showerror("错误", "至少选择一个用户")
        return

    add_user_group(group_name, selected_users)  # 保存到数据库
    messagebox.showinfo("成功", f"用户组 '{group_name}' 已保存")
    show_user_groups()  # 返回user groups 界面


def show_edit_user_group(group_id):
    """编辑用户组界面"""
    clear_frame()
    tk.Label(main_frame, text="编辑用户组", font=("Arial", 16)).pack(pady=10)

    # 获取用户组信息
    group = fetch_user_group_by_id(group_id)
    if not group:
        messagebox.showerror("错误", "用户组不存在")
        show_user_groups()
        return

    group_name = group['group_name']
    members = group['members']
    users = [user_id for user_id, _, _ in members]
    # 表单区域
    form_frame = tk.Frame(main_frame)
    form_frame.pack(pady=10, padx=20)

    tk.Label(form_frame, text="组名:", anchor="w", width=15).grid(row=0, column=0, pady=5, sticky="w")
    group_name_entry = custom_entry(form_frame)
    group_name_entry.grid(row=0, column=1, pady=5, sticky="ew")
    group_name_entry.insert(0, group_name)

    tk.Label(form_frame, text="用户选择:", anchor="w", width=15).grid(row=1, column=0, pady=5, sticky="nw")
    users_listbox = tk.Listbox(form_frame, selectmode="multiple", height=10, width=30)
    users_listbox.grid(row=1, column=1, pady=5, sticky="ew")

    all_users = fetch_all_users()
    for user in all_users:
        user_id, platform, username, *_ = user
        users_listbox.insert("end", f"{username} ({platform})")
        if user_id in users:
            # 查找 user_id 对应的索引
            index = next((i for i, u in enumerate(all_users) if u[0] == user_id), None)
            if index is not None:
                users_listbox.selection_set(index)

    # 保存编辑后的用户组
    def save_edited_group(group_id,group_name_entry, users_listbox, users):
        new_group_name = group_name_entry.get().strip()
        selected_indices = users_listbox.curselection()
        selected_users = [users[i][0] for i in selected_indices]  # 获取选中用户的ID
        if not new_group_name:
            messagebox.showwarning("警告", "组名不能为空！")
            return
        if not selected_users:
            messagebox.showwarning("警告", "请至少选择一个用户！")
            return
        print('更新group',group_id,new_group_name,selected_users)
        update_user_group(group_id, new_group_name, selected_users)
        messagebox.showinfo("成功", "用户组已更新")
        show_user_groups()

    # 底部按钮区域
    bottom_frame = tk.Frame(main_frame)
    bottom_frame.pack(pady=10)

    create_button(bottom_frame, "保存", "default", command=lambda: save_edited_group(group_id,group_name_entry, users_listbox, all_users)).pack(side="left", padx=10)
    create_button(bottom_frame, "返回", "default", command=show_user_groups).pack(side="left", padx=10)

def show_add_user():
    """显示添加用户功能界面"""
    clear_frame()
    tk.Label(main_frame, text="添加用户", font=("Arial", 16)).grid(row=0, column=0, pady=10, columnspan=2)
    
    # 使用 Frame 布局表单
    form_frame = tk.Frame(main_frame)
    form_frame.grid(row=1, column=0, pady=10, padx=20, columnspan=2)

    # 用户平台选择
    tk.Label(form_frame, text="用户平台:", anchor="w", width=15).grid(row=0, column=0, pady=5, sticky="w")
    platform_combo = ttk.Combobox(form_frame, values=["Bilibili", "Toutiao", "Douyin", "YouTube", "TikTok"])
    platform_combo.grid(row=0, column=1, pady=5, sticky="ew")
    platform_combo.set("YouTube")  # 默认选择 YouTube

    # 用户名称输入框
    tk.Label(form_frame, text="用户名称:", anchor="w", width=15).grid(row=1, column=0, pady=5, sticky="w")
    username_entry = custom_entry(form_frame)
    username_entry.grid(row=1, column=1, pady=5, sticky="ew")

    # Cookie 显示框
    tk.Label(form_frame, text="Cookie 信息:", anchor="w", width=15).grid(row=2, column=0, pady=5, sticky="w")
    cookie_textarea = Text(form_frame, height=10, width=50, wrap="word", state="normal")
    cookie_textarea.grid(row=2, column=1, pady=5, sticky="ew")

    # 按钮状态管理
    browser_dict = {}

    # 获取登录信息按钮
    get_login_button = tk.Button(form_frame, text="获取登录信息", 
                                  command=lambda: open_login_page(platform_combo.get(), get_login_button, save_cookie_button, browser_dict))
    get_login_button.grid(row=3, column=0, pady=10, padx=10)

    # 保存 Cookie 按钮
    save_cookie_button = tk.Button(form_frame, text="保存 Cookie", state="disabled",
                                    command=lambda: save_cookies(browser_dict, save_cookie_button, get_login_button, username_entry, cookie_textarea))
    save_cookie_button.grid(row=3, column=1, pady=10, padx=10)

    # 底部按钮区域
    bottom_button_frame = tk.Frame(main_frame)
    bottom_button_frame.grid(row=4, column=0, pady=10, columnspan=2)

    # 保存用户按钮
    create_button(
        bottom_button_frame, "保存用户", "default",
        command=lambda: save_user(platform_combo.get(), username_entry.get(), cookie_textarea.get("1.0", tk.END).strip())
    ).grid(row=0, column=0, padx=10)

    # 返回发布视频界面按钮
    create_button(
        bottom_button_frame, "返回主页", "default",
        command=show_main_menu
    ).grid(row=0, column=1, padx=10)



def show_user_list():
    """显示用户列表界面"""
    def on_tree_select(event):
        """Treeview选择事件"""
        selected_item = tree.selection()  # 获取选中的行
        if selected_item:
            selected_user = tree.item(selected_item, "values")
            user_id.set(selected_user[0])  # 保存选中的用户ID
            edit_button.pack(side="left", padx=10)
            delete_button.pack(side="left", padx=10)
    def edit_user():
        """编辑选中用户"""
        uid = user_id.get()
        if uid:
            print(f"编辑用户: {uid}")
            show_edit_user(uid)

    def delete_user():
        """删除用户后刷新界面"""
        uid = user_id.get()
        if uid:
            if messagebox.askyesno("确认", f"确定要删除 ID 为 {user_id} 的用户吗？"):
                delete_user_by_id(user_id)
                messagebox.showinfo("成功", "用户已删除！")
                show_user_list()

    clear_frame()
    tk.Label(main_frame, text="用户列表", font=("Arial", 16)).pack(pady=10)

    # 从数据库中获取用户列表
    users = fetch_all_users()

    if not users:
        tk.Label(main_frame, text="没有用户信息", font=("Arial", 14)).pack(pady=10)
    else:
        # 创建 Treeview 控件
        treeview_frame = tk.Frame(main_frame)
        treeview_frame.pack(pady=10, padx=20, fill="both", expand=True)

        tree = ttk.Treeview(treeview_frame, columns=("ID", "平台", "用户名", "Cookie"), show="headings")
        tree.pack(fill="both", expand=True)

        # 设置列
        tree.heading("ID", text="ID")
        tree.heading("平台", text="平台")
        tree.heading("用户名", text="用户名")
        tree.heading("Cookie", text="Cookie")  # 设置 Cookie 列标题

        # 设置列宽
        tree.column("ID", width=50, anchor="center")
        tree.column("平台", width=100, anchor="w")
        tree.column("用户名", width=100, anchor="w")
        tree.column("Cookie", width=200, anchor="w")  # 设置 Cookie 列宽

        # 向 Treeview 中插入数据
        for user in users:
            user_id, platform, username, login_info = user  # 解包所有值，确保获取 login_info
            # 插入用户数据，包括登录信息（Cookie）
            tree.insert("", "end", values=(user_id, platform, username, login_info))


        # 创建外部按钮
        edit_button = tk.Button(main_frame, text="编辑", command=lambda: edit_user(tree.selection()[0]))
        delete_button = tk.Button(main_frame, text="删除", command=lambda: delete_user(tree.selection()[0]))

        # 绑定 Treeview 的选择事件
        tree.bind("<<TreeviewSelect>>", on_tree_select)

        # 底部按钮区域
        bottom_frame = tk.Frame(main_frame)
        bottom_frame.pack(fill="x")

        # 创建编辑和删除按钮的子区域，默认隐藏
        action_frame = tk.Frame(bottom_frame)
        action_frame.pack(side="top", padx=10, fill="x")  # 确保它在最上面

        user_id = tk.StringVar()  # 存储选中用户的ID
        edit_button = tk.Button(action_frame, text="编辑", command=edit_user)
        delete_button = tk.Button(action_frame, text="删除", command=delete_user)


        # 创建其他按钮的子区域
        other_button_frame = tk.Frame(bottom_frame)
        other_button_frame.pack(side="top", pady=5, padx=10)

        create_button(
            other_button_frame, "添加用户",
            "default",
            command=show_add_user
        ).pack(side="left", padx=10)

        create_button(
            other_button_frame, "返回主界面",
            "default",
            command=show_main_menu
        ).pack(side="left", padx=10)



def show_edit_user(user_id):
    """编辑用户信息"""
    clear_frame()
    tk.Label(main_frame, text="编辑用户", font=("Arial", 16)).grid(row=0, column=0, pady=10, columnspan=2)

    # 获取用户信息
    user = fetch_user_by_id(user_id)
    if not user:
        messagebox.showerror("错误", "用户不存在")
        show_user_list()
        return

    platform, username, login_info = user

    # 编辑表单
    form_frame = tk.Frame(main_frame)
    form_frame.grid(row=1, column=0, pady=10, padx=20, columnspan=2)

    tk.Label(form_frame, text="用户平台:", anchor="w", width=15).grid(row=0, column=0, pady=5, sticky="w")
    platform_combo = ttk.Combobox(form_frame, values=["Bilibili", "Toutiao", "Douyin", "YouTube", "TikTok"])
    platform_combo.grid(row=0, column=1, pady=5, sticky="ew")
    platform_combo.set(platform)

    tk.Label(form_frame, text="用户名称:", anchor="w", width=15).grid(row=1, column=0, pady=5, sticky="w")
    username_entry = custom_entry(form_frame)
    username_entry.grid(row=1, column=1, pady=5, sticky="ew")
    username_entry.insert(0, username)

    # Cookie 显示框
    tk.Label(form_frame, text="Cookie 信息:", anchor="w", width=15).grid(row=2, column=0, pady=5, sticky="w")
    cookie_textarea = tk.Text(form_frame, height=10, width=50, wrap="word", state="normal")
    cookie_textarea.grid(row=2, column=1, pady=5, sticky="ew")
    cookie_textarea.insert("1.0", login_info)

    # 按钮状态管理
    browser_dict = {}

    # 获取登录信息按钮
    get_login_button = tk.Button(form_frame, text="更新登录信息", 
                                  command=lambda: open_login_page(platform_combo.get(), get_login_button, save_cookie_button, browser_dict))
    get_login_button.grid(row=3, column=0, pady=10, padx=10)

    # 保存 Cookie 按钮
    save_cookie_button = tk.Button(form_frame, text="保存 Cookie", state="disabled",
                                    command=lambda: save_cookies(browser_dict, save_cookie_button, get_login_button, username_entry, cookie_textarea))
    save_cookie_button.grid(row=3, column=1, pady=10, padx=10)

    # 底部按钮区域
    bottom_frame = tk.Frame(main_frame)
    bottom_frame.grid(row=4, column=0, pady=10, columnspan=2)

    create_button(
        bottom_frame, "保存修改",
        "default",
        command=lambda: save_user_edits(
            user_id, platform_combo.get(), username_entry.get(), cookie_textarea.get("1.0", "end").strip()
        )
    ).grid(row=0, column=0, padx=10)

    create_button(
        bottom_frame, "返回用户列表",
        "default",
        command=show_user_list
    ).grid(row=0, column=1, padx=10)


def save_user_edits(user_id, platform, username, login_info):
    """保存用户的编辑内容到数据库"""
    if not platform or not username or not login_info:
        messagebox.showerror("错误", "所有字段均为必填")
        return

    update_user(user_id, platform, username, login_info)
    messagebox.showinfo("成功", "用户信息已更新")
    show_user_list()


def clear_frame():
    """清空主框架中的所有控件"""
    for widget in main_frame.winfo_children():
        widget.destroy()

def process_task(task):
    """
    处理单个视频任务。
    根据平台动态调用对应的 upload_video 函数。
    """
    task_id, video_title, video_desc, video_path, cover_path, video_tags, user_group_id, user_id, scheduled_time, status = task

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
            # 动态导入平台模块
            platform_module = importlib.import_module(f"platforms.{platform.lower()}")
            # 调用 upload_video 函数
            platform_module.upload_video(task, user)
            print(f"[成功] 任务 {task_id} 上传到平台 {platform} 用户 {username}。")

            # 成功后更新任务状态为 "已完成" (2)
            update_video_task_status(task_id, 2)

        except ModuleNotFoundError:
            print(f"平台 {platform} 不支持，跳过用户 {username} 的任务。")
        except Exception as e:
            print(f"任务 {task_id} 上传到 {platform} 用户 {username} 失败：{e}")


scheduler_thread = None  # 全局变量，存储调度器线程
scheduler_event = threading.Event()  # 全局事件，用于控制线程停止
is_scheduler_running = False  # 定时任务状态

def task_scheduler():
    """定时检查并执行未发布的任务"""
    print("任务调度器启动...")
    while not scheduler_event.is_set():  # 检查是否设置停止标志
        try:
            print("检查未发布的任务...")
            pending_tasks = fetch_pending_video_tasks()
            print(f"找到 {len(pending_tasks)} 个未发布的任务。")
            for task in pending_tasks:
                print(f"正在处理任务: {task}")
                process_task(task)  # 调用任务处理函数
        except Exception as e:
            print(f"任务调度器出现错误: {e}")
        # 每隔 10 秒检查一次
        scheduler_event.wait(10)  # 如果 `scheduler_event` 被设置，则提前退出
    print("任务调度器已停止。")

def start_scheduler():
    """启动调度器线程"""
    scheduler_thread = threading.Thread(target=task_scheduler, daemon=True)
    scheduler_thread.start()
    print("任务调度器已启动。")

def run_client():
    """初始化客户端并启动主程序"""
    # 初始化数据库
    initialize_database()

    # 创建主窗口
    root = tk.Tk()
    root.title("视频自动发布客户端")
    root.geometry("900x600")

    # 创建主框架
    global main_frame
    main_frame = tk.Frame(root)
    main_frame.pack(fill="both", expand=True)

    # 显示主界面
    show_main_menu()

    # 启动主事件循环
    root.mainloop()

if __name__ == "__main__":
    run_client()