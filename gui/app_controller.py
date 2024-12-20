from ui.main_menu_ui import MainMenuUI
from ui.user_ui import UserUI
from ui.video_task_ui import VideoTaskUI
from ui.user_group_ui import UserGroupUI
from ui.setting_ui import SettingUI
import sys

class AppController:
    def __init__(self, main_frame):
        self.main_frame = main_frame
        self.current_frame = None

    def show_frame(self, frame_class, method_name=None, *args, **kwargs):
        """切换到指定的界面，并根据需要调用特定的方法"""
        # 在切换界面前重置 stdout
        sys.stdout = sys.__stdout__
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = frame_class(self.main_frame, self)
        
        # 如果有 method_name 且该方法在当前界面类中定义，则调用该方法并传递参数
        if method_name and hasattr(self.current_frame, method_name):
            method = getattr(self.current_frame, method_name)
            method(*args, **kwargs)  # 调用方法并传递参数

        self.current_frame.pack(fill="both", expand=True)

    def show_main_menu(self):
        self.show_frame(MainMenuUI)

    def show_user_list(self):
        self.show_frame(UserUI,'show_user_list')
    
    def show_add_user(self):
        self.show_frame(UserUI,'show_add_user')
    
    def show_edit_user(self, user_id):
        self.show_frame(UserUI, 'show_edit_user', user_id)

    def show_video_tasks(self):
        self.show_frame(VideoTaskUI,'show_video_tasks')
    
    def show_create_video_task(self):
        self.show_frame(VideoTaskUI,'show_create_video_task')

    def show_edit_video_task(self, task_id):
        self.show_frame(VideoTaskUI, 'show_edit_video_task', task_id)

    def show_user_groups(self):
        self.show_frame(UserGroupUI,'show_user_groups')
    
    def show_add_user_group(self):
        self.show_frame(UserGroupUI,'show_add_user_group')
    
    def show_edit_user_group(self, group_id):
        self.show_frame(UserGroupUI,'show_edit_user_group', group_id)
    
    def show_settings(self):
        self.show_frame(SettingUI,'show_settings')
    