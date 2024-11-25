from playwright.sync_api import sync_playwright
import os
import time
import json
from datetime import datetime

# 配置常量
# USERNAME = "19720709092"  # 替换为你的账号
USERNAME = "绿绿和蓝蓝"
DATA_DIR = "./data"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 获取当前脚本所在目录
AUTH_DIR = os.path.join(BASE_DIR, "auth")
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(AUTH_DIR, exist_ok=True)  # 自动创建目录（如果不存在）
AUTH_FILE = os.path.join(AUTH_DIR, f"auth_{USERNAME}.json")

def save_auth_state(context):
    """保存登录状态到 AUTH_FILE"""
    context.storage_state(path=AUTH_FILE)
    print(f"登录状态已保存为 {AUTH_FILE}")

def manual_login(page, context):
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
    save_auth_state(context)
def upload_video(page, video_path, title, tags, cover_path):
    """
    上传视频到今日头条
    :param page: Playwright Page 对象
    :param video_path: 视频文件路径
    :param title: 视频标题
    :param tags: 视频标签列表
    :param cover_path: 封面图片路径
    """
    print("开始上传视频...")
    # 上传视频文件
    video_upload_input = page.locator('input[type="file"]').nth(0)  # 视频上传输入框
    video_upload_input.set_input_files(video_path)
    print("视频文件已选择")

    # 等待视频上传成功
    wait_for_upload_progress(page)

    # 输入视频标题
    print("填写视频标题...")
    title_input = page.wait_for_selector('input[class*="xigua-input"]')
    title_input.fill(title)
    print("标题填写完成")

    # 输入视频标签
    if tags:
        print("填写视频标签...")
        for tag in tags:
            tag_input = page.locator('input[placeholder="请输入标签"]')
            tag_input.fill(tag)
            tag_input.press("Enter")
            print(f"添加标签: {tag}")

    # 上传封面图片
    print("开始上传封面...")
    page.locator('.fake-upload-trigger').click()  # 点击封面上传按钮
    page.locator('li:has-text("本地上传")').click()  # 选择本地上传
    upload_cover_image(page,cover_path)


def wait_for_upload_progress(page, no_change_timeout=30):
    """
    等待视频上传成功，并监测上传进度是否发生变化。
    如果 30 秒内上传进度无变化，则抛出超时错误。

    :param page: 当前页面对象
    :param no_change_timeout: 上传进度无变化的最大等待时间，单位秒
    """
    last_change_time = time.time()
    last_progress = ""

    while True:
        try:
            # 获取上传进度文本
            progress_element = page.locator("span.percent")
            if progress_element.is_visible():
                current_progress = progress_element.inner_text().strip()
                print(f"当前上传进度: {current_progress}")

                # 检查是否上传成功
                if "上传成功" in current_progress:
                    print("视频上传成功")
                    return

                # 检查进度是否变化
                if current_progress != last_progress:
                    last_progress = current_progress
                    last_change_time = time.time()
                elif time.time() - last_change_time > no_change_timeout:
                    raise TimeoutError("上传进度超过30秒无变化，可能上传失败")
            else:
                print("等待上传进度显示...")

        except Exception as e:
            print(f"检查上传进度时出错: {e}")

        # 每秒检查一次
        time.sleep(1)

def upload_cover_image(page, image_path):
    if not os.path.exists(image_path):
        raise Exception(f"文件路径无效: {image_path}")

    file_input = page.locator('input[type="file"][accept*="image"]')
    print("文件输入框属性:")
    print(file_input.get_attribute("accept"))  # 确认 accept 属性是否正确
    print(file_input.get_attribute("style"))  # 查看是否仍然隐藏

    if file_input.count() == 0:
        raise Exception("未找到文件输入框")
    print("找到文件输入框")

    # 4. 设置封面图片文件
    file_input.set_input_files(image_path)
    print(f"封面图片 {image_path} 已设置")
    confirm_cover_image(page)

def confirm_cover_image(page):
    # 1. 点击“确定”按钮，确认封面图片
    confirm_button = page.locator('button.btn-l.btn-sure.ml16', has_text="确定")
    if not confirm_button.is_enabled():
        raise Exception("封面确认按钮不可点击，请检查上传状态")
    confirm_button.click()
    print("封面确认按钮已点击")

    # 2. 等待弹出确认对话框，并点击“确定”
    dialog_confirm_button = page.locator('button.m-button.red', has_text="确定")
    if dialog_confirm_button.is_visible():
        dialog_confirm_button.click()
        print("对话框确认按钮已点击")
    else:
        raise Exception("未找到对话框的确认按钮")
    
def publish_video(page, context):
    # 1. 定位发布按钮
    publish_button = page.locator(
        'button.byte-btn.byte-btn-primary.byte-btn-size-large.byte-btn-shape-square.action-footer-btn.submit',
        has_text="发布"
    )
    
    # 2. 检查发布按钮是否可用
    if not publish_button.is_enabled():
        raise Exception("发布按钮不可用，请检查页面状态")
    
    # 3. 点击发布按钮
    publish_button.click()
    print("发布按钮已点击")
    
    # 4. 等待跳转到任意一个成功页面
    expected_urls = [
        "https://mp.toutiao.com/profile_v4/xigua/content-manage-v2",
        "https://mp.toutiao.com/profile_v4/xigua/small-video"
    ]
    # 使用 JavaScript 脚本检查是否跳转到目标页面
    page.wait_for_function(
        f"""
        () => {{
            const url = window.location.href;
            return {str(expected_urls)}.includes(url);
        }}
        """,
        timeout=60000  # 等待跳转完成，超时设置为 60 秒
    )
    print(f"页面跳转成功，当前 URL: {page.url}")

    # 5. 关闭浏览器
    context.close()
    print("浏览器已关闭")


def load_tasks(file_path):
    """加载任务列表"""
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)
def save_tasks(file_path, tasks):
    """保存任务列表"""
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(tasks, file, ensure_ascii=False, indent=4)

def publish_pending_videos(username, tasks):
    """发布未设置 publish_date 的视频"""
    auth_file = os.path.join(AUTH_DIR, f"auth_{username}.json")
    pending_tasks = [task for task in tasks if not task.get("publish_date")]

    if not pending_tasks:
        print(f"{username} 没有待发布的视频任务")
        return
    
    print(f"{username} 有 {len(pending_tasks)} 个待发布视频任务")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        if os.path.exists(auth_file):
            context = browser.new_context(storage_state=auth_file)
        else:
            print(f"未检测到 {username} 的登录状态文件，请先手动登录")
            return

        page = context.new_page()

        for task in pending_tasks:
            try:
                # 打开发布页面
                page.goto("https://mp.toutiao.com/profile_v4/xigua/upload-video")
                page.wait_for_load_state("load")

                # 发布视频
                upload_video(
                    page=page,
                    video_path=task["video_path"],
                    title=task["title"],
                    tags=task["tags"],
                    cover_path=task["cover_path"],
                )
                publish_video(page, context)

                # 更新任务的 publish_date
                task["publish_date"] = datetime.now().isoformat()
                print(f"视频发布成功: {task['title']}")

            except Exception as e:
                print(f"发布视频失败: {task['title']}，错误: {e}")

        # 保存已更新的任务列表
        save_tasks(os.path.join(DATA_DIR, f"data_{username}.json"), tasks)
        browser.close()
        
def main():
    """主程序入口"""
    if not os.path.exists(DATA_DIR):
        print(f"任务目录 {DATA_DIR} 不存在，请检查")
        return

    for file_name in os.listdir(DATA_DIR):
        if not file_name.startswith("data_") or not file_name.endswith(".json"):
            continue

        username = file_name[5:-5]  # 从文件名中提取 USERNAME
        file_path = os.path.join(DATA_DIR, file_name)
        tasks = load_tasks(file_path)
        publish_pending_videos(username, tasks)

    video_path = "/Volumes/disk/剪映Pro/德国超市/德国超市.mp4"  # 替换为你的视频路径
    title = "探访上海的德国夫妻：没想到这里的Aldi比德国还棒！"  # 替换为你的标题
    cover_path = "/Volumes/disk/剪映Pro/德国超市/德国超市-封面.jpg" 

    # with sync_playwright() as p:
    #     browser = p.chromium.launch(headless=False)
    #     try:
    #         # 检查是否已有登录状态文件
    #         if os.path.exists(AUTH_FILE):
    #             print(f"检测到已有登录状态文件: {AUTH_FILE}")
    #             context = browser.new_context(storage_state=AUTH_FILE)
    #         else:
    #             print("未检测到登录状态文件，开始登录...")
    #             context = browser.new_context()
    #             page = context.new_page()
    #             manual_login(page, context)

    #         # 打开发布页面
    #         page = context.new_page()
    #         page.goto("https://mp.toutiao.com/profile_v4/xigua/upload-video")
    #         page.wait_for_load_state("load")
    #         print("已进入发布页面")

    #         # 调用上传视频功能
    #         upload_video(
    #             page=page,
    #             video_path=video_path,  # 替换为你的本地视频路径
    #             title=title,       # 替换为你的标题
    #             tags=[],  # 替换为你的标签
    #             cover_path=cover_path
    #         )

    #         # 发布视频
    #         publish_video(page, context)
    #     except Exception as e:
    #         print(f"运行过程中出现异常: {e}")
    #     finally:
    #         browser.close()
    #         print("浏览器已关闭")

if __name__ == "__main__":
    main()