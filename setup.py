import sys
import os
from cx_Freeze import setup, Executable

# 添加文件
include_files = [(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources'), 'resources')]

# 添加yt-dlp可执行文件
# 尝试多个可能的路径来查找yt-dlp.exe
yt_dlp_paths = [
    os.path.join(sys.executable.replace('python.exe', 'Scripts'), 'yt-dlp.exe'),
    os.path.join(os.path.dirname(sys.executable), 'Scripts', 'yt-dlp.exe'),
    # 用户目录下的Python脚本
    os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'Python', 'Python312', 'Scripts', 'yt-dlp.exe'),
    # 其他可能的路径
    'C:\\Users\\Lenovo1\\AppData\\Roaming\\Python\\Python312\\Scripts\\yt-dlp.exe'
]

yt_dlp_found = False
for path in yt_dlp_paths:
    if os.path.exists(path):
        include_files.append((path, 'yt-dlp.exe'))
        print(f"找到yt-dlp.exe: {path}")
        yt_dlp_found = True
        break

if not yt_dlp_found:
    print("警告: 未找到yt-dlp.exe，打包后的程序可能无法正常工作")
    print("请确保已安装yt-dlp: pip install yt-dlp")

# 构建选项
build_exe_options = {
    "packages": ["os", "sys", "re", "threading", "subprocess", "json", "PyQt5", "datetime", "urllib", "tempfile", "PyQt5.QtWidgets", "PyQt5.QtCore", "PyQt5.QtGui"],
    "excludes": ["PyQt5.QtQml", "PyQt5.QtQuick"],  # 排除导致错误的模块
    "include_files": include_files,
    "include_msvcr": True,
    "includes": ["video_info"],
    "bin_includes": ["yt-dlp"],
    "bin_path_includes": [sys.executable.replace("python.exe", "Scripts")],  # 动态获取Python Scripts目录
    "zip_include_packages": ["*"],
    "zip_exclude_packages": [],
    "build_exe": "build/YouTubeDownloader",  # 指定输出目录
    "optimize": 2,  # 优化字节码
}

# 可执行文件选项
base = None
if sys.platform == "win32":
    base = "Win32GUI"

executable = [
    Executable(
        "youtube_downloader.py",
        base=base,
        target_name="YouTubeDownloader.exe",
        icon="resources/youtube_logo.ico",  # 如果有图标文件的话
    )
]

# 设置
setup(
    name="YouTube Downloader",
    version="1.0.0",
    description="YouTube视频下载器",
    options={"build_exe": build_exe_options},
    executables=executable
)