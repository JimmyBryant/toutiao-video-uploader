import tkinter as tk
from tkinter import ttk, messagebox, Text
from database import fetch_all_users, fetch_user_by_id, add_user, delete_user_by_id, update_user,fetch_all_user_groups,fetch_group_members
from playwright.sync_api import sync_playwright
import json
# 打开对应平台的登录页面
def open_login_page(platform, get_login_button, save_cookie_button, browser_dict):
    login_urls = {
        "Bilibili": "https://passport.bilibili.com/login",
        "Toutiao": "https://www.toutiao.com/login",
        "Douyin": "https://www.douyin.com/login",
        "YouTube": "https://accounts.google.com/signin",
        "TikTok": "https://www.tiktok.com/login"
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

        # 打开指定平台登录页面
        page.goto(login_url)
        messagebox.showinfo("提示", "请在浏览器中完成登录，然后点击“保存登录信息”")

        # 暂存 Playwright 对象
        browser_dict["playwright"] = playwright
        browser_dict["browser"] = browser
        browser_dict["context"] = context
        browser_dict["page"] = page

        # 切换按钮状态
        get_login_button.config(state="disabled", text="更新登录信息")
        save_cookie_button.config(state="normal")
    except Exception as e:
        messagebox.showerror("错误", f"无法打开登录页面：{e}")

# 保存 Storage State 并关闭浏览器
def save_cookies(browser_dict, save_cookie_button, get_login_button, username_entry, cookie_textarea):
    try:
        if "context" in browser_dict:
            context = browser_dict["context"]
            # 保存 Storage State
            storage_state = context.storage_state()
            # 将 storage_state 转换为 JSON 格式的字符串
            storage_state_json = json.dumps(storage_state)
            
            username_entry.login_info = storage_state_json  # 存储为用户的登录信息

            # 更新 TextArea 的内容
            cookie_textarea.config(state="normal")  # 解锁 Text 框
            cookie_textarea.delete("1.0", "end")    # 清空内容
            cookie_textarea.insert("1.0", storage_state_json)  # 插入 Storage State 数据
            cookie_textarea.config(state="disabled")  # 设置为只读

            # 关闭浏览器
            browser_dict["browser"].close()
            browser_dict["playwright"].stop()

            # 清除浏览器对象
            browser_dict.clear()

            # 切换按钮状态
            save_cookie_button.config(state="disabled")
            get_login_button.config(state="normal", text="获取登录信息")
            messagebox.showinfo("成功", "登录信息已成功保存！")
        else:
            raise Exception("未找到浏览器上下文，无法保存登录信息")
    except Exception as e:
        messagebox.showerror("错误", f"保存登录信息时出错：{e}")

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

import tkinter as tk

class UserUI(tk.Frame):
    def __init__(self, master, app_controller):
        super().__init__(master)
        self.app_controller = app_controller

    def show_user_list(self):        
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
                self.app_controller.show_edit_user(uid)

        def delete_user():
            """删除用户后刷新界面"""
            uid = user_id.get()
            if uid:
                if messagebox.askyesno("确认", f"确定要删除 ID 为 {user_id} 的用户吗？"):
                    delete_user_by_id(user_id)
                    messagebox.showinfo("成功", "用户已删除！")
                    self.app_controller.show_user_list()


        # 从数据库中获取用户列表
        users = fetch_all_users()
        main_frame = self
        tk.Label(main_frame, text="用户列表", font=("Arial", 16)).pack(pady=10)
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

            # 绑定 Treeview 的选择事件
            tree.bind("<<TreeviewSelect>>", on_tree_select)

        # 底部按钮区域
        bottom_frame = tk.Frame(main_frame)
        bottom_frame.pack(fill="x")

        # 创建编辑和删除按钮的子区域，默认隐藏
        action_frame = tk.Frame(bottom_frame)
        action_frame.pack(side="top", pady=10, fill="x")  # 确保它在最上面

        user_id = tk.StringVar()  # 存储选中用户的ID
        edit_button = tk.Button(action_frame, text="编辑", command=edit_user)
        edit_button.pack(side="left", padx=10)
        delete_button = tk.Button(action_frame, text="删除", command=delete_user)
        delete_button.pack(side="left", padx=10)

        tk.Button(action_frame, text="返回主界面", command=self.app_controller.show_main_menu).pack(side="right", padx=10)
        tk.Button(action_frame, text="添加用户", command=self.app_controller.show_add_user).pack(side="right", padx=10)

    def show_add_user(self):
        """显示添加用户功能界面"""
        main_frame=self
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
        username_entry = tk.Entry(form_frame)
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
        tk.Button(
            bottom_button_frame, text="保存用户",
            command=lambda: save_user(platform_combo.get(), username_entry.get(), cookie_textarea.get("1.0", tk.END).strip())
        ).grid(row=0, column=0, padx=10)

        # 返回发布视频界面按钮
        tk.Button(
            bottom_button_frame, text="返回主页",
            command=self.app_controller.show_main_menu
        ).grid(row=0, column=1, padx=10)

    def show_edit_user(self, user_id):
        """编辑用户信息"""
        main_frame = self
        tk.Label(main_frame, text="编辑用户", font=("Arial", 16)).grid(row=0, column=0, pady=10, columnspan=2)

        # 获取用户信息
        user = fetch_user_by_id(user_id)
        if not user:
            messagebox.showerror("错误", "用户不存在")
            self.app_controller.show_user_list()
            return

        id, platform, username, login_info,*_ = user

        # 编辑表单
        form_frame = tk.Frame(main_frame)
        form_frame.grid(row=1, column=0, pady=10, padx=20, columnspan=2)

        tk.Label(form_frame, text="用户平台:", anchor="w", width=15).grid(row=0, column=0, pady=5, sticky="w")
        platform_combo = ttk.Combobox(form_frame, values=["Bilibili", "Toutiao", "Douyin", "YouTube", "TikTok"])
        platform_combo.grid(row=0, column=1, pady=5, sticky="ew")
        platform_combo.set(platform)

        tk.Label(form_frame, text="用户名称:", anchor="w", width=15).grid(row=1, column=0, pady=5, sticky="w")
        username_entry = tk.Entry(form_frame)
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

        tk.Button(
            bottom_frame, text="保存修改",
            command=lambda: self.save_user_edits(
                user_id, platform_combo.get(), username_entry.get(), cookie_textarea.get("1.0", "end").strip()
            )
        ).grid(row=0, column=0, padx=10)

        tk.Button(
            bottom_frame, text="返回用户列表",
            command=self.app_controller.show_user_list
        ).grid(row=0, column=1, padx=10)


    def save_user_edits(self, user_id, platform, username, login_info):
        """保存用户的编辑内容到数据库"""
        if not platform or not username or not login_info:
            messagebox.showerror("错误", "所有字段均为必填")
            return

        update_user(user_id, platform, username, login_info)
        messagebox.showinfo("成功", "用户信息已更新")
        self.app_controller.show_user_list()