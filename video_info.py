import os
import json
import subprocess
import tempfile
import urllib.request
from PyQt5.QtCore import QThread, pyqtSignal

class VideoInfoThread(QThread):
    info_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.is_cancelled = False
        
    def run(self):
        try:
            # 构建命令获取视频信息
            cmd = [
                'yt-dlp',
                '--dump-json',
                '--no-playlist',
                '--no-warnings',
                '--no-check-certificate',
                '--ignore-errors',
                self.url
            ]
            
            # 执行命令获取JSON数据
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode != 0 or not stdout.strip():
                self.error_signal.emit("无法获取视频信息")
                return
            
            # 解析JSON数据
            video_data = json.loads(stdout)
            
            # 下载缩略图
            thumbnail_url = video_data.get('thumbnail')
            if thumbnail_url:
                # 创建临时文件保存缩略图
                temp_dir = tempfile.gettempdir()
                thumbnail_path = os.path.join(temp_dir, f"yt_thumb_{video_data.get('id')}.jpg")
                
                # 下载缩略图
                try:
                    urllib.request.urlretrieve(thumbnail_url, thumbnail_path)
                    video_data['thumbnail_path'] = thumbnail_path
                except Exception:
                    video_data['thumbnail_path'] = None
            
            # 提取关键信息
            video_info = {
                'title': video_data.get('title', '未知标题'),
                'uploader': video_data.get('uploader', '未知上传者'),
                'duration': video_data.get('duration', 0),
                'view_count': video_data.get('view_count', 0),
                'like_count': video_data.get('like_count', 0),
                'upload_date': video_data.get('upload_date', ''),
                'description': video_data.get('description', '无描述'),
                'thumbnail_path': video_data.get('thumbnail_path'),
                'resolution': self._get_resolution(video_data),
                'formats': self._get_formats(video_data),
                'id': video_data.get('id', '')
            }
            
            # 发送信号
            self.info_signal.emit(video_info)
            
        except Exception as e:
            self.error_signal.emit(f"获取视频信息失败")
    
    def _get_resolution(self, video_data):
        """从视频数据中提取最佳分辨率"""
        if 'resolution' in video_data and video_data['resolution']:
            return video_data['resolution']
        
        # 尝试从格式列表中获取最佳分辨率
        best_height = 0
        best_width = 0
        
        formats = video_data.get('formats', [])
        for fmt in formats:
            height = fmt.get('height', 0) or 0
            width = fmt.get('width', 0) or 0
            
            if height > best_height:
                best_height = height
                best_width = width
        
        if best_height > 0 and best_width > 0:
            return f"{best_width}x{best_height}"
        return "未知"
    
    def _get_formats(self, video_data):
        """获取可用的视频格式列表"""
        formats = []
        for fmt in video_data.get('formats', []):
            if 'format_note' in fmt and fmt['format_note'] and 'format_id' in fmt:
                format_info = f"{fmt.get('format_note')} ({fmt.get('ext', '')})"
                if format_info not in formats:
                    formats.append(format_info)
        return formats
    
    def cancel(self):
        self.is_cancelled = True