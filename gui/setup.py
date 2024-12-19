from setuptools import setup

APP = ['index.py']
DATA_FILES = []  # 如果需要附加文件，可以将其放入这里
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'app.icns',  # 如果需要图标，提供 .icns 文件
    'packages': [],  # 如果你的程序需要额外的 Python 包，可以添加到这里
    'excludes': ['packaging','typing_extensions'],  # 显式排除
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)