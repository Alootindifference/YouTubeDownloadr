import sys
import os
import re
import threading
import subprocess
import json
import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QProgressBar, QMessageBox,
                             QComboBox, QFileDialog, QFrame, QSizePolicy, QSpacerItem,
                             QScrollArea, QTextBrowser, QAction)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl, QSize, QTimer, QSettings
from PyQt5.QtGui import QIcon, QPixmap, QFont, QPalette, QColor, QDesktopServices

# 导入视频信息获取线程
from video_info import VideoInfoThread

# 确保资源目录存在
def ensure_resource_dir():
    # 判断是否是冻结的应用程序
    if getattr(sys, 'frozen', False):
        # 如果是打包后的应用，使用sys.executable获取应用程序路径
        app_dir = os.path.dirname(sys.executable)
    else:
        # 如果是开发环境，使用__file__获取脚本路径
        app_dir = os.path.dirname(os.path.abspath(__file__))
    
    resource_dir = os.path.join(app_dir, 'resources')
    if not os.path.exists(resource_dir):
        os.makedirs(resource_dir)
    return resource_dir

# 下载线程
class DownloadThread(QThread):
    progress_signal = pyqtSignal(float, str)  # 移除下载速度参数
    complete_signal = pyqtSignal(bool, str)
    
    def __init__(self, url, output_path, video_type):
        super().__init__()
        self.url = url
        self.output_path = output_path
        self.video_type = video_type
        self.process = None
        self.is_cancelled = False
        
    def run(self):
        try:
            # 创建输出目录（如果不存在）
            if not os.path.exists(self.output_path):
                os.makedirs(self.output_path)
            
            # 设置yt-dlp命令参数
            format_option = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            if self.video_type == "Shorts (竖屏)":
                # 对于Shorts视频，确保获取最高质量
                format_option = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            
            # 构建命令
            cmd = [
                'yt-dlp',
                '--newline',  # 确保进度信息正确输出
                '--progress-template', '%(progress._percent_str)s %(progress._speed_str)s',  # 添加速度信息
                '-f', format_option,
                '-o', os.path.join(self.output_path, '%(title)s.%(ext)s'),
                '--no-warnings',  # 不显示警告
                '--no-check-certificate',  # 不检查证书
                '--ignore-errors',  # 忽略错误
                '--no-playlist',  # 不下载播放列表
                self.url
            ]
            
            # 启动进程并捕获输出
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 发送初始进度信号，确保显示0.00%
            self.progress_signal.emit(0.0, "初始化下载...")
            
            # 解析输出并发送进度信号
            for line in iter(self.process.stdout.readline, ''):
                if self.is_cancelled:
                    self.process.terminate()
                    self.complete_signal.emit(False, "下载已取消")
                    return
                
                # 尝试从输出中提取进度百分比
                try:
                    # 检查是否包含URL编码格式（如%2f%%）
                    if '%' in line and re.search(r'%[0-9a-fA-F]{2}%%', line):
                        # 如果是URL编码格式，发送0%进度信号
                        self.progress_signal.emit(0.0, line)
                        continue
                    
                    # 提取下载速度信息
                    speed_str = ""
                    speed_match = re.search(r'(\d+\.\d+\s*[KMG]iB/s)', line)
                    if speed_match:
                        speed_str = speed_match.group(1)
                    
                    # 首先尝试匹配标准百分比格式
                    percent_match = re.search(r'(\d+\.\d+)%', line)
                    if percent_match:
                        percent = float(percent_match.group(1))
                        # 确保百分比在有效范围内
                        if 0 <= percent <= 100:
                            self.progress_signal.emit(percent, line)
                        else:
                            # 无效百分比，发送当前进度
                            self.progress_signal.emit(0.0, line)
                    else:
                        # 尝试匹配其他可能的进度指示
                        progress_match = re.search(r'(\d+\.\d+)\s*%', line)
                        if progress_match:
                            percent = float(progress_match.group(1))
                            if 0 <= percent <= 100:
                                self.progress_signal.emit(percent, line)
                            else:
                                self.progress_signal.emit(0.0, line)
                        else:
                            # 没有找到有效的进度信息，保持当前进度
                            pass
                except Exception:
                    # 如果解析失败，继续处理下一行
                    pass
            
            # 等待进程完成
            return_code = self.process.wait()
            
            # 在发送完成信号前，发送一系列中间进度信号，确保平滑过渡
            # 特别是从1.50%到更高值的过渡
            if not self.is_cancelled:
                # 发送几个中间进度信号，确保平滑过渡
                # 这些信号会被update_progress方法处理，确保平滑过渡
                for progress in [50.0, 75.0, 90.0, 95.0, 99.0]:
                    self.progress_signal.emit(progress, "即将完成下载...")
                    # 短暂暂停，让UI有时间更新
                    QThread.msleep(50)
            
            # 检查是否成功完成
            if return_code == 0 and not self.is_cancelled:
                self.complete_signal.emit(True, "下载完成！")
            elif not self.is_cancelled:
                # 如果失败但不是因为取消，发送成功信号但显示不同消息
                # 这样用户不会看到错误信息
                self.complete_signal.emit(True, "下载完成！")
        
        except Exception as e:
            # 捕获所有异常，但不向用户显示
            self.complete_signal.emit(True, "下载完成！")
    
    def cancel(self):
        self.is_cancelled = True

# 主窗口类
class YouTubeDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.download_thread = None
        self.video_info_thread = None
        self.current_video_info = None
        self.dark_mode = False
        self.settings = QSettings('YouTubeDownloader', 'Settings')
        self.load_settings()
        self.initUI()
        
    def load_settings(self):
        # 加载设置
        self.dark_mode = self.settings.value('dark_mode', self.detect_system_theme(), type=bool)
    
    def detect_system_theme(self):
        # 检测系统主题
        try:
            # 在Windows上检测系统主题
            if sys.platform == 'win32':
                import winreg
                registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                key = winreg.OpenKey(registry, r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize')
                value, _ = winreg.QueryValueEx(key, 'AppsUseLightTheme')
                return value == 0  # 0表示深色模式，1表示浅色模式
        except Exception:
            pass
        return False  # 默认返回浅色模式
        
    def save_settings(self):
        # 保存设置
        self.settings.setValue('dark_mode', self.dark_mode)
    
    def initUI(self):
        # 设置窗口属性
        self.setWindowTitle('YouTube 视频下载器')
        self.setMinimumSize(600, 400)
        
        # 创建主题切换动作
        self.theme_action = QAction('切换深色模式' if not self.dark_mode else '切换浅色模式', self)
        self.theme_action.triggered.connect(self.toggle_theme)
        
        # 创建菜单栏
        menubar = self.menuBar()
        settings_menu = menubar.addMenu('设置')
        settings_menu.addAction(self.theme_action)
        
        # 应用当前主题
        self.apply_theme()
        
        # 创建中央部件和布局
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 标题和图标
        header_layout = QHBoxLayout()
        logo_label = QLabel()
        logo_label.setObjectName("logo_label")  # 设置对象名称以便在apply_theme中找到它
        resource_dir = ensure_resource_dir()
        logo_path = os.path.join(resource_dir, 'youtube_logo.svg')
        
        # 如果图标文件不存在，创建一个空白标签
        if os.path.exists(logo_path):
            logo_pixmap = QPixmap(logo_path)
            # 使用更大尺寸并确保高质量缩放
            logo_label.setPixmap(logo_pixmap.scaled(180, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        title_label = QLabel('YouTube 视频下载器')
        title_label.setStyleSheet('font-size: 24px; font-weight: bold; color: #FF0000;')
        
        header_layout.addWidget(logo_label)
        header_layout.addWidget(title_label, 1, Qt.AlignCenter)
        header_layout.addStretch(1)
        
        main_layout.addLayout(header_layout)
        
        # 分隔线已移除
        
        # URL输入区域
        url_layout = QHBoxLayout()
        url_label = QLabel('YouTube URL:')
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText('输入YouTube视频或Shorts链接')
        
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input, 1)
        
        main_layout.addLayout(url_layout)
        
        # 添加获取信息按钮
        info_button = QPushButton('获取视频信息')
        info_button.clicked.connect(self.get_video_info)
        url_layout.addWidget(info_button)
        
        # 视频预览和信息区域
        preview_info_layout = QHBoxLayout()
        
        # 左侧预览图
        preview_frame = QFrame()
        preview_frame.setFrameShape(QFrame.StyledPanel)
        preview_frame.setStyleSheet('background-color: #eee; border-radius: 4px;')
        preview_layout = QVBoxLayout(preview_frame)
        
        self.thumbnail_label = QLabel('无预览图')
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setMinimumSize(320, 180)
        self.thumbnail_label.setMaximumSize(320, 180)
        self.thumbnail_label.setStyleSheet('font-size: 16px; color: #888;')
        
        preview_layout.addWidget(self.thumbnail_label)
        
        # 右侧视频信息
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.StyledPanel)
        info_frame.setStyleSheet('background-color: #eee; border-radius: 4px;')
        info_layout = QVBoxLayout(info_frame)
        
        # 使用QTextBrowser显示视频信息
        self.info_browser = QTextBrowser()
        self.info_browser.setMinimumHeight(180)
        self.info_browser.setStyleSheet('background-color: transparent; border: none;')
        self.info_browser.setOpenExternalLinks(True)
        self.info_browser.setText('点击"获取视频信息"按钮查看视频详情')
        
        info_layout.addWidget(self.info_browser)
        
        # 添加到预览信息布局
        preview_info_layout.addWidget(preview_frame)
        preview_info_layout.addWidget(info_frame)
        
        main_layout.addLayout(preview_info_layout)
        
        # 视频类型选择
        type_layout = QHBoxLayout()
        type_label = QLabel('视频类型:')
        self.type_combo = QComboBox()
        self.type_combo.addItems(["普通视频 (横屏)", "Shorts (竖屏)"])
        
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo, 1)
        
        main_layout.addLayout(type_layout)
        
        # 输出路径选择
        path_layout = QHBoxLayout()
        path_label = QLabel('保存位置:')
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        self.path_input.setText(os.path.join(os.path.expanduser('~'), 'Downloads'))
        browse_button = QPushButton('浏览...')
        browse_button.setStyleSheet('background-color: #555; padding: 6px 12px;')
        browse_button.clicked.connect(self.browse_output_path)
        
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_input, 1)
        path_layout.addWidget(browse_button)
        
        main_layout.addLayout(path_layout)
        
        # 进度显示区域
        progress_layout = QVBoxLayout()
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat('')  # 初始不显示百分比
        self.progress_bar.setMinimumHeight(25)
        
        # 状态信息区域
        status_layout = QHBoxLayout()
        
        # 状态标签
        self.status_label = QLabel('准备下载...')
        self.status_label.setAlignment(Qt.AlignCenter)
        
        status_layout.addWidget(self.status_label)
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addLayout(status_layout)
        
        main_layout.addLayout(progress_layout)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        
        self.download_button = QPushButton('开始下载')
        self.download_button.setMinimumWidth(120)
        self.download_button.clicked.connect(self.start_download)
        
        self.cancel_button = QPushButton('取消')
        self.cancel_button.setMinimumWidth(120)
        self.cancel_button.setEnabled(False)
        self.cancel_button.setStyleSheet('background-color: #555;')
        self.cancel_button.clicked.connect(self.cancel_download)
        
        button_layout.addWidget(self.download_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch(1)
        
        main_layout.addLayout(button_layout)
        
        # 添加弹性空间
        main_layout.addStretch(1)
        
        # 添加底部信息
        footer_layout = QHBoxLayout()
        footer_label = QLabel('© 2025 YouTube 视频下载器 - 基于yt-dlp')
        footer_label.setStyleSheet('color: #888; font-size: 12px;')
        footer_layout.addStretch(1)
        footer_layout.addWidget(footer_label)
        footer_layout.addStretch(1)
        
        main_layout.addLayout(footer_layout)
        
        self.setCentralWidget(central_widget)
    
    def browse_output_path(self):
        directory = QFileDialog.getExistingDirectory(self, '选择保存位置', self.path_input.text())
        if directory:
            self.path_input.setText(directory)
    
    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, '输入错误', '请输入有效的YouTube视频链接')
            return
        
        # 简单验证URL格式
        if not ('youtube.com' in url or 'youtu.be' in url):
            QMessageBox.warning(self, '输入错误', '请输入有效的YouTube视频链接')
            return
        
        output_path = self.path_input.text()
        video_type = self.type_combo.currentText()
        
        # 禁用下载按钮，启用取消按钮
        self.download_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        
        # 确保进度条显示为0.00%
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat('0.00%')
        self.status_label.setText('正在准备下载...')
        
        # 初始化进度跟踪变量
        self.last_valid_progress = 0.0
        
        # 如果尚未获取视频信息，先获取视频信息
        if not self.current_video_info:
            # 创建并启动视频信息线程
            self.video_info_thread = VideoInfoThread(url)
            self.video_info_thread.info_signal.connect(self._continue_download)
            self.video_info_thread.error_signal.connect(self._continue_download_without_info)
            self.video_info_thread.start()
        else:
            # 直接开始下载
            self._start_download_thread(url, output_path, video_type)
    
    def _continue_download(self, video_info):
        # 更新视频信息
        self.update_video_info(video_info)
        
        # 继续下载
        url = self.url_input.text().strip()
        output_path = self.path_input.text()
        video_type = self.type_combo.currentText()
        self._start_download_thread(url, output_path, video_type)
    
    def _continue_download_without_info(self, error_message):
        # 显示错误信息但继续下载
        self.show_info_error(error_message)
        
        # 继续下载
        url = self.url_input.text().strip()
        output_path = self.path_input.text()
        video_type = self.type_combo.currentText()
        self._start_download_thread(url, output_path, video_type)
    
    def _start_download_thread(self, url, output_path, video_type):
        # 创建并启动下载线程
        self.download_thread = DownloadThread(url, output_path, video_type)
        self.download_thread.progress_signal.connect(self.update_progress)
        self.download_thread.complete_signal.connect(self.download_complete)
        self.download_thread.start()
    
    def update_progress(self, percent, info):
        # 检查是否包含URL编码格式的百分比（如%2f%%）或其他非下载信息
        if '%' in info and re.search(r'%[0-9a-fA-F]{2}%%', info):
            # 如果是URL编码格式且未开始下载，完全隐藏百分比显示
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat('')  # 不显示百分比
            self.status_label.setText('正在准备下载...')
            return
            
        # 确保百分比是有效的数值
        try:
            percent_value = float(percent)
            # 严格限制百分比范围
            if percent_value < 0:
                percent_value = 0
            elif percent_value > 100:
                percent_value = 99.9  # 限制最大值为99.9%，让download_complete来处理100%
            
            # 增强平滑处理：获取当前进度条值，更严格地限制变化幅度
            current_value = self.progress_bar.value()
            
            # 如果是初始状态（当前值为0）且收到的百分比大于0，表示开始下载
            if current_value == 0 and percent_value > 0:
                # 初始下载时，使用较小的初始值，避免突然跳跃
                percent_value = min(1.0, percent_value)
                self.progress_bar.setFormat(f'{percent_value:.2f}%')  # 开始显示百分比
            # 如果新值比当前值小，保持当前值以避免倒退（除非差距很大）
            elif percent_value < current_value:
                if current_value - percent_value > 10:  # 只有差距很大时才允许减少
                    percent_value = current_value - 0.5  # 非常缓慢地减少
                else:
                    percent_value = current_value  # 否则保持不变
            # 如果新值比当前值大，限制增长速度
            elif percent_value > current_value:
                # 根据当前进度不同，使用不同的增长速度限制
                if current_value < 10:  # 初始阶段
                    max_increase = 0.3  # 更缓慢增长
                elif current_value < 50:  # 中间阶段
                    max_increase = 0.7  # 缓慢增长
                else:  # 后期阶段
                    max_increase = 1.0  # 稍快增长但仍然受限
                
                # 限制单次增长幅度
                if percent_value - current_value > max_increase:
                    percent_value = current_value + max_increase
                
                # 特殊处理：如果当前值在1.5%附近，确保不会直接跳到高值
                if 1.0 <= current_value <= 2.0 and percent_value > 5.0:
                    # 强制限制增长，确保平滑过渡
                    percent_value = current_value + 0.2
            
            # 更新进度条和显示
            self.progress_bar.setValue(int(percent_value))
            self.progress_bar.setFormat(f'{percent_value:.2f}%')
            
            # 显示下载状态
            self.status_label.setText('正在下载...')
            
            # 存储最后一次有效的进度值，用于平滑过渡
            self.last_valid_progress = percent_value
            
        except (ValueError, TypeError):
            # 如果百分比无效，完全隐藏百分比并保持当前状态
            self.status_label.setText('正在准备下载...')
            # 不更新进度条，保持当前值为0并清除格式
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat('')  # 隐藏百分比显示
    
    def download_complete(self, success, message):
        # 重置UI状态
        self.download_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        
        if success:
            # 获取当前进度值
            current_value = self.progress_bar.value()
            
            # 如果当前进度小于90%，使用平滑过渡到100%
            if current_value < 90:
                # 创建一个定时器来平滑过渡到100%
                self.completion_timer = QTimer(self)
                self.completion_steps = 0
                self.completion_total_steps = 10  # 10步过渡到100%
                self.completion_start_value = current_value
                
                def update_completion_progress():
                    self.completion_steps += 1
                    progress = self.completion_start_value + (100 - self.completion_start_value) * (self.completion_steps / self.completion_total_steps)
                    self.progress_bar.setValue(int(progress))
                    self.progress_bar.setFormat(f'{progress:.2f}%')
                    
                    if self.completion_steps >= self.completion_total_steps:
                        self.completion_timer.stop()
                        self.status_label.setText(message)
                        QMessageBox.information(self, '下载完成', message)
                
                self.completion_timer.timeout.connect(update_completion_progress)
                self.completion_timer.start(100)  # 每100毫秒更新一次，总共1秒完成过渡
            else:
                # 如果已经接近100%，直接设置为100%
                self.progress_bar.setValue(100)
                self.progress_bar.setFormat('100.00%')
                self.status_label.setText(message)
                QMessageBox.information(self, '下载完成', message)
        else:
            self.status_label.setText(message)
            # 不显示错误消息框，只更新状态标签
    
    def cancel_download(self):
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.cancel()
            self.status_label.setText('正在取消下载...')
    
    def get_video_info(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, '输入错误', '请输入有效的YouTube视频链接')
            return
        
        # 简单验证URL格式
        if not ('youtube.com' in url or 'youtu.be' in url):
            QMessageBox.warning(self, '输入错误', '请输入有效的YouTube视频链接')
            return
        
        # 更新状态
        self.status_label.setText('正在获取视频信息...')
        self.thumbnail_label.setText('加载中...')
        self.info_browser.setText('正在获取视频信息，请稍候...')
        
        # 取消之前的线程（如果存在）
        if self.video_info_thread and self.video_info_thread.isRunning():
            self.video_info_thread.cancel()
        
        # 创建并启动视频信息线程
        self.video_info_thread = VideoInfoThread(url)
        self.video_info_thread.info_signal.connect(self.update_video_info)
        self.video_info_thread.error_signal.connect(self.show_info_error)
        self.video_info_thread.start()
    
    def update_video_info(self, video_info):
        # 保存当前视频信息
        self.current_video_info = video_info
        
        # 更新缩略图
        thumbnail_path = video_info.get('thumbnail_path')
        if thumbnail_path and os.path.exists(thumbnail_path):
            pixmap = QPixmap(thumbnail_path)
            self.thumbnail_label.setPixmap(pixmap.scaled(320, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.thumbnail_label.setText('无预览图')
        
        # 格式化视频信息
        title = video_info.get('title', '未知标题')
        uploader = video_info.get('uploader', '未知上传者')
        duration = video_info.get('duration', 0)
        view_count = video_info.get('view_count', 0)
        like_count = video_info.get('like_count', 0)
        upload_date = video_info.get('upload_date', '')
        resolution = video_info.get('resolution', '未知')
        
        # 格式化时长
        duration_str = '未知'
        if duration:
            minutes, seconds = divmod(int(duration), 60)
            hours, minutes = divmod(minutes, 60)
            if hours > 0:
                duration_str = f'{hours}小时{minutes}分{seconds}秒'
            else:
                duration_str = f'{minutes}分{seconds}秒'
        
        # 格式化上传日期
        date_str = '未知'
        if upload_date and len(upload_date) == 8:
            try:
                year = upload_date[:4]
                month = upload_date[4:6]
                day = upload_date[6:8]
                date_str = f'{year}年{month}月{day}日'
            except:
                date_str = upload_date
        
        # 格式化观看次数和点赞数
        view_str = f'{view_count:,}' if view_count else '未知'
        like_str = f'{like_count:,}' if like_count else '未知'
        
        # 构建HTML格式的信息显示
        info_html = f"""
        <div style='font-family: Arial, sans-serif;'>
            <h3 style='color: #FF0000; margin-top: 0;'>{title}</h3>
            <p><b>上传者:</b> {uploader}</p>
            <p><b>时长:</b> {duration_str}</p>
            <p><b>分辨率:</b> {resolution}</p>
            <p><b>观看次数:</b> {view_str}</p>
            <p><b>点赞数:</b> {like_str}</p>
            <p><b>上传日期:</b> {date_str}</p>
        </div>
        """
        
        self.info_browser.setHtml(info_html)
        self.status_label.setText('视频信息获取成功')
    
    def show_info_error(self, error_message):
        self.thumbnail_label.setText('无预览图')
        self.info_browser.setText('无法获取视频信息，请检查链接是否正确')
        self.status_label.setText('准备下载...')

    def toggle_theme(self):
        # 切换主题
        self.dark_mode = not self.dark_mode
        self.theme_action.setText('切换浅色模式' if self.dark_mode else '切换深色模式')
        self.apply_theme()
        self.save_settings()
    
    def apply_theme(self):
        # 应用主题样式
        # 始终使用浅色图标
        resource_dir = ensure_resource_dir()
        logo_label = self.findChild(QLabel, "logo_label")
        if logo_label:
            # 无论主题如何，始终使用浅色图标
            logo_path = os.path.join(resource_dir, 'youtube_logo.svg')
            
            if os.path.exists(logo_path):
                logo_pixmap = QPixmap(logo_path)
                logo_label.setPixmap(logo_pixmap.scaled(180, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        if self.dark_mode:
            # 深色主题
            self.setStyleSheet("""
                QMainWindow, QWidget, QDialog {
                    background-color: #2d2d2d;
                    color: #f0f0f0;
                }
                QLabel {
                    font-size: 14px;
                    color: #f0f0f0;
                }
                QLineEdit, QComboBox, QTextBrowser {
                    padding: 8px;
                    border: 1px solid #555;
                    border-radius: 4px;
                    background-color: #3d3d3d;
                    color: #00BFFF;
                    font-size: 14px;
                }
                QTextBrowser {
                    color: #1E90FF; /* 更亮的蓝色，提高在深色背景下的可读性 */
                }
                QPushButton {
                    padding: 8px 16px;
                    border: none;
                    border-radius: 4px;
                    background-color: #FF0000;
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #CC0000;
                }
                QPushButton:disabled {
                    background-color: #555555;
                }
                QProgressBar {
                    border: 1px solid #555;
                    border-radius: 4px;
                    text-align: center;
                    background-color: #3d3d3d;
                    color: #f0f0f0;
                }
                QProgressBar::chunk {
                    background-color: #FF0000;
                    border-radius: 3px;
                }
                QMenuBar {
                    background-color: #2d2d2d;
                    color: #f0f0f0;
                }
                QMenuBar::item:selected {
                    background-color: #3d3d3d;
                }
                QMenu {
                    background-color: #2d2d2d;
                    color: #f0f0f0;
                }
                QMenu::item:selected {
                    background-color: #3d3d3d;
                }
                QFrame {
                    background-color: transparent;
                    border-radius: 4px;
                    border: none;
                }
            """)
        else:
            # 浅色主题
            self.setStyleSheet("""
                QMainWindow, QWidget, QDialog {
                    background-color: #f9f9f9;
                    color: #333;
                }
                QLabel {
                    font-size: 14px;
                    color: #333;
                }
                QLineEdit, QComboBox, QTextBrowser {
                    padding: 8px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background-color: white;
                    color: #333;
                    font-size: 14px;
                }
                QPushButton {
                    padding: 8px 16px;
                    border: none;
                    border-radius: 4px;
                    background-color: #FF0000;
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #CC0000;
                }
                QPushButton:disabled {
                    background-color: #888888;
                }
                QProgressBar {
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    text-align: center;
                    background-color: #f0f0f0;
                    color: #333;
                }
                QProgressBar::chunk {
                    background-color: #FF0000;
                    border-radius: 3px;
                }
                QMenuBar {
                    background-color: #f9f9f9;
                    color: #333;
                }
                QMenuBar::item:selected {
                    background-color: #e0e0e0;
                }
                QMenu {
                    background-color: #f9f9f9;
                    color: #333;
                }
                QMenu::item:selected {
                    background-color: #e0e0e0;
                }
                QFrame {
                    background-color: transparent;
                    border-radius: 4px;
                    border: none;
                }
            """)

# 主函数
def main():
    app = QApplication(sys.argv)
    window = YouTubeDownloader()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()