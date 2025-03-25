# YouTube 视频下载器

一个简单易用的YouTube视频下载工具，支持普通视频和Shorts视频的下载，并且能够下载最高分辨率的视频。

## 功能特点

- 支持下载普通YouTube视频（横屏）
- 支持下载YouTube Shorts视频（竖屏）
- 实时显示下载进度和百分比
- 美观的用户界面
- 无错误提示，用户友好
- 支持下载最高分辨率视频
- 基于yt-dlp（也可以叫yt-dlp版YouTube下载视频的图形界面）

## 使用方法

1. 运行程序
2. 输入YouTube视频链接
3. 选择视频类型（普通视频或Shorts）
4. 选择保存位置
5. 点击"开始下载"按钮

## 安装说明

### 方法一：直接运行（python）

确保已安装Python和所需依赖：

```
pip install PyQt5 yt-dlp
```

然后运行：

```
python youtube_downloader.py
```

### 方法二：使用打包好的EXE程序（在Releases里）

1. 直接运行build/YouTubeDownloader目录中的YouTubeDownloader.exe文件

2. 无需安装Python或任何依赖，所有必要的组件已经打包在一起

3. 如果需要自行打包，可以按照以下步骤操作：
   - 安装cx_Freeze：`pip install cx_Freeze`
   - 运行打包命令：`python setup.py build`
   - 在build/YouTubeDownloader目录中找到生成的EXE文件

## 注意事项

- 本程序是基于yt-dlp引擎工作的
- 下载高清视频需要较好的网络环境
- 程序会自动忽略任何错误，确保用户体验流畅
