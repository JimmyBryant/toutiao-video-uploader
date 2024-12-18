import tkinter as tk
from tkinter import ttk, messagebox, Text
from database import fetch_all_users, fetch_user_group_by_id, add_user_group,fetch_group_members, fetch_all_user_groups, update_user_group, delete_user_group

class UserGroupUI(tk.Frame):  
    def __init__(self, master, app_controller):
        super().__init__(master)
        self.app_controller = app_controller
    def show_user_groups(self):
        """用户组管理界面"""
        main_frame = self
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
            self.app_controller.show_add_user_group()

        def edit_group():
            selected_item = group_tree.selection()
            if not selected_item:
                messagebox.showwarning("警告", "请选择一个用户组进行编辑！")
                return
            group_id = group_tree.item(selected_item, "values")[0]  # 假设第0列是组ID
            self.app_controller.show_edit_user_group(group_id)

        def delete_group():
            selected_item = group_tree.selection()
            if not selected_item:
                messagebox.showwarning("警告", "请选择一个用户组进行删除！")
                return
            group_id = group_tree.item(selected_item, "values")[0]  # 假设第0列是组ID
            if messagebox.askyesno("确认", "确定删除该用户组吗？"):
                delete_user_group(group_id)
                self.app_controller.show_user_groups()

        # 底部按钮区域
        bottom_frame = tk.Frame(main_frame)
        bottom_frame.pack(pady=10)

        tk.Button(bottom_frame, "添加用户组", "default", command=add_group).pack(side="left", padx=10)
        tk.Button(bottom_frame, "编辑用户组", "default", command=edit_group).pack(side="left", padx=10)
        tk.Button(bottom_frame, "删除用户组", "default", command=delete_group).pack(side="left", padx=10)
        tk.Button(bottom_frame, "返回主菜单", "default", command=self.app_controller.show_main_menu).pack(side="left", padx=10)

    def add_user_group_and_refresh(self, group_name_entry, users_listbox, users):
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
        self.app_controller.show_user_groups()  # 返回user groups 界面

    def show_add_user_group(self):
        """显示添加用户组界面"""
        main_frame = self
        tk.Label(main_frame, text="添加用户组", font=("Arial", 16)).pack(pady=10)

        # 用户组表单
        form_frame = tk.Frame(main_frame)
        form_frame.pack(pady=10, padx=20)

        # 用户组名称输入
        tk.Label(form_frame, text="用户组名称:", anchor="w", width=15).grid(row=0, column=0, pady=5, sticky="w")
        group_name_entry = tk.Entry(form_frame)
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
        tk.Button(
            bottom_frame, "创建用户组",
            "default",
            command=lambda: self.add_user_group_and_refresh(group_name_entry, users_listbox, users)
        ).pack(side="left", padx=10)

        # 返回按钮
        tk.Button(
            bottom_frame, "返回",
            "default",
            command=show_user_groups
        ).pack(side="left", padx=10)

    def show_edit_user_group(self, group_id):
        """编辑用户组界面"""
        main_frame = self
        tk.Label(main_frame, text="编辑用户组", font=("Arial", 16)).pack(pady=10)

        # 获取用户组信息
        group = fetch_user_group_by_id(group_id)
        if not group:
            messagebox.showerror("错误", "用户组不存在")
            self.app_controller.show_user_groups()
            return

        group_name = group['group_name']
        members = group['members']
        users = [user_id for user_id, _, _ in members]
        # 表单区域
        form_frame = tk.Frame(main_frame)
        form_frame.pack(pady=10, padx=20)

        tk.Label(form_frame, text="组名:", anchor="w", width=15).grid(row=0, column=0, pady=5, sticky="w")
        group_name_entry = tk.Entry(form_frame)
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
            self.app_controller.show_user_groups()

        # 底部按钮区域
        bottom_frame = tk.Frame(main_frame)
        bottom_frame.pack(pady=10)

        tk.Button(bottom_frame, "保存", "default", command=lambda: save_edited_group(group_id,group_name_entry, users_listbox, all_users)).pack(side="left", padx=10)
        tk.Button(bottom_frame, "返回", "default", command=self.app_controller.show_user_groups).pack(side="left", padx=10)