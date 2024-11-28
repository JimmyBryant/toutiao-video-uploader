# 视频自动发布脚本

## 目录结构
```
.
├── README.md
├── data.json
├── main.py
├─ auth
└── platforms
```

## 使用方法
在data.json配置要上传是视频数据
1. 配置好data.json文件

```
    {
        "platform": "bilibili", // 平台名称，还可以填写toutiao
        "username": "账号名称", // 主要用于获取和保存auth文件
        "video_path": "/Volumes/disk/剪映Pro/李行亮争女儿/李行亮争女儿.mp4", // 视频路径
        "title": "看到最后好窒息！李行亮为女儿崩溃大哭，戳穿麦琳不懂女儿",  // 标题
        "cover_path": "/Volumes/disk/剪映Pro/李行亮争女儿/李行亮争女儿-封面.jpg",   // 封面路径
        "tags": [   // 标签
            "再见爱人4",
            "李行亮大哭",
            "麦琳"
        ],
        "desc": "【精彩看点】看到最后好窒息！李行亮为争女儿抚养权崩溃大哭，戳穿麦琳不会理解女儿｜《再见爱人4》",    // 描述
    }
```
2. 运行main.py
3. 运行成功后，会在当前目录生成auth文件夹，里面有auth文件，用于保存登录信息，下次运行不需要再登录