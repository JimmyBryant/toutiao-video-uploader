from playwright.sync_api import sync_playwright
import json
import time

def upload_video(task, context):
    """
    使用 Playwright 在 YouTube 发布视频
    :param task: 视频任务信息 (包含视频路径、标题、描述等)
    :param user: 用户信息 (包含登录信息 login_info)
    """
    task_id, video_title, video_desc, video_path, cover_path, video_tags, user_group_id, user_id, scheduled_time, status = task

    try:

        page = context.new_page()
         # 修改 navigator.webdriver 属性
        page.evaluate("() => { Object.defineProperty(navigator, 'webdriver', { get: () => undefined }) }")

        print("[YouTube] 打开 YouTube 视频上传页面...")
        page.goto("https://www.youtube.com/upload", timeout=60000)

        # 等待上传页面加载完成
        page.wait_for_selector('input[type="file"]', timeout=30000)
        print("[YouTube] 页面加载完成")

        # 上传视频文件
        print("[YouTube] 正在上传视频文件...")
        page.set_input_files('input[type="file"]', video_path)
        time.sleep(5)  # 等待上传开始

        # 输入视频标题
        print("[YouTube] 输入视频标题...")
        page.fill('textarea[id="textbox"][aria-label="Title"]', video_title)

        # 输入视频描述
        print("[YouTube] 输入视频描述...")
        page.fill('textarea[id="textbox"][aria-label="Description"]', video_desc)

        # 输入视频标签 (视频标签字段可能需要选择)
        if video_tags:
            print("[YouTube] 输入视频标签...")
            page.click('div[aria-label="Tags"]')  # 点击标签输入区域
            page.fill('input[aria-label="Add tags"]', video_tags)
            time.sleep(1)

        # 上传封面图片（如提供）
        if cover_path:
            print("[YouTube] 上传封面图片...")
            page.set_input_files('input[type="file"][accept="image/*"]', cover_path)
            time.sleep(2)  # 等待封面上传

        # 点击下一步按钮 (三次)
        print("[YouTube] 提交视频信息...")
        for _ in range(3):
            page.click('button:has-text("Next")')
            time.sleep(2)

        # 选择“公开”发布选项
        print("[YouTube] 设置视频为公开...")
        page.click('div[role="radio"][aria-label="Public"]')

        # 点击发布按钮
        print("[YouTube] 正在发布视频...")
        page.click('button:has-text("Publish")')
        time.sleep(5)  # 等待发布完成

        # 检查是否成功
        print("[YouTube] 视频上传完成")

    except Exception as e:
        print(f"[YouTube] 上传视频失败: {e}")
        raise e
