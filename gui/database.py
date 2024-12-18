import sqlite3
import datetime

# 数据库文件路径
DB_FILE = "user_data.db"

def initialize_database():
    """初始化数据库并创建必要的表"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 创建用户表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            username TEXT NOT NULL,
            login_info TEXT NOT NULL
        )
    """)

    # 创建用户组表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT NOT NULL UNIQUE
        )
    """)

    # 创建用户组成员表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_group_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (group_id) REFERENCES user_groups(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)


    # 创建 video_tasks 表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS video_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_title TEXT,
            video_desc TEXT,
            video_path TEXT,
            cover_path TEXT,
            video_tags TEXT,
            user_group_id INTEGER DEFAULT NULL,
            user_id INTEGER DEFAULT NULL,
            scheduled_time TEXT,
            status INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()

def fetch_all_users():
    """获取所有用户"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    return users

def fetch_user_by_id(user_id):
    """根据用户ID获取用户信息"""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            return user
    
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None  # 可以根据需求返回 None 或者其他错误标识
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def add_user(platform, username, login_info):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (platform, username, login_info) VALUES (?, ?, ?)
    """, (platform, username, login_info))
    conn.commit()
    conn.close()


def delete_user_by_id(user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def update_user(user_id, platform, username, login_info):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET platform = ?, username = ?, login_info = ? WHERE id = ?
    """, (platform, username, login_info, user_id))
    conn.commit()
    conn.close()

def delete_user_group(group_id):
    """
    删除用户组及其成员
    :param group_id: 用户组ID
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # 删除用户组成员
        cursor.execute("DELETE FROM user_group_members WHERE group_id = ?", (group_id,))
        
        # 删除用户组
        cursor.execute("DELETE FROM user_groups WHERE id = ?", (group_id,))

        conn.commit()
        print(f"用户组 {group_id} 已删除")
    except sqlite3.Error as e:
        print(f"删除用户组失败: {e}")
    finally:
        conn.close()



def fetch_all_user_groups():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_groups")
    groups = cursor.fetchall()
    conn.close()
    # 将元组转换为字典
    return groups

def fetch_all_user_group_names():
    """获取所有用户组名称"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT group_name FROM user_groups")
    group_names = [row[0] for row in cursor.fetchall()]
    conn.close()
    return group_names

def update_user_group(group_id, new_name):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE user_groups SET group_name = ? WHERE id = ?
    """, (new_name, group_id))
    conn.commit()
    conn.close()


# 用户组成员表相关操作
def add_user_to_group(group_id, user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO user_group_members (group_id, user_id) VALUES (?, ?)
        """, (group_id, user_id))
        conn.commit()
    except sqlite3.IntegrityError:
        print("该用户已在用户组中")
    finally:
        conn.close()


def remove_user_from_group(group_id, user_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM user_group_members WHERE group_id = ? AND user_id = ?
    """, (group_id, user_id))
    conn.commit()
    conn.close()


def fetch_group_members(group_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.platform, u.username 
        FROM user_group_members ugm
        JOIN users u ON ugm.user_id = u.id
        WHERE ugm.group_id = ?
    """, (group_id,))
    members = cursor.fetchall()
    conn.close()
    return members

def add_user_group(group_name, selected_users):
    """
    保存用户组及其成员
    :param group_name: 用户组名称
    :param selected_users: 用户ID列表
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # 创建用户组
        cursor.execute("INSERT INTO user_groups (group_name) VALUES (?)", (group_name,))
        group_id = cursor.lastrowid

        # 添加用户到用户组
        for user_id in selected_users:
            cursor.execute("""
                INSERT INTO user_group_members (group_id, user_id) VALUES (?, ?)
            """, (group_id, user_id))

        conn.commit()
    except sqlite3.IntegrityError as e:
        print(f"保存用户组失败: {e}")
    finally:
        conn.close()

def update_user_group(group_id, new_group_name, selected_users):
    """
    更新用户组及其成员
    :param group_id: 用户组ID
    :param new_group_name: 新的用户组名称
    :param selected_users: 用户ID列表
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # 更新用户组名称
        cursor.execute("UPDATE user_groups SET group_name = ? WHERE id = ?", (new_group_name, group_id))

        # 清除现有的用户组成员
        cursor.execute("DELETE FROM user_group_members WHERE group_id = ?", (group_id,))

        # 添加新的用户到用户组
        for user_id in selected_users:
            cursor.execute("""
                INSERT INTO user_group_members (group_id, user_id) VALUES (?, ?)
            """, (group_id, user_id))

        conn.commit()
    except sqlite3.IntegrityError as e:
        print(f"更新用户组失败: {e}")
    finally:
        conn.close()

def fetch_user_group_by_id(group_id):
    """
    根据用户组ID获取用户组及其成员
    :param group_id: 用户组ID
    :return: 用户组信息，包括成员列表
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 获取用户组信息
    cursor.execute("SELECT * FROM user_groups WHERE id = ?", (group_id,))
    group = cursor.fetchone()

    if not group:
        conn.close()
        return None  # 用户组不存在

    # 获取用户组成员信息
    cursor.execute("""
        SELECT u.id, u.platform, u.username 
        FROM user_group_members ugm
        JOIN users u ON ugm.user_id = u.id
        WHERE ugm.group_id = ?
    """, (group_id,))
    members = cursor.fetchall()

    conn.close()

    return {
        "group_id": group[0],
        "group_name": group[1],
        "members": members
    }

def fetch_user_group_members_by_id(group_id):
    """
    根据用户组ID获取用户组所有成员
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.platform, u.username 
        FROM user_group_members ugm
        JOIN users u ON ugm.user_id = u.id
        WHERE ugm.group_id = ?
    """, (group_id,))
    results = cursor.fetchall()
    conn.close()
    return results

def add_video_task(video_title, video_desc, video_path, cover_path, video_tags, user_group_id, user_id, scheduled_time, status=0):
    """
    创建视频任务
    :param video_title: 视频标题
    :param video_desc: 视频描述
    :param video_path: 视频路径
    :param cover_path: 视频封面路径
    :param video_tags: 视频标签（逗号分隔）
    :param user_group_id: 用户组 ID，若选择用户组则为整数，若不选择则为 None
    :param user_id: 用户 ID，若选择用户则为整数，若不选择则为 None
    :param scheduled_time: 预约发布时间（字符串格式：YYYY-MM-DD HH:MM:SS）
    :param status: 任务状态，默认为 0
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # 确保 user_group_id 和 user_id 至少有一个非空
        if user_group_id is None and user_id is None:
            raise ValueError("用户组 ID 和用户 ID 不能同时为空")

        cursor.execute("""
            INSERT INTO video_tasks (video_title, video_desc, video_path, cover_path, video_tags, user_group_id, user_id, scheduled_time, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (video_title, video_desc, video_path, cover_path, video_tags, user_group_id, user_id, scheduled_time, status))

        conn.commit()
        print("视频任务创建成功")
    except ValueError as ve:
        print(f"创建视频任务失败: {ve}")
    except sqlite3.IntegrityError as e:
        print(f"创建视频任务失败: {e}")
    finally:
        conn.close()


def fetch_all_video_tasks():
    """获取所有视频任务"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM video_tasks ORDER BY id DESC")
    tasks = cursor.fetchall()

    conn.close()
    return tasks

def fetch_video_task_by_id(task_id):
    """根据任务ID获取视频任务"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM video_tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()

    conn.close()
    return task

def update_video_task(task_id, video_title=None, video_desc=None, video_path=None, cover_path=None, video_tags=None, user_group=None, user_id=None, scheduled_time=None, status=None):
    """更新视频任务"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 动态生成更新语句
    set_clauses = []
    params = []
    
    if video_title is not None:
        set_clauses.append("video_title = ?")
        params.append(video_title)
    
    if video_desc is not None:
        set_clauses.append("video_desc = ?")
        params.append(video_desc)
    
    if video_path is not None:
        set_clauses.append("video_path = ?")
        params.append(video_path)
    
    if cover_path is not None:
        set_clauses.append("cover_path = ?")
        params.append(cover_path)
    
    if video_tags is not None:
        set_clauses.append("video_tags = ?")
        params.append(video_tags)
    
    if user_group is not None:
        set_clauses.append("user_group = ?")
        params.append(user_group)
    
    if scheduled_time is not None:
        set_clauses.append("scheduled_time = ?")
        params.append(scheduled_time)
    
    if status is not None:  # 显式检查 status 是否为 None
        set_clauses.append("status = ?")
        params.append(status)

    set_clause = ", ".join(set_clauses)
    params.append(task_id)

    try:
        cursor.execute(f"""
            UPDATE video_tasks
            SET {set_clause}
            WHERE id = ?
        """, tuple(params))

        conn.commit()
    except sqlite3.IntegrityError as e:
        print(f"更新视频任务失败: {e}")
    finally:
        conn.close()

def delete_video_task(task_id):
    """删除视频任务"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM video_tasks WHERE id = ?", (task_id,))
        conn.commit()
        print(f"视频任务 {task_id} 已删除")
    except sqlite3.Error as e:
        print(f"删除视频任务失败: {e}")
    finally:
        conn.close()

def fetch_pending_video_tasks():
    """查询未发布且满足预约时间的任务"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 当前时间
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 查询未发布（status = 0）且预约时间已到的任务
    cursor.execute("""
        SELECT * FROM video_tasks
        WHERE status = 0 AND scheduled_time <= ?
    """, (now,))

    tasks = cursor.fetchall()
    conn.close()
    return tasks

def update_video_task_status(task_id, status):
    """更新任务状态"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE video_tasks
        SET status = ?
        WHERE id = ?
    """, (status, task_id))
    conn.commit()
    conn.close()