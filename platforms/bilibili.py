import os
import time


def login(page, username, context):
    """
    登录 Bilibili 账号，并保存登录状态到对应的 JSON 文件。
    
    :param page: Playwright 的 Page 对象
    :param username: 用户名，用于标记保存的登录状态文件
    :param context: Playwright 的 Context 对象，用于管理浏览器上下文
    """
    # Bilibili 登录页面
    login_url = "https://passport.bilibili.com/login"
    page.goto(login_url)
    page.wait_for_load_state("load")
    print(f"打开 Bilibili 登录页面: {login_url}")    
    
    # 等待用户扫码完成
    while True:
        print("等待用户扫码并完成登录...")
        time.sleep(3)
        
        # 判断是否出现 "退出登录" 元素
        if page.locator("span:has-text('退出登录')").count() > 0:
            print("检测到 '退出登录'，登录成功！")
            break

        # 如果页面 URL 不再包含 "passport" 或 "login"，也视为成功跳转
        if "passport" not in page.url and "login" not in page.url:
            print(f"页面 URL 已跳转到: {page.url}")
            break

    print("登录成功！")


def upload_video(page, video_path, title, desc, tags=None, cover_path=None):
    """
    上传视频到 Bilibili 并设置标题、简介、标签和其他相关信息。

    :param page: Playwright 的 Page 对象
    :param video_path: 视频文件路径
    :param title: 视频标题
    :param desc: 视频简介
    :param tags: 视频标签列表
    :param cover_path: 封面图片路径（可选）
    """
    # 打开 Bilibili 上传视频页面
    upload_url = "https://member.bilibili.com/platform/upload/video/frame"
    page.goto(upload_url)
    page.wait_for_load_state("load")
    print(f"打开 Bilibili 上传视频页面: {page.url}")
    

    # 等待视频上传的文件输入框出现
    try:
        page.wait_for_selector('.bcc-upload-wrapper', timeout=5000)
        file_input = page.locator(".bcc-upload-wrapper input[type='file']")

        if file_input.count() == 0:
            raise Exception("未找到视频文件输入框")
        print("找到视频文件输入框")
    except Exception as e:
        raise e

    # 上传视频文件
    print(f"开始上传视频: {video_path}")
    file_input.set_input_files(video_path)


    # 设置封面图片（如果提供了封面路径）
    if cover_path:
        print("上传封面图片...")
        page.locator("span:has-text('更改封面')").click()
        page.locator('.text:has-text("上传封面")').click()
        cover_file_input = page.locator(".bcc-upload input[type='file'][accept*='image']").first
        if cover_file_input.count() == 0:
            raise Exception("未找到封面文件输入框")
        cover_file_input.set_input_files(cover_path)
        page.locator("button span:has-text('完成')").click()
        print(f"封面图片上传完成: {cover_path}")

    # 设置标题
    title_input = page.locator("input.input-val[type='text'][maxlength='80']").first
    if title_input.count() == 0:
        raise Exception("未找到标题输入框")
    title_input.fill(title)
    print(f"标题已设置: {title}")

    # 设置简介
    print("填写视频简介...")
    desc_editor = page.locator("div.ql-editor p").first
    if desc_editor.count() == 0:
        raise Exception("未找到简介输入框")
    desc_editor.fill(desc)
    print(f"视频简介已填写: {desc}")

    # 设置标签（如果提供了标签）
    if tags:
        # 清空已有标签
        print("清空已有标签...")
        close_buttons = page.locator(".label-item-v2-container .close")
        while close_buttons.count() > 0:
            close_buttons.first.click()
            print("删除一个标签")
            time.sleep(1)  # 确保删除动作完成后再查找剩余标签
        print("设置标签...")
        for tag in tags:
            tag_input = page.locator("input.input-val[type='text'][placeholder*='按回车键Enter创建标签']").first
            if tag_input.count() == 0:
                raise Exception("未找到标签输入框")
            # 点击输入框以确保获得焦点
            tag_input.click()
            print(f"标签输入框已获得焦点")

            # 填写标签内容
            tag_input.fill(tag)
            print(f"填写标签: {tag}")

            # 按下回车键以添加标签
            page.keyboard.press("Enter")
            print(f"已添加标签: {tag}")
            time.sleep(1)

    # 等待上传完成
    print("等待视频上传完成...")
    prev_progress = None
    unchanged_progress_time = 0
    while True:
        # 检查上传进度
        try:
            progress_text = page.locator("span.progress-text").inner_text()
            if prev_progress == progress_text:
                unchanged_progress_time += 2
                if unchanged_progress_time >= 30:  # 进度超过 30 秒无变化，超时退出
                    raise Exception("上传超时，进度未变化")
            else:
                unchanged_progress_time = 0  # 进度变化，重置计时
                prev_progress = progress_text
            print(f"当前上传进度: {progress_text}")
        except:
            pass

        # 检查上传完成标志
        if page.locator("div.file-item-content-status-text:has(span.success)").count() > 0:
            print("视频上传完成！")
            break

        # 等待 2 秒后继续检查
        time.sleep(2)


    # 点击发布按钮
    publish_button = page.locator(".submit-add:has-text('立即投稿')")
    if publish_button.count() == 0:
        raise Exception("未找到发布按钮")
    publish_button.click()
    time.sleep(1)
    print("已点击发布按钮，视频发布成功！")


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
        