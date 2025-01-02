import asyncio
import time
from asyncio import get_running_loop
async def upload_video(task, context):
    """
    使用 Playwright 在 YouTube 发布视频（异步版本）
    :param task: 视频任务信息 (包含视频路径、标题、描述等)
    :param context: Playwright 浏览器上下文对象
    """
    task_id, video_title, video_desc, video_path, cover_path, video_tags, user_group_id, user_id, scheduled_time, status = task

    try:
        # 使用异步方法来创建页面
        page = await context.new_page()
        # 修改 navigator.webdriver 属性
        await page.evaluate("() => { Object.defineProperty(navigator, 'webdriver', { get: () => undefined }) }")

        print("[YouTube] 打开 YouTube 视频上传页面...")
        await page.goto("https://www.youtube.com/upload")
        await page.wait_for_load_state("load")
        print("[YouTube] 页面加载完成")
        
        # 等待上传页面加载完成
        await page.locator('input[type="file"]').wait_for(state='attached')

        # 上传视频文件
        print("[YouTube] 正在上传视频文件...",video_path)
        await page.set_input_files('input[type="file"]', video_path)
        await asyncio.sleep(5)  # 异步等待上传开始

        # 输入视频标题和描述
        print("[YouTube] 输入视频标题...")
        textbox = page.locator('#textbox.ytcp-social-suggestions-textbox')
        if await textbox.count() == 2:
            await textbox.nth(0).fill(video_title)
            await textbox.nth(1).fill(video_desc)
        else:
            print("[YouTube] 输入视频标题/描述失败")

        # 实时检查上传进度
        print("[YouTube] 检查上传进度...")
        await check_upload_progress(page)

        # 点击 Not For Kids Radio
        radios = page.locator('#radioContainer')
        if await radios.count() > 1:
            await radios.nth(1).click()
        else:
            print("[YouTube] 没找到 Not for Kids radio")

        # 输入视频标签（如提供）
        if video_tags:
            print("[YouTube] 输入视频标签...")
            await page.click('div[aria-label="Tags"]')  # 点击标签输入区域
            await page.fill('input[aria-label="Add tags"]', video_tags)
            await asyncio.sleep(1)

        # 上传封面图片（如提供）
        if cover_path:
            print("[YouTube] 上传封面图片...")
            await page.set_input_files('input[type="file"][accept="image/*"]', cover_path)
            await asyncio.sleep(2)  # 异步等待封面上传

        # 点击下一步按钮（三次）
        print("[YouTube] 提交视频信息...")
        for _ in range(3):
            await page.click('.right-button-area #next-button')
            await asyncio.sleep(2)

        # 选择“公开”发布选项
        print("[YouTube] 设置视频为公开...")
        await page.click('tp-yt-paper-radio-button[role="radio"][name="PUBLIC"]')
        await asyncio.sleep(2)

        # 点击发布按钮
        print("[YouTube] 正在发布视频...")
        await page.click('#done-button')
        await asyncio.sleep(5)  # 等待发布完成

        # 检查是否成功
        print("[YouTube] 视频上传完成")

    except Exception as e:
        print(f"[YouTube] 上传视频失败: {e}")
        raise e

async def check_upload_progress(page):
    last_progress = ""
    start_time = get_running_loop().time()  # 异步时间
    completed_keywords = ["100%", "上传完毕", "正在检查", "检查完毕", "Upload complete", "Checking"]

    while True:
        progress_label = page.locator(".progress-label.ytcp-video-upload-progress")
        progress_text = await progress_label.inner_text() if await progress_label.count() > 0 else ""
        print(f"[YouTube] 上传进度: {progress_text}")

        if any(keyword in progress_text for keyword in completed_keywords):
            print("[YouTube] 上传完成!")
            break
        
        if progress_text != last_progress:
            start_time = get_running_loop().time()  # 更新 start_time 在进度变化时

        if progress_text == last_progress and get_running_loop().time() - start_time > 120:
            raise Exception("[YouTube] 上传进度在 2 分钟内没有变化，可能是网络问题。")

        last_progress = progress_text
        await asyncio.sleep(2)  # 异步等待

