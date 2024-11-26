import os
import json
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright
from platforms.toutiao import login as toutiao_login, upload_video as toutiao_upload_video
from platforms.bilibili import login as bilibili_login, upload_video as bilibili_upload_video

# 配置目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 获取当前脚本所在目录
AUTH_DIR = os.path.join(BASE_DIR, "auth")
DATA_FILE = os.path.join(BASE_DIR, "./data.json")
LOG_FILE = os.path.join(BASE_DIR, "error.log")

# 支持的平台
SUPPORTED_PLATFORMS = {"toutiao", "bilibili"}

# 登录函数
def login(platform, username, context):
    page = context.new_page()
    if platform == "toutiao":
        toutiao_login(page, username, context)
    elif platform == "bilibili":
        bilibili_login(page, username, context)
    else:
        raise ValueError(f"未支持的平台: {platform}")
    page.close()

# 发布函数
def publish(platform, task, context):
    page = context.new_page()
    if platform == "toutiao":
        toutiao_upload_video(
            page=page,
            video_path=task["video_path"],
            title=task["title"],
            tags=task["tags"],
            cover_path=task["cover_path"],
        )
    elif platform == "bilibili":
        bilibili_upload_video(
            page=page,
            video_path=task["video_path"],
            title=task["title"],
            tags=task["tags"],
            cover_path=task["cover_path"],
        )
    else:
        raise ValueError(f"未支持的平台: {platform}")
    page.close()

# 主函数
def main():
    # 检查数据文件是否存在
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(f"数据文件 {DATA_FILE} 不存在！")

    # 读取任务数据
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    # 启动 Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        for task in tasks:
            platform = task["platform"]
            username = task["username"]
            publish_date = task.get("publish_date")

            # 跳过已发布的任务
            if publish_date:
                print(f"任务已发布，跳过: {task['title']} (平台: {platform}, 用户: {username})")
                continue

            # 跳过不支持的平台
            if platform not in SUPPORTED_PLATFORMS:
                print(f"不支持的平台，跳过: {platform}")
                continue

            # 检查登录状态
            auth_file = os.path.join(AUTH_DIR, f"auth_{platform}_{username}.json")
            if os.path.exists(auth_file):
                print(f"检测到已有登录状态文件: {auth_file}")
                context = browser.new_context(storage_state=auth_file)
            else:
                print(f"未检测到 {platform} 平台账号 {username} 的登录状态，开始登录...")
                context = browser.new_context()
                try:
                    login(platform, username, context)
                    context.storage_state(path=auth_file)
                except Exception as e:
                    print(f"登录失败: 平台={platform}, 用户={username}, 错误={e}")
                    with open(LOG_FILE, "a", encoding="utf-8") as log:
                        log.write(f"[{datetime.now()}] 登录失败: 平台={platform}, 用户={username}, 错误={e}\n")
                    context.close()
                    continue

            # 发布视频
            try:
                print(f"开始发布任务: {task['title']} (平台: {platform}, 用户: {username})")
                publish(platform, task, context)
                print(f"任务发布成功: {task['title']} (平台: {platform}, 用户: {username})")
                task["publish_date"] = datetime.now().isoformat()
            except Exception as e:
                print(f"任务发布失败: {task['title']} (平台: {platform}, 用户: {username}), 错误: {e}")
                with open(LOG_FILE, "a", encoding="utf-8") as log:
                    log.write(f"[{datetime.now()}] 发布失败: {task}, 错误={e}\n")
            finally:
                context.close()

        # 保存更新后的任务数据
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=4)

        browser.close()

if __name__ == "__main__":
    main()