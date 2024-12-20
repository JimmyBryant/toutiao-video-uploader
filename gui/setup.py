from setuptools import setup
import os
APP = ['index.py']
DATA_FILES = [
    # 确保 Playwright 的驱动被复制到资源目录
    ('playwright/driver', [
        os.path.join('playwright', 'driver', 'node'),  # Playwright 的驱动文件
    ])
]
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'app.icns',  # 如果需要图标，提供 .icns 文件
    'packages': ['playwright'],
    'includes': [
        'playwright._impl',
        'playwright._impl._api_types',
        'playwright._impl._sync_base',
        'playwright._impl.sync_api',
    ],  # 包括所有动态实现部分
    'resources': ['playwright/driver'],  # 复制 Playwright 驱动文件
    'compressed': False,  # 不压缩资源文件（Playwright 可能需要解压）
    # 'excludes': ['packaging','typing_extensions'],  # 显式排除
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)