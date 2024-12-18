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
        page.goto("https://www.youtube.com/upload")
        page.wait_for_load_state("load")
        print("[YouTube] 页面加载完成")
        # 等待上传页面加载完成
        page.locator('input[type="file"]')


        # 上传视频文件
        print("[YouTube] 正在上传视频文件...")
        page.set_input_files('input[type="file"]', video_path)
        time.sleep(5)  # 等待上传开始

        # 输入视频标题
        # 输入视频描述
        print("[YouTube] 输入视频标题...")
        textbox = page.locator('#textbox.ytcp-social-suggestions-textbox')
        if(textbox.count() ==2):
            textbox.nth(0).fill(video_title)
            textbox.nth(1).fill(video_desc)
        else:
            print("[YouTube] 输入视频标题/描述 失败")

       # 实时检查上传进度
        print("[YouTube] 检查上传进度...")
        check_upload_progress(page)
        
        # 点击Not For Kids Radio
        radios = page.locator('#radioContainer')
        if(radios.count()>1):
            radios.nth(1).click()
        else:
            print("[YouTube] 没找到not for kids radio")
        
        # 输入视频标签 (视频标签字段可能需要选择)
        # if video_tags:
        #     print("[YouTube] 输入视频标签...")
        #     page.click('div[aria-label="Tags"]')  # 点击标签输入区域
        #     page.fill('input[aria-label="Add tags"]', video_tags)
        #     time.sleep(1)

        # 上传封面图片（如提供）
        # if cover_path:
        #     print("[YouTube] 上传封面图片...")
        #     page.set_input_files('input[type="file"][accept="image/*"]', cover_path)
        #     time.sleep(2)  # 等待封面上传

        # 点击下一步按钮 (三次)
        print("[YouTube] 提交视频信息...")
        for _ in range(3):
            page.click('.right-button-area #next-button')
            time.sleep(2)

        # 选择“公开”发布选项
        print("[YouTube] 设置视频为公开...")
        page.click('tp-yt-paper-radio-button[role="radio"][name="PUBLIC"]')
        time.sleep(2)

        # 点击发布按钮
        print("[YouTube] 正在发布视频...")
        page.click('#done-button')
        time.sleep(5)  # 等待发布完成

        # 检查是否成功
        print("[YouTube] 视频上传完成")

    except Exception as e:
        print(f"[YouTube] 上传视频失败: {e}")
        raise e

def check_upload_progress(page):
    """
    检查视频上传进度，直到上传完成或检测到 2 分钟内无进度变化
    :param page: Playwright 的页面对象
    """
    last_progress = ""
    start_time = time.time()

    while True:
        progress_label = page.locator(".progress-label.ytcp-video-upload-progress")
        progress_text = progress_label.inner_text() if progress_label.count() > 0 else ""
        print(f"[YouTube] 上传进度: {progress_text}")

        if "100%" in progress_text:
            print("[YouTube] 上传完成!")
            break

        if progress_text == last_progress and time.time() - start_time > 120:
            raise Exception("[YouTube] 上传进度在 2 分钟内没有变化，可能是网络问题。")

        last_progress = progress_text
        time.sleep(2)  # 等待一段时间后重试