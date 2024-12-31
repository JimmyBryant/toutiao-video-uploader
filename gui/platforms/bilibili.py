import asyncio

async def upload_video(task, context):
    """
    上传视频到 Bilibili 并设置标题、简介、标签和其他相关信息（异步版）

    :param page: Playwright 的 Page 对象
    :param video_path: 视频文件路径
    :param title: 视频标题
    :param desc: 视频简介
    :param tags: 视频标签列表
    :param cover_path: 封面图片路径（可选）
    """
    task_id, video_title, video_desc, video_path, cover_path, video_tags, user_group_id, user_id, scheduled_time, status = task
    # 打开 Bilibili 上传视频页面
    upload_url = "https://member.bilibili.com/platform/upload/video/frame"

    
    # 等待视频上传的文件输入框出现
    try:
        page = await context.new_page()
        await page.goto(upload_url)
        await page.wait_for_load_state("load")
        print(f"打开 Bilibili 上传视频页面: {page.url}")
        await page.wait_for_selector('.bcc-upload-wrapper', timeout=5000)
        file_input = page.locator(".bcc-upload-wrapper input[type='file']")

        if await file_input.count() == 0:
            raise Exception("未找到视频文件输入框")
        print("找到视频文件输入框")
    except Exception as e:
        raise e

    # 上传视频文件
    print(f"开始上传视频: {video_path}")
    await file_input.set_input_files(video_path)

    # 设置封面图片（如果提供了封面路径）
    if cover_path:
        print("上传封面图片...")
        await page.locator("span:has-text('更改封面')").click()
        await page.locator('.text:has-text("上传封面")').click()
        cover_file_input = page.locator(".bcc-upload input[type='file'][accept*='image']").first
        if await cover_file_input.count() == 0:
            raise Exception("未找到封面文件输入框")
        await cover_file_input.set_input_files(cover_path)
        await page.locator("button span:has-text('完成')").click()
        print(f"封面图片上传完成: {cover_path}")

    # 设置标题
    title_input = page.locator("input.input-val[type='text'][maxlength='80']").first
    if await title_input.count() == 0:
        raise Exception("未找到标题输入框")
    await title_input.fill(video_title)
    print(f"标题已设置: {video_title}")

    # 设置简介
    print("填写视频简介...")
    desc_editor = page.locator("div.ql-editor p").first
    if await desc_editor.count() == 0:
        raise Exception("未找到简介输入框")
    await desc_editor.fill(video_desc)
    print(f"视频简介已填写: {video_desc}")

    # 设置标签（如果提供了标签）
    tags = video_tags.split(",") if video_tags else []
    if tags:
        # 清空已有标签
        print("清空已有标签...")
        close_buttons = page.locator(".label-item-v2-container .close")
        while await close_buttons.count() > 0:
            await close_buttons.first.click()
            print("删除一个标签")
            await asyncio.sleep(1)  # 异步等待删除完成
        print("设置标签...")
        for tag in tags:
            tag_input = page.locator("input.input-val[type='text'][placeholder*='按回车键Enter创建标签']").first
            if await tag_input.count() == 0:
                raise Exception("未找到标签输入框")
            # 点击输入框以确保获得焦点
            await tag_input.click()
            print(f"标签输入框已获得焦点")

            # 填写标签内容
            await tag_input.fill(tag)
            print(f"填写标签: {tag}")

            # 按下回车键以添加标签
            await page.keyboard.press("Enter")
            print(f"已添加标签: {tag}")
            await asyncio.sleep(1)

    # 等待上传完成
    print("等待视频上传完成...")
    prev_progress = None
    unchanged_progress_time = 0
    while True:
        # 检查上传进度
        try:
            progress_text = await page.locator("span.progress-text").inner_text()
            if prev_progress == progress_text:
                unchanged_progress_time += 2
                if unchanged_progress_time >= 30:  # 进度超过 30 秒无变化，超时退出
                    raise Exception("上传超时，进度未变化")
            else:
                unchanged_progress_time = 0  # 进度变化，重置计时
                prev_progress = progress_text
            print(f"Bilibili当前上传进度: {progress_text}")
        except:
            pass

        # 检查上传完成标志
        if await page.locator("div.file-item-content-status-text:has(span.success)").count() > 0:
            print("视频上传完成！")
            break

        # 等待 2 秒后继续检查
        await asyncio.sleep(2)

    # 点击发布按钮
    publish_button = page.locator(".submit-add:has-text('立即投稿')")
    if await publish_button.count() == 0:
        raise Exception("未找到发布按钮")
    await publish_button.click()
    await asyncio.sleep(1)
    print("已点击发布按钮，视频发布成功！")
