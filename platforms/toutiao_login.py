import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 获取当前脚本所在目录
AUTH_DIR = os.path.join(BASE_DIR, "auth")
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(AUTH_DIR, exist_ok=True)  # 自动创建目录（如果不存在）


def save_auth_state(username,context):
    """保存登录状态到 AUTH_FILE"""
    AUTH_FILE = os.path.join(AUTH_DIR, f"auth_{username}.json")
    context.storage_state(path=AUTH_FILE)
    print(f"登录状态已保存为 {AUTH_FILE}")

def login(page, username, context):
    """手动扫码登录"""
    # 打开登录页面
    login_url = "https://mp.toutiao.com/auth/page/login?redirect_url=JTJGcHJvZmlsZV92NCUyRnhpZ3VhJTJGdXBsb2FkLXZpZGVv"
    page.goto(login_url)
    page.wait_for_load_state("load")
    print("请手动扫码登录...")

    # 等待用户扫码完成
    while True:
        print("等待用户扫码并完成登录...")
        time.sleep(3)
        # 打印当前 URL 以观察变化
        print(f"当前页面 URL: {page.url}")
        # 判断登录完成：通过 URL 或页面元素
        if "upload-video" in page.url:  # 登录成功后跳转页面
            break
        if page.locator("text=上传视频").is_visible():  # 或者检查某个标志性元素
            break

    print("登录成功！")
    save_auth_state(username, context)

