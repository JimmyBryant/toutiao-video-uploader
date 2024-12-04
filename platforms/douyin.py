import os
import time


def login(page):
    """手动扫码登录"""
    # 打开登录页面
    login_url = "https://creator.douyin.com/"
    page.goto(login_url)
    page.wait_for_load_state("load")
    print("请手动扫码登录...")

    # 等待用户扫码完成
    while True:
        print("等待用户扫码并完成登录...")
        time.sleep(3)
        # 判断登录完成：通过 URL 或页面元素
        if page.locator("text=发布视频").count()>0:  # 或者检查某个标志性元素
            # 打印当前 URL 以观察变化
            print(f"当前页面 URL: {page.url}")
            break

    print("登录成功！")

def upload_video(page, video_path, title, desc, tags, cover_path):
    """
    上传视频到今日头条
    :param page: Playwright Page 对象
    :param video_path: 视频文件路径
    :param title: 视频标题
    :param tags: 视频标签列表
    :param cover_path: 封面图片路径
    """
    # 打开发布页面
    page.goto("https://creator.douyin.com/creator-micro/content/upload")
    page.wait_for_load_state("load")
    print("已进入发布页面")
    page.wait_for_selector('.semi-tabs.semi-tabs-top')
    # 上传视频文件
    video_upload_input = page.locator('input[type="file"]')  # 视频上传输入框
    if video_upload_input.count() == 0:
        raise Exception("未找到视频上传输入框")
    video_upload_input.set_input_files(video_path)
    print("视频文件已选择",video_path)

    # 输入视频标题
    print("填写视频标题...")
    page.wait_for_selector('input[class*="semi-input"]')
    title_input = page.locator('input[class*="semi-input"]').first
    title_input.fill(title)
    print("标题填写完成")

    # 输入视频描述
    # print("填写视频描述...")
    # page.wait_for_selector('textarea[class*="semi-textarea"]')

    # 输入视频标签
    # if tags:
    #     print("填写视频标签...")
    #     for tag in tags:
    #         tag_input = page.locator('input.arco-input-tag-input')
    #         tag_input.click()
    #         tag_input.fill(tag)
    #         time.sleep(1)
    #         tag_input.press("Enter")
    #         time.sleep(1)
    #         tag_input.press("Enter")
    #         print(f"添加标签: {tag}")

    # 等待视频上传成功
    wait_for_upload_progress(page)

    # 上传封面图片
    # print("开始上传封面...")
    # page.locator('.fake-upload-trigger').click()  # 点击封面上传按钮
    # page.locator('li:has-text("本地上传")').click()  # 选择本地上传
    # upload_cover_image(page,cover_path)

    # 发布视频
    publish_video(page)

def wait_for_upload_progress(page, no_change_timeout=60):
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
            progress_element = page.locator("div[class*='upload-progress-inner']>span[class*='text']")
            if progress_element.is_visible():
                current_progress = progress_element.inner_text().strip()
                print(f"抖音视频上传进度: {current_progress}")

                # 检查进度是否变化
                if current_progress != last_progress:
                    last_progress = current_progress
                    last_change_time = time.time()
                elif time.time() - last_change_time > no_change_timeout:
                    raise TimeoutError("上传进度超过30秒无变化，可能上传失败")
            else:
                if last_progress:
                    print("上传进度无变化，上传成功")
                    return
                else:
                    print("等待上传进度显示...")

        except Exception as e:
            print(f"检查上传进度时出错: {e}")
            raise e

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
    # 1. 检查是否需要裁剪图片
    crop_button = page.locator('.clip-btn-content',has_text="完成裁剪")
    if crop_button.count() > 0 and crop_button.is_visible():
        crop_button.click()
        print("完成裁剪")
    time.sleep(2)
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
    
def publish_video(page):
    # 1. 定位发布按钮
    publish_button = page.locator(
        'button[class*="primary-"]',
        has_text="发布"
    )
    
    # 2. 检查发布按钮是否可用
    if not publish_button.is_enabled():
        raise Exception("发布按钮不可用，请检查页面状态")
    
    # 3. 点击发布按钮
    publish_button.click()
    print("发布按钮已点击")
    
    # 4. 等待跳转到任意一个成功页面
    try:
        page.wait_for_url(
            "https://creator.douyin.com/creator-micro/content/manage*",
            timeout=60000  # 设置超时时间，例如 60 秒
        )
        print("发布成功，页面已跳转到内容管理页面")
    except Exception as e:
        print(f"发布失败或页面未跳转，错误: {e}")
        