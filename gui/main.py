import tkinter as tk
from tkinter import ttk, messagebox, Text
from playwright.sync_api import sync_playwright
import sqlite3

DB_FILE = "user_data.db"

def initialize_database():
    """初始化数据库（仅创建表结构，不影响已有数据）"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            username TEXT NOT NULL,
            login_info TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def fetch_all_users():
    """获取所有用户信息"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, platform, username,login_info FROM users")
    users = cursor.fetchall()
    conn.close()
    return users

def fetch_user_by_id(user_id):
    """根据用户 ID 获取用户信息"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT platform, username, login_info FROM users WHERE id = ?", (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    return user_data

def insert_user(platform, username, login_info):
    """插入新用户"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (platform, username, login_info) VALUES (?, ?, ?)", 
                   (platform, username, login_info))
    conn.commit()
    conn.close()

def update_user(user_id, platform, username, login_info):
    """更新用户信息"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users 
        SET platform = ?, username = ?, login_info = ?
        WHERE id = ?
    """, (platform, username, login_info, user_id))
    conn.commit()
    conn.close()

def delete_user_by_id(user_id):
    """根据用户 ID 删除用户"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    
def save_user(platform, username, login_info):
    """保存用户逻辑，调用数据库操作函数"""
    # 检查输入是否完整
    if not platform or not username or not login_info:
        messagebox.showwarning("警告", "请确保所有信息已填写完整！")
        return

    try:
        # 调用数据库操作函数
        insert_user(platform, username, login_info)
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
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()
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
    clear_frame()
    tk.Label(main_frame, text="主界面", font=("Arial", 16)).pack(pady=20)
    tk.Button(main_frame, text="发布视频", command=show_publish_video, width=20, height=2).pack(pady=10)
    tk.Button(main_frame, text="查看任务", command=show_tasks, width=20, height=2).pack(pady=10)
    tk.Button(main_frame, text="用户列表", command=show_user_list, width=20, height=2).pack(pady=10)

def show_publish_video():
    """显示发布视频功能界面，左侧显示标签，右侧显示输入框"""
    clear_frame()
    tk.Label(main_frame, text="发布视频", font=("Arial", 16)).pack(pady=10)

    # 使用 Frame 布局表单
    form_frame = tk.Frame(main_frame)
    form_frame.pack(pady=10, padx=20)

    # 视频标题
    tk.Label(form_frame, text="视频标题:", anchor="w", width=15).grid(row=0, column=0, pady=5, sticky="w")
    title_entry = custom_entry(form_frame)
    title_entry.grid(row=0, column=1, pady=5, sticky="ew")

    # 视频文件路径
    tk.Label(form_frame, text="视频文件路径:", anchor="w", width=15).grid(row=1, column=0, pady=5, sticky="w")
    video_path_entry = custom_entry(form_frame)
    video_path_entry.grid(row=1, column=1, pady=5, sticky="ew")

    # 视频封面路径
    tk.Label(form_frame, text="视频封面路径:", anchor="w", width=15).grid(row=2, column=0, pady=5, sticky="w")
    cover_path_entry = custom_entry(form_frame)
    cover_path_entry.grid(row=2, column=1, pady=5, sticky="ew")

    # 用户组选择
    tk.Label(form_frame, text="用户组:", anchor="w", width=15).grid(row=3, column=0, pady=5, sticky="w")
    user_group_combo = ttk.Combobox(form_frame, values=["组1", "组2", "组3"])
    user_group_combo.grid(row=3, column=1, pady=5, sticky="ew")

    # 添加用户按钮
    add_user_button = tk.Button(form_frame, text="添加用户", command=show_add_user)
    add_user_button.grid(row=3, column=2, padx=10, pady=5, sticky="ew")

    # 发布按钮
    publish_button = tk.Button(main_frame, text="发布", command=lambda: publish_video(
        title_entry.get(), video_path_entry.get(), cover_path_entry.get(), user_group_combo.get()))
    publish_button.pack(pady=10)

    # 返回主界面按钮
    back_button = tk.Button(main_frame, text="返回主界面", command=show_main_menu)
    back_button.pack(pady=10)


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
    cookie_textarea = Text(main_frame, height=10, width=50, wrap="word", state="normal")
    cookie_textarea.grid(row=2, column=0, pady=10, padx=20, columnspan=2)

    # 按钮状态管理
    browser_dict = {}

    # 获取登录信息按钮
    get_login_button = tk.Button(form_frame, text="获取登录信息", 
                                  command=lambda: open_login_page(platform_combo.get(), get_login_button, save_cookie_button, browser_dict))
    get_login_button.grid(row=2, column=0, pady=10, padx=10)

    # 保存 Cookie 按钮
    save_cookie_button = tk.Button(form_frame, text="保存 Cookie", state="disabled",
                                    command=lambda: save_cookies(browser_dict, save_cookie_button, get_login_button, username_entry, cookie_textarea))
    save_cookie_button.grid(row=2, column=1, pady=10, padx=10)

    # 底部按钮区域
    bottom_button_frame = tk.Frame(main_frame)
    bottom_button_frame.grid(row=3, column=0, pady=10, columnspan=2)

    # 保存用户按钮
    create_button(
        bottom_button_frame, "保存用户", "default",
        command=lambda: save_user(platform_combo.get(), username_entry.get(), cookie_textarea.get("1.0", tk.END).strip())
    ).grid(row=0, column=0, padx=10)

    # 返回发布视频界面按钮
    create_button(
        bottom_button_frame, "返回发布视频", "default",
        command=show_publish_video
    ).grid(row=0, column=1, padx=10)


def show_tasks():
    """显示任务管理功能界面"""
    clear_frame()
    tk.Label(main_frame, text="查看任务", font=("Arial", 16)).pack(pady=10)
    tk.Label(main_frame, text="这里可以显示任务列表（占位内容）").pack(pady=10)
    tk.Button(main_frame, text="返回主界面", command=show_main_menu).pack(pady=10)


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
    tk.Label(main_frame, text="编辑用户", font=("Arial", 16)).pack(pady=10)

    # 获取用户信息
    user = fetch_user_by_id(user_id)
    if not user:
        messagebox.showerror("错误", "用户不存在")
        show_user_list()
        return

    platform, username, login_info = user

    # 编辑表单
    form_frame = tk.Frame(main_frame)
    form_frame.pack(pady=10, padx=20)

    tk.Label(form_frame, text="用户平台:", anchor="w", width=15).grid(row=0, column=0, pady=5, sticky="w")
    platform_combo = ttk.Combobox(form_frame, values=["Bilibili", "Toutiao", "Douyin", "YouTube", "TikTok"])
    platform_combo.grid(row=0, column=1, pady=5, sticky="ew")
    platform_combo.set(platform)

    tk.Label(form_frame, text="用户名称:", anchor="w", width=15).grid(row=1, column=0, pady=5, sticky="w")
    username_entry = custom_entry(form_frame)
    username_entry.grid(row=1, column=1, pady=5, sticky="ew")
    username_entry.insert(0, username)

    tk.Label(form_frame, text="Cookie 信息:", anchor="w", width=15).grid(row=2, column=0, pady=5, sticky="w")
    cookie_textarea = tk.Text(form_frame, height=5, width=30)
    cookie_textarea.grid(row=2, column=1, pady=5, sticky="ew")
    cookie_textarea.insert("1.0", login_info)

    # 底部按钮区域
    bottom_frame = tk.Frame(main_frame)
    bottom_frame.pack(pady=10)

    create_button(
        bottom_frame, "保存修改",
        button_type="default",
        command=lambda: save_user_edits(
            user_id, platform_combo.get(), username_entry.get(), cookie_textarea.get("1.0", "end").strip()
        )
    ).pack(side="left", padx=10)

    create_button(
        bottom_frame, "返回用户列表",
        button_type="default",
        command=show_user_list
    ).pack(side="right", padx=10)


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

# 初始化数据库
initialize_database()

# 主窗口
root = tk.Tk()
root.title("视频客户端")
root.geometry("600x400")

# 主框架
main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True)

# 默认显示主界面
show_main_menu()
root.mainloop()
