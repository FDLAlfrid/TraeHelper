#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TraeCacheCleaner - Trae IDE Cache Management Tool
支持 GUI 和 CLI 两种模式，单文件架构
"""

import os
import sys
import json
import shutil
import subprocess
import ctypes
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Version
VERSION = "v0.1.4"

# ============================================================================
# Configuration Directory Management
# ============================================================================

def get_config_dir() -> Path:
    """获取隐藏的配置目录"""
    config_dir = Path.home() / '.trae_cache_cleaner'
    config_dir.mkdir(exist_ok=True)
    return config_dir

def get_app_config_file() -> Path:
    """获取应用配置文件路径"""
    return get_config_dir() / 'app_config.json'

def load_app_config() -> Dict[str, Any]:
    """加载应用配置"""
    config_file = get_app_config_file()
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        'font_size': 10,
        'safe_mode': True,
        'show_console': False,
        'window_geometry': None
    }

def save_app_config(config: Dict[str, Any]) -> None:
    """保存应用配置"""
    config_file = get_app_config_file()
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

# ============================================================================
# Basic Utilities
# ============================================================================

def get_current_directory():
    """获取当前目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def is_git_installed():
    """检查 git 是否安装"""
    try:
        subprocess.run(['git', '--version'], capture_output=True, check=True)
        return True
    except:
        return False

def get_git_version():
    """获取 git 版本"""
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except:
        return None

def get_git_config(key):
    """获取 git 配置"""
    try:
        result = subprocess.run(['git', 'config', '--global', key], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except:
        return None

# ============================================================================
# Path Configuration
# ============================================================================

class PathConfig:
    """路径配置"""
    
    @staticmethod
    def get_appdata():
        return os.getenv('APPDATA')
    
    @staticmethod
    def get_userprofile():
        return os.getenv('USERPROFILE')
    
    @staticmethod
    def get_trae_root():
        """获取 Trae 根目录"""
        appdata = PathConfig.get_appdata()
        candidates = [
            os.path.join(appdata, 'Trae CN'),
            os.path.join(appdata, 'Trae'),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return candidates[0]
    
    @staticmethod
    def get_trae_user():
        """获取 Trae User 目录"""
        return os.path.join(PathConfig.get_trae_root(), 'User')
    
    @staticmethod
    def get_mcp_path():
        """获取 MCP 配置路径"""
        userprofile = PathConfig.get_userprofile()
        candidates = [
            os.path.join(userprofile, '.trae-cn', 'mcp.json'),
            os.path.join(userprofile, '.trae', 'mcp.json'),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return candidates[0]
    
    @staticmethod
    def get_rules_path():
        """获取 Rules 配置路径"""
        userprofile = PathConfig.get_userprofile()
        candidates = [
            os.path.join(userprofile, '.trae-cn', 'rules'),
            os.path.join(userprofile, '.trae', 'rules'),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return candidates[0]
    
    @staticmethod
    def get_workspace_storage():
        """获取 workspace storage 路径"""
        return os.path.join(PathConfig.get_trae_user(), 'workspaceStorage')
    
    @staticmethod
    def get_chat_sessions():
        """获取 chat sessions 路径（新）"""
        return os.path.join(PathConfig.get_trae_user(), 'History')
    
    @staticmethod
    def get_extensions():
        """获取扩展目录"""
        userprofile = PathConfig.get_userprofile()
        appdata = PathConfig.get_appdata()
        candidates = [
            os.path.join(userprofile, '.trae-cn', 'extensions'),
            os.path.join(userprofile, '.trae', 'extensions'),
            os.path.join(appdata, 'Trae CN', 'extensions'),
            os.path.join(appdata, 'Trae', 'extensions'),
        ]
        return candidates
    
    @staticmethod
    def get_app_dir():
        """获取应用存储路径"""
        userprofile = PathConfig.get_userprofile()
        candidates = [
            os.path.join(userprofile, '.trae-cn'),
            os.path.join(userprofile, '.trae'),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return candidates[0]

# ============================================================================
# Cache Entries Configuration
# ============================================================================

CACHE_ENTRIES = [
    {'name': '浏览器缓存', 'desc': 'Chromium 内核缓存', 'path': lambda: os.path.join(PathConfig.get_trae_root(), 'Cache'), 'safe': True},
    {'name': 'Code 缓存', 'desc': 'VSCode 核心缓存', 'path': lambda: os.path.join(PathConfig.get_trae_root(), 'Code Cache'), 'safe': True},
    {'name': 'GPU 缓存', 'desc': '图形加速缓存', 'path': lambda: os.path.join(PathConfig.get_trae_root(), 'GPUCache'), 'safe': True},
    {'name': '日志文件', 'desc': '系统运行日志', 'path': lambda: os.path.join(PathConfig.get_trae_root(), 'logs'), 'safe': True},
    {'name': '临时文件', 'desc': '临时数据文件', 'path': lambda: os.path.join(PathConfig.get_trae_root(), 'tmp'), 'safe': True},
    {'name': 'Crash 日志', 'desc': '崩溃堆栈信息', 'path': lambda: os.path.join(PathConfig.get_trae_root(), 'Crash Reports'), 'safe': True},
    {'name': '系统���存', 'desc': '系统级缓存数据', 'path': lambda: os.path.join(PathConfig.get_trae_root(), 'System Cache'), 'safe': True},
    {'name': 'Blob Store', 'desc': '二进制对象存储', 'path': lambda: os.path.join(PathConfig.get_trae_user(), 'globalStorage', 'blob storage'), 'safe': True},
    {'name': 'Service Worker', 'desc': 'Web Service Worker 缓存', 'path': lambda: os.path.join(PathConfig.get_trae_user(), 'serviceworkers'), 'safe': True},
    {'name': 'IndexedDB', 'desc': '浏览器 IndexedDB 数据库', 'path': lambda: os.path.join(PathConfig.get_trae_user(), 'IndexedDB'), 'safe': False},
    {'name': '本地存储', 'desc': 'LocalStorage 本地数据', 'path': lambda: os.path.join(PathConfig.get_trae_user(), 'Local Storage'), 'safe': False},
    {'name': '网站数据', 'desc': '网站 Cookie 和存储', 'path': lambda: os.path.join(PathConfig.get_trae_user(), 'Default', 'Web Data'), 'safe': False},
    {'name': 'Session Storage', 'desc': 'SessionStorage 会话数据', 'path': lambda: os.path.join(PathConfig.get_trae_user(), 'Session Storage'), 'safe': False},
    {'name': 'DOM Storage', 'desc': 'DOM 本地存储', 'path': lambda: os.path.join(PathConfig.get_trae_user(), 'DOMStorage'), 'safe': False},
    {'name': 'WebSQL', 'desc': 'WebSQL 数据库', 'path': lambda: os.path.join(PathConfig.get_trae_user(), 'databases'), 'safe': False},
    {'name': 'Cookies', 'desc': 'HTTP Cookies 文件', 'path': lambda: os.path.join(PathConfig.get_trae_user(), 'Default', 'Cookies'), 'safe': False},
    {'name': '媒体缓存', 'desc': '音视频临时缓存', 'path': lambda: os.path.join(PathConfig.get_trae_root(), 'Media Cache'), 'safe': True},
    {'name': '代码完成缓存', 'desc': '智能补全推荐缓存', 'path': lambda: os.path.join(PathConfig.get_trae_user(), 'globalStorage', 'ai-completion-cache'), 'safe': True},
    {'name': '开发工具', 'desc': '开发者工具数据', 'path': lambda: os.path.join(PathConfig.get_trae_user(), 'devtools'), 'safe': True},
    {'name': '扩展缓存', 'desc': '已安装扩展的缓存', 'path': lambda: os.path.join(PathConfig.get_app_dir(), 'globalStorage'), 'safe': True},
    {'name': '书签数据', 'desc': '本地保存的书签', 'path': lambda: os.path.join(PathConfig.get_trae_user(), 'Default', 'Bookmarks'), 'safe': False},
    {'name': '历史记录数据库', 'desc': '浏览历史数据库', 'path': lambda: os.path.join(PathConfig.get_trae_user(), 'Default', 'History'), 'safe': False},
]

# Settings items for export/import
SETTINGS_ITEMS = [
    {'name': 'settings.json', 'path': lambda: os.path.join(PathConfig.get_app_dir(), 'User', 'settings.json')},
    {'name': 'mcp.json', 'path': lambda: PathConfig.get_mcp_path()},
    {'name': 'keybindings.json', 'path': lambda: os.path.join(PathConfig.get_app_dir(), 'User', 'keybindings.json')},
    {'name': 'globalStorage', 'path': lambda: os.path.join(PathConfig.get_trae_user(), 'globalStorage')},
    {'name': 'workspaceStorage', 'path': lambda: os.path.join(PathConfig.get_trae_user(), 'workspaceStorage')},
    {'name': 'snippets', 'path': lambda: os.path.join(PathConfig.get_app_dir(), 'User', 'snippets')},
    {'name': 'rules', 'path': lambda: PathConfig.get_rules_path()},
]

# ============================================================================
# Utility Functions
# ============================================================================

def format_size(bytes_size: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f'{bytes_size:.2f} {unit}'
        bytes_size /= 1024
    return f'{bytes_size:.2f} TB'

def scan_dir_size(path: str) -> int:
    """扫描目录大小"""
    if not os.path.exists(path):
        return 0
    
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file(follow_symlinks=False):
                total += entry.stat(follow_symlinks=False).st_size
            elif entry.is_dir(follow_symlinks=False):
                total += scan_dir_size(entry.path)
    except (PermissionError, OSError):
        pass
    
    return total

def is_dark_mode() -> bool:
    """检测系统是否使用深色主题"""
    try:
        if sys.platform == 'win32':
            import winreg
            registry_path = r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize'
            registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path)
            value, _ = winreg.QueryValueEx(registry_key, 'AppsUseLightTheme')
            return value == 0
    except:
        pass
    return False

def open_folder(path: str) -> None:
    """打开文件夹"""
    if not os.path.exists(path):
        return
    
    try:
        if sys.platform == 'win32':
            os.startfile(path)
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', path])
        else:
            subprocess.Popen(['xdg-open', path])
    except:
        pass

# ============================================================================
# GUI Implementation
# ============================================================================

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTabWidget, QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
        QPushButton, QCheckBox, QLabel, QMessageBox, QProgressBar, QHeaderView,
        QFileDialog, QDialog, QScrollArea, QSpinBox, QComboBox, QDoubleSpinBox,
        QDateTimeEdit
    )
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QDateTime, QTimer
    from PyQt5.QtGui import QFont, QColor, QIcon, QStyleFactory
    
    PYQT5_AVAILABLE = True
    
    class ScanThread(QThread):
        """扫描线程"""
        scan_progress = pyqtSignal(int, str)
        scan_done = pyqtSignal(list)
        
        def __init__(self, scan_type: str, parent=None):
            super().__init__(parent)
            self.scan_type = scan_type
        
        def run(self):
            """运行扫描"""
            if self.scan_type == 'cache':
                items = self.scan_cache()
            elif self.scan_type == 'chat':
                items = self.scan_chat()
            elif self.scan_type == 'workspace':
                items = self.scan_workspace()
            elif self.scan_type == 'extension':
                items = self.scan_extension()
            else:
                items = []
            
            self.scan_done.emit(items)
        
        def scan_cache(self) -> List[Dict]:
            """扫描缓存"""
            items = []
            for idx, entry in enumerate(CACHE_ENTRIES):
                path = entry['path']()
                size = scan_dir_size(path)
                if size > 0 or os.path.exists(path):
                    items.append({
                        'name': entry['name'],
                        'desc': entry['desc'],
                        'path': path,
                        'size': size,
                        'safe': entry['safe'],
                        'checked': entry['safe']
                    })
                self.scan_progress.emit(idx, entry['name'])
            return items
        
        def scan_chat(self) -> List[Dict]:
            """扫描对话记录"""
            items = []
            chat_path = PathConfig.get_chat_sessions()
            
            if not os.path.exists(chat_path):
                return items
            
            try:
                for hash_dir in os.listdir(chat_path):
                    hash_path = os.path.join(chat_path, hash_dir)
                    if not os.path.isdir(hash_path):
                        continue
                    
                    for chat_file in os.listdir(hash_path):
                        if chat_file.endswith('.json'):
                            file_path = os.path.join(hash_path, chat_file)
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    chat_data = json.load(f)
                                    size = os.path.getsize(file_path)
                                    mtime = os.path.getmtime(file_path)
                                    mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                                    
                                    # Try to extract file information
                                    file_info = '未知'
                                    if isinstance(chat_data, dict) and 'messages' in chat_data:
                                        if chat_data['messages']:
                                            file_info = chat_data.get('file', '未知')
                                    
                                    items.append({
                                        'name': chat_file.replace('.json', ''),
                                        'path': file_path,
                                        'size': size,
                                        'time': mtime_str,
                                        'file': file_info,
                                        'checked': False
                                    })
                            except:
                                pass
            except:
                pass
            
            return items
        
        def scan_workspace(self) -> List[Dict]:
            """扫描工作区"""
            items = []
            userprofile = PathConfig.get_userprofile()
            
            # 传统 workspaceStorage
            ws_storage = PathConfig.get_workspace_storage()
            if os.path.exists(ws_storage):
                for folder in os.listdir(ws_storage):
                    folder_path = os.path.join(ws_storage, folder)
                    if os.path.isdir(folder_path):
                        try:
                            state_file = os.path.join(folder_path, 'workspace.json')
                            project_name = folder
                            project_path = '未知'
                            
                            if os.path.exists(state_file):
                                with open(state_file, 'r', encoding='utf-8') as f:
                                    state_data = json.load(f)
                                    if 'folder' in state_data:
                                        project_path = state_data['folder']
                                        project_name = os.path.basename(project_path)
                            
                            size = scan_dir_size(folder_path)
                            items.append({
                                'name': project_name,
                                'path': folder_path,
                                'project_path': project_path,
                                'size': size,
                                'source': 'workspaceStorage',
                                'checked': False
                            })
                        except:
                            pass
            
            # Worktrees
            for trae_dir in ['.trae-cn', '.trae']:
                worktrees_path = os.path.join(userprofile, trae_dir, 'worktrees')
                if os.path.exists(worktrees_path):
                    for folder in os.listdir(worktrees_path):
                        folder_path = os.path.join(worktrees_path, folder)
                        if os.path.isdir(folder_path):
                            size = scan_dir_size(folder_path)
                            items.append({
                                'name': folder,
                                'path': folder_path,
                                'project_path': folder_path,
                                'size': size,
                                'source': 'worktrees',
                                'checked': False
                            })
            
            return items
        
        def scan_extension(self) -> List[Dict]:
            """扫描扩展"""
            items = []
            ext_paths = PathConfig.get_extensions()
            
            for ext_path in ext_paths:
                if not os.path.exists(ext_path):
                    continue
                
                try:
                    for ext_dir in os.listdir(ext_path):
                        ext_full_path = os.path.join(ext_path, ext_dir)
                        if os.path.isdir(ext_full_path):
                            # Try to get package.json
                            pkg_file = os.path.join(ext_full_path, 'package.json')
                            size = scan_dir_size(ext_full_path)
                            
                            name = ext_dir
                            version = '未知'
                            publisher = '未知'
                            
                            if os.path.exists(pkg_file):
                                try:
                                    with open(pkg_file, 'r', encoding='utf-8') as f:
                                        pkg_data = json.load(f)
                                        name = pkg_data.get('displayName', name)
                                        version = pkg_data.get('version', version)
                                        publisher = pkg_data.get('publisher', publisher)
                                except:
                                    pass
                            
                            items.append({
                                'name': name,
                                'publisher': publisher,
                                'version': version,
                                'path': ext_full_path,
                                'size': size
                            })
                except:
                    pass
            
            return items
    
    class CleanThread(QThread):
        """清理线程"""
        clean_progress = pyqtSignal(int, str)
        clean_done = pyqtSignal(int, int)
        
        def __init__(self, items: List[Dict], parent=None):
            super().__init__(parent)
            self.items = items
        
        def run(self):
            """运行清理"""
            cleaned = 0
            freed = 0
            
            for idx, item in enumerate(self.items):
                path = item.get('path', '')
                if path and os.path.exists(path):
                    try:
                        size_before = scan_dir_size(path) if os.path.isdir(path) else os.path.getsize(path)
                        
                        if os.path.isdir(path):
                            shutil.rmtree(path, ignore_errors=True)
                        else:
                            os.remove(path)
                        
                        cleaned += 1
                        freed += size_before
                        self.clean_progress.emit(idx, item.get('name', ''))
                    except:
                        pass
            
            self.clean_done.emit(cleaned, freed)
    
    class MainWindow(QMainWindow):
        """主窗口"""
        
        def __init__(self):
            super().__init__()
            self.app_config = load_app_config()
            self.base_font_size = self.app_config.get('font_size', 10)
            
            # Initialize window
            self.setWindowTitle(f'Trae Cache Cleaner - {VERSION}')
            self.setWindowIcon(self.get_app_icon())
            self.setGeometry(100, 100, 1000, 700)
            
            # Set taskbar icon on Windows
            if sys.platform == 'win32':
                try:
                    icon_path = self.get_icon_path()
                    if icon_path and os.path.exists(icon_path):
                        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f'Trae.CacheCleaner.{VERSION}')
                except:
                    pass
            
            # Setup theme and UI
            self.setup_theme()
            self.init_ui()
            self.start_scans()
            
            # Restore window geometry
            if self.app_config.get('window_geometry'):
                try:
                    geo = self.app_config['window_geometry']
                    self.setGeometry(geo[0], geo[1], geo[2], geo[3])
                except:
                    pass
        
        def get_icon_path(self) -> Optional[str]:
            """获取图标路径"""
            current_dir = get_current_directory()
            candidates = [
                os.path.join(current_dir, 'TraeCacheCleaner.ico'),
                os.path.join(os.path.dirname(current_dir), 'TraeCacheCleaner.ico'),
            ]
            for icon_path in candidates:
                if os.path.exists(icon_path):
                    return icon_path
            return None
        
        def get_app_icon(self) -> QIcon:
            """获取应用图标"""
            icon_path = self.get_icon_path()
            if icon_path:
                return QIcon(icon_path)
            return QIcon()
        
        def setup_theme(self):
            """设置主题"""
            dark = is_dark_mode()
            
            if dark:
                # Dark theme
                bg_color = '#1e1e1e'
                text_color = '#e0e0e0'
                button_bg = '#2d2d2d'
                button_hover = '#3d3d3d'
            else:
                # Light theme
                bg_color = '#ffffff'
                text_color = '#000000'
                button_bg = '#f0f0f0'
                button_hover = '#e0e0e0'
            
            stylesheet = f"""
                QMainWindow, QDialog, QWidget {{
                    background-color: {bg_color};
                    color: {text_color};
                }}
                QPushButton {{
                    background-color: {button_bg};
                    color: {text_color};
                    border: 1px solid {button_hover};
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-size: {self.base_font_size}pt;
                }}
                QPushButton:hover {{
                    background-color: {button_hover};
                }}
                QListWidget, QTableWidget {{
                    background-color: {bg_color};
                    color: {text_color};
                    border: 1px solid {button_hover};
                }}
                QCheckBox, QLabel {{
                    color: {text_color};
                }}
            """
            
            self.setStyleSheet(stylesheet)
        
        def init_ui(self):
            """初始化UI"""
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            main_layout = QVBoxLayout()
            
            # Top info bar with font size
            top_bar = QHBoxLayout()
            
            self.safe_mode_check = QCheckBox('🛡️ 防呆模式（推荐）')
            self.safe_mode_check.setChecked(self.app_config.get('safe_mode', True))
            self.safe_mode_check.stateChanged.connect(self.toggle_safe_mode)
            self.safe_mode_check.setFont(self.get_font(self.base_font_size))
            top_bar.addWidget(self.safe_mode_check)
            
            top_bar.addStretch()
            
            self.selected_label = QLabel('已选择: 0 B (0 项)')
            self.selected_label.setFont(self.get_font(self.base_font_size + 1, bold=True))
            top_bar.addWidget(self.selected_label)
            
            font_label = QLabel('字体大小:')
            font_label.setFont(self.get_font(self.base_font_size))
            top_bar.addWidget(font_label)
            
            self.font_size_spin = QSpinBox()
            self.font_size_spin.setMinimum(8)
            self.font_size_spin.setMaximum(16)
            self.font_size_spin.setValue(self.base_font_size)
            self.font_size_spin.setFont(self.get_font(self.base_font_size))
            self.font_size_spin.valueChanged.connect(self.change_font_size)
            top_bar.addWidget(self.font_size_spin)
            
            main_layout.addLayout(top_bar)
            
            # Tabs
            self.tabs = QTabWidget()
            self.tabs.setFont(self.get_font(self.base_font_size))
            
            self.init_cache_tab()
            self.init_chat_tab()
            self.init_workspace_tab()
            self.init_extension_tab()
            self.init_mcp_tab()
            self.init_settings_tab()
            
            main_layout.addWidget(self.tabs)
            
            # Progress bar
            self.progress = QProgressBar()
            self.progress.setFont(self.get_font(self.base_font_size))
            main_layout.addWidget(self.progress)
            
            central_widget.setLayout(main_layout)
        
        def get_font(self, size: int, bold: bool = False) -> QFont:
            """获取字体"""
            font = QFont()
            font.setPointSize(size)
            if bold:
                font.setBold(True)
            return font
        
        def change_font_size(self, size: int):
            """改变字体大小"""
            self.base_font_size = size
            self.app_config['font_size'] = size
            save_app_config(self.app_config)
            self.update_all_fonts()
        
        def update_all_fonts(self):
            """更新所有字体"""
            self.setup_theme()
            # Update all widgets
            self.safe_mode_check.setFont(self.get_font(self.base_font_size))
            self.selected_label.setFont(self.get_font(self.base_font_size + 1, bold=True))
            self.font_size_spin.setFont(self.get_font(self.base_font_size))
            self.tabs.setFont(self.get_font(self.base_font_size))
        
        def init_cache_tab(self):
            """初始化缓存标签页"""
            widget = QWidget()
            layout = QVBoxLayout()
            
            # List widget
            self.cache_list = QListWidget()
            self.cache_list.setFont(self.get_font(self.base_font_size))
            layout.addWidget(self.cache_list)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            select_safe_btn = QPushButton('仅选安全项')
            select_safe_btn.setFont(self.get_font(self.base_font_size))
            select_safe_btn.clicked.connect(self.select_only_safe)
            button_layout.addWidget(select_safe_btn)
            
            select_all_btn = QPushButton('全选')
            select_all_btn.setFont(self.get_font(self.base_font_size))
            select_all_btn.clicked.connect(self.select_all_cache)
            button_layout.addWidget(select_all_btn)
            
            deselect_all_btn = QPushButton('全不选')
            deselect_all_btn.setFont(self.get_font(self.base_font_size))
            deselect_all_btn.clicked.connect(lambda: self.select_all_cache(False))
            button_layout.addWidget(deselect_all_btn)
            
            clean_btn = QPushButton('🗑️ 清理选中')
            clean_btn.setFont(self.get_font(self.base_font_size))
            clean_btn.clicked.connect(self.clean_cache)
            button_layout.addWidget(clean_btn)
            
            layout.addLayout(button_layout)
            
            widget.setLayout(layout)
            self.tabs.addTab(widget, '缓存清理')
        
        def init_chat_tab(self):
            """初始化对话记录标签页"""
            widget = QWidget()
            layout = QVBoxLayout()
            
            # Sort buttons
            sort_layout = QHBoxLayout()
            
            time_btn = QPushButton('按时间排序')
            time_btn.setFont(self.get_font(self.base_font_size))
            time_btn.clicked.connect(lambda: self.sort_chat('time'))
            sort_layout.addWidget(time_btn)
            
            size_btn = QPushButton('按大小排序')
            size_btn.setFont(self.get_font(self.base_font_size))
            size_btn.clicked.connect(lambda: self.sort_chat('size'))
            sort_layout.addWidget(size_btn)
            
            name_btn = QPushButton('按名称排序')
            name_btn.setFont(self.get_font(self.base_font_size))
            name_btn.clicked.connect(lambda: self.sort_chat('name'))
            sort_layout.addWidget(name_btn)
            
            sort_layout.addStretch()
            layout.addLayout(sort_layout)
            
            # List widget
            self.chat_list = QListWidget()
            self.chat_list.setFont(self.get_font(self.base_font_size))
            layout.addWidget(self.chat_list)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            select_all_btn = QPushButton('全选')
            select_all_btn.setFont(self.get_font(self.base_font_size))
            select_all_btn.clicked.connect(self.select_all_chat)
            button_layout.addWidget(select_all_btn)
            
            deselect_all_btn = QPushButton('全不选')
            deselect_all_btn.setFont(self.get_font(self.base_font_size))
            deselect_all_btn.clicked.connect(lambda: self.select_all_chat(False))
            button_layout.addWidget(deselect_all_btn)
            
            clean_btn = QPushButton('🗑️ 删除选中')
            clean_btn.setFont(self.get_font(self.base_font_size))
            clean_btn.clicked.connect(self.clean_chat)
            button_layout.addWidget(clean_btn)
            
            layout.addLayout(button_layout)
            
            widget.setLayout(layout)
            self.tabs.addTab(widget, '对话记录')
        
        def init_workspace_tab(self):
            """初始化工作区标签页"""
            widget = QWidget()
            layout = QVBoxLayout()
            
            # List widget
            self.workspace_list = QListWidget()
            self.workspace_list.setFont(self.get_font(self.base_font_size))
            layout.addWidget(self.workspace_list)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            select_all_btn = QPushButton('全选')
            select_all_btn.setFont(self.get_font(self.base_font_size))
            select_all_btn.clicked.connect(self.select_all_workspace)
            button_layout.addWidget(select_all_btn)
            
            deselect_all_btn = QPushButton('全不选')
            deselect_all_btn.setFont(self.get_font(self.base_font_size))
            deselect_all_btn.clicked.connect(lambda: self.select_all_workspace(False))
            button_layout.addWidget(deselect_all_btn)
            
            clean_btn = QPushButton('🗑️ 删除选中')
            clean_btn.setFont(self.get_font(self.base_font_size))
            clean_btn.clicked.connect(self.clean_workspace)
            button_layout.addWidget(clean_btn)
            
            layout.addLayout(button_layout)
            
            widget.setLayout(layout)
            self.tabs.addTab(widget, '工作区')
        
        def init_extension_tab(self):
            """初始化扩展标签页"""
            widget = QWidget()
            layout = QVBoxLayout()
            
            # Table
            self.extension_table = QTableWidget()
            self.extension_table.setColumnCount(5)
            self.extension_table.setHorizontalHeaderLabels(['名称', '发布者', '版本', '大小', '操作'])
            self.extension_table.setFont(self.get_font(self.base_font_size))
            self.extension_table.horizontalHeader().setStretchLastSection(True)
            layout.addWidget(self.extension_table)
            
            widget.setLayout(layout)
            self.tabs.addTab(widget, '扩展')
        
        def init_mcp_tab(self):
            """初始化 MCP 标签页"""
            widget = QWidget()
            layout = QVBoxLayout()
            
            # Table
            self.mcp_table = QTableWidget()
            self.mcp_table.setColumnCount(3)
            self.mcp_table.setHorizontalHeaderLabels(['名称', '启用', '操作'])
            self.mcp_table.setFont(self.get_font(self.base_font_size))
            layout.addWidget(self.mcp_table)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            save_btn = QPushButton('💾 保存配置')
            save_btn.setFont(self.get_font(self.base_font_size))
            save_btn.clicked.connect(self.save_mcp_config)
            button_layout.addWidget(save_btn)
            
            open_btn = QPushButton('📁 打开配置目录')
            open_btn.setFont(self.get_font(self.base_font_size))
            open_btn.clicked.connect(self.open_mcp_dir)
            button_layout.addWidget(open_btn)
            
            button_layout.addStretch()
            layout.addLayout(button_layout)
            
            widget.setLayout(layout)
            self.tabs.addTab(widget, 'MCP')
        
        def init_settings_tab(self):
            """初始化设置标签页"""
            widget = QWidget()
            layout = QVBoxLayout()
            
            # Info section
            info_label = QLabel('💡 功能说明：\n'
                              '• 悬停提示 - 将鼠标悬停在项目上可查看详细信息\n'
                              '• 路径点击 - 支持双击或单击打开文件夹\n'
                              '• 防呆模式 - 默认启用，保护重要数据\n'
                              '• 字体大小 - 支持 8-16pt 调整\n'
                              '• 主题适配 - 自动检测系统深色/浅色主题')
            info_label.setFont(self.get_font(self.base_font_size))
            info_label.setWordWrap(True)
            layout.addWidget(info_label)
            
            layout.addSpacing(20)
            
            # Export/Import section
            export_btn = QPushButton('📤 导出设置')
            export_btn.setFont(self.get_font(self.base_font_size))
            export_btn.clicked.connect(self.export_settings)
            layout.addWidget(export_btn)
            
            import_btn = QPushButton('📥 导入设置')
            import_btn.setFont(self.get_font(self.base_font_size))
            import_btn.clicked.connect(self.import_settings)
            layout.addWidget(import_btn)
            
            layout.addStretch()
            
            widget.setLayout(layout)
            self.tabs.addTab(widget, '设置')
        
        def start_scans(self):
            """启动扫描"""
            self.progress.setValue(0)
            
            # Scan cache
            cache_thread = ScanThread('cache')
            cache_thread.scan_done.connect(self.on_cache_scan_done)
            cache_thread.start()
            
            # Scan chat
            chat_thread = ScanThread('chat')
            chat_thread.scan_done.connect(self.on_chat_scan_done)
            chat_thread.start()
            
            # Scan workspace
            ws_thread = ScanThread('workspace')
            ws_thread.scan_done.connect(self.on_workspace_scan_done)
            ws_thread.start()
            
            # Scan extensions
            ext_thread = ScanThread('extension')
            ext_thread.scan_done.connect(self.on_extension_scan_done)
            ext_thread.start()
            
            # Load MCP
            self.load_mcp_config()
        
        def on_cache_scan_done(self, items: List[Dict]):
            """缓存扫描完成"""
            self.cache_items = items
            self.update_cache_list()
        
        def on_chat_scan_done(self, items: List[Dict]):
            """对话记录扫描完成"""
            self.chat_items = items
            self.update_chat_list()
        
        def on_workspace_scan_done(self, items: List[Dict]):
            """工作区扫描完成"""
            self.workspace_items = items
            self.update_workspace_list()
        
        def on_extension_scan_done(self, items: List[Dict]):
            """扩展扫描完成"""
            self.extension_items = items
            self.update_extension_table()
        
        def update_cache_list(self):
            """更新缓存列表"""
            self.cache_list.clear()
            
            for item in self.cache_items:
                text = f"{item['name']} ({format_size(item['size'])})"
                
                # Safety indicator
                if item['safe']:
                    text = '✅ ' + text
                else:
                    text = '⚠️ ' + text
                
                list_item = QListWidgetItem(text)
                list_item.setFont(self.get_font(self.base_font_size))
                
                checkbox = QCheckBox()
                checkbox.setChecked(item.get('checked', False))
                checkbox.stateChanged.connect(lambda state, idx=self.cache_items.index(item):
                                            self.update_item_checked(idx, state, 'cache'))
                
                # Tooltip with path
                tooltip = f"{item['name']}\n{item['desc']}\n\n📁 {item['path']}\n大小: {format_size(item['size'])}"
                list_item.setToolTip(tooltip)
                
                list_item.setCheckState(Qt.Checked if item.get('checked', False) else Qt.Unchecked)
                self.cache_list.addItem(list_item)
            
            self.update_selected_label()
        
        def update_selected_label(self):
            """更新已选择标签"""
            total_size = 0
            total_count = 0
            
            if hasattr(self, 'cache_items'):
                for item in self.cache_items:
                    if item.get('checked', False):
                        total_size += item.get('size', 0)
                        total_count += 1
            
            if hasattr(self, 'chat_items'):
                for item in self.chat_items:
                    if item.get('checked', False):
                        total_size += item.get('size', 0)
                        total_count += 1
            
            if hasattr(self, 'workspace_items'):
                for item in self.workspace_items:
                    if item.get('checked', False):
                        total_size += item.get('size', 0)
                        total_count += 1
            
            self.selected_label.setText(f'已选择: {format_size(total_size)} ({total_count} 项)')
        
        def sort_chat(self, sort_by: str):
            """排序对话记录"""
            if not hasattr(self, 'chat_items'):
                return
            
            if sort_by == 'time':
                self.chat_items.sort(key=lambda x: x.get('time', ''), reverse=True)
            elif sort_by == 'size':
                self.chat_items.sort(key=lambda x: x.get('size', 0), reverse=True)
            elif sort_by == 'name':
                self.chat_items.sort(key=lambda x: x.get('name', ''))
            
            self.update_chat_list()
        
        def update_chat_list(self):
            """更新对话记录列表"""
            self.chat_list.clear()
            
            if not hasattr(self, 'chat_items'):
                return
            
            for item in self.chat_items:
                text = f"📝 {item['name']} ({format_size(item['size'])})"
                
                list_item = QListWidgetItem(text)
                list_item.setFont(self.get_font(self.base_font_size))
                
                tooltip = f"{item['name']}\n\n📁 {item['path']}\n大小: {format_size(item['size'])}\n时间: {item.get('time', '未知')}"
                list_item.setToolTip(tooltip)
                
                list_item.setCheckState(Qt.Checked if item.get('checked', False) else Qt.Unchecked)
                self.chat_list.addItem(list_item)
            
            self.update_selected_label()
        
        def update_workspace_list(self):
            """更新工作区列表"""
            self.workspace_list.clear()
            
            if not hasattr(self, 'workspace_items'):
                return
            
            for item in self.workspace_items:
                text = f"🏗️ {item['name']} ({format_size(item['size'])})"
                
                list_item = QListWidgetItem(text)
                list_item.setFont(self.get_font(self.base_font_size))
                
                project_path = item.get('project_path', '未知')
                tooltip = f"{item['name']}\n\n📁 {item['path']}\n项目: {project_path}\n大小: {format_size(item['size'])}"
                list_item.setToolTip(tooltip)
                
                list_item.setCheckState(Qt.Checked if item.get('checked', False) else Qt.Unchecked)
                self.workspace_list.addItem(list_item)
            
            self.update_selected_label()
        
        def update_extension_table(self):
            """更新扩展表格"""
            self.extension_table.setRowCount(len(self.extension_items))
            
            for row, item in enumerate(self.extension_items):
                # Name
                name_item = QTableWidgetItem(item['name'])
                name_item.setFont(self.get_font(self.base_font_size))
                self.extension_table.setItem(row, 0, name_item)
                
                # Publisher
                pub_item = QTableWidgetItem(item['publisher'])
                pub_item.setFont(self.get_font(self.base_font_size))
                self.extension_table.setItem(row, 1, pub_item)
                
                # Version
                ver_item = QTableWidgetItem(item['version'])
                ver_item.setFont(self.get_font(self.base_font_size))
                self.extension_table.setItem(row, 2, ver_item)
                
                # Size
                size_item = QTableWidgetItem(format_size(item['size']))
                size_item.setFont(self.get_font(self.base_font_size))
                self.extension_table.setItem(row, 3, size_item)
                
                # Open button
                btn = QPushButton('📁 打开')
                btn.setFont(self.get_font(self.base_font_size))
                btn.clicked.connect(lambda checked, path=item['path']: open_folder(path))
                self.extension_table.setCellWidget(row, 4, btn)
        
        def load_mcp_config(self):
            """加载 MCP 配置"""
            mcp_path = PathConfig.get_mcp_path()
            self.mcp_config = {}
            
            if os.path.exists(mcp_path):
                try:
                    with open(mcp_path, 'r', encoding='utf-8') as f:
                        self.mcp_config = json.load(f)
                except:
                    pass
            
            self.update_mcp_table()
        
        def update_mcp_table(self):
            """更新 MCP 表格"""
            mcps = self.mcp_config.get('mcpServers', {})
            self.mcp_table.setRowCount(len(mcps))
            
            for row, (name, config) in enumerate(mcps.items()):
                # Name
                name_item = QTableWidgetItem(name)
                name_item.setFont(self.get_font(self.base_font_size))
                self.mcp_table.setItem(row, 0, name_item)
                
                # Enabled
                enabled = config.get('enabled', True)
                checkbox = QCheckBox()
                checkbox.setChecked(enabled)
                checkbox.stateChanged.connect(lambda state, r=row: self.update_mcp_enabled(r, state))
                self.mcp_table.setCellWidget(row, 1, checkbox)
                
                # Open button
                mcp_dir = PathConfig.get_app_dir()
                btn = QPushButton('📁 打开')
                btn.setFont(self.get_font(self.base_font_size))
                btn.clicked.connect(lambda checked, path=mcp_dir: open_folder(path))
                self.mcp_table.setCellWidget(row, 2, btn)
        
        def select_all_cache(self, check: bool = True):
            """全选/全不选缓存"""
            for idx, item in enumerate(self.cache_items):
                item['checked'] = check
                self.cache_list.item(idx).setCheckState(Qt.Checked if check else Qt.Unchecked)
            
            self.update_selected_label()
        
        def select_all_chat(self, check: bool = True):
            """全选/全不选对话记录"""
            if not hasattr(self, 'chat_items'):
                return
            
            for idx, item in enumerate(self.chat_items):
                item['checked'] = check
                self.chat_list.item(idx).setCheckState(Qt.Checked if check else Qt.Unchecked)
            
            self.update_selected_label()
        
        def select_all_workspace(self, check: bool = True):
            """全选/全不选工作区"""
            if not hasattr(self, 'workspace_items'):
                return
            
            for idx, item in enumerate(self.workspace_items):
                item['checked'] = check
                self.workspace_list.item(idx).setCheckState(Qt.Checked if check else Qt.Unchecked)
            
            self.update_selected_label()
        
        def select_only_safe(self):
            """仅选安全项"""
            for idx, item in enumerate(self.cache_items):
                item['checked'] = item['safe']
                self.cache_list.item(idx).setCheckState(Qt.Checked if item['safe'] else Qt.Unchecked)
            
            self.update_selected_label()
        
        def toggle_safe_mode(self, state: int):
            """切换防呆模式"""
            enabled = state == Qt.Checked
            
            if not enabled:
                # Show warning
                reply = self.msg_warning('⚠️ 警告', 
                                        '您即将关闭防呆模式\n\n关闭后可以清理危险项，可能导致数据丢失！\n\n确定要继续吗？',
                                        QMessageBox.Ok | QMessageBox.Cancel,
                                        QMessageBox.Cancel)
                
                if reply != QMessageBox.Ok:
                    self.safe_mode_check.setChecked(True)
                    return
            
            self.app_config['safe_mode'] = enabled
            save_app_config(self.app_config)
            
            # Update cache list
            for idx, item in enumerate(self.cache_items):
                if not item['safe']:
                    list_item = self.cache_list.item(idx)
                    if list_item:
                        list_item.setCheckState(Qt.Checked if enabled else Qt.Unchecked)
        
        def clean_cache(self):
            """清理缓存"""
            to_clean = [item for item in self.cache_items if item.get('checked', False)]
            
            if not to_clean:
                self.msg_info('提示', '请先选择要清理的缓存项')
                return
            
            # Confirm
            reply = self.msg_confirm('⚠️ 确认清理', f'确定删除选中的 {len(to_clean)} 项缓存？\n\n清理后无法恢复！')
            if reply != QMessageBox.Ok:
                return
            
            # Clean
            thread = CleanThread(to_clean)
            thread.clean_done.connect(self.on_clean_done)
            thread.start()
        
        def clean_chat(self):
            """清理对话记录"""
            if not hasattr(self, 'chat_items'):
                return
            
            to_clean = [item for item in self.chat_items if item.get('checked', False)]
            
            if not to_clean:
                self.msg_info('提示', '请先选择要删除的对话记录')
                return
            
            # Confirm
            reply = self.msg_confirm('⚠️ 确认删除', f'确定删除选中的 {len(to_clean)} 条对话记录？\n\n删除后无法恢复！')
            if reply != QMessageBox.Ok:
                return
            
            # Clean
            thread = CleanThread(to_clean)
            thread.clean_done.connect(self.on_chat_clean_done)
            thread.start()
        
        def clean_workspace(self):
            """清理工作区"""
            if not hasattr(self, 'workspace_items'):
                return
            
            to_clean = [item for item in self.workspace_items if item.get('checked', False)]
            
            if not to_clean:
                self.msg_info('提示', '请先选择要删除的工作区')
                return
            
            # Confirm
            reply = self.msg_confirm('⚠️ 确认删除', f'确定删除选中的 {len(to_clean)} 个工作区？\n\n删除后无法恢复！')
            if reply != QMessageBox.Ok:
                return
            
            # Clean
            thread = CleanThread(to_clean)
            thread.clean_done.connect(self.on_workspace_clean_done)
            thread.start()
        
        def on_clean_done(self, cleaned: int, freed: int):
            """清理完成"""
            self.msg_info('✅ 完成', f'已清理 {cleaned} 项，释放空间 {format_size(freed)}')
            self.start_scans()
        
        def on_chat_clean_done(self, cleaned: int, freed: int):
            """对话记录清理完成"""
            self.msg_info('✅ 完成', f'已删除 {cleaned} 条对话记录，释放空间 {format_size(freed)}')
            self.start_scans()
        
        def on_workspace_clean_done(self, cleaned: int, freed: int):
            """工作区清理完成"""
            self.msg_info('✅ 完成', f'已删除 {cleaned} 个工作区，释放空间 {format_size(freed)}')
            self.start_scans()
        
        def update_item_checked(self, idx: int, state: int, list_type: str):
            """更新项目勾选状态"""
            checked = state == Qt.Checked
            
            if list_type == 'cache':
                if idx < len(self.cache_items):
                    self.cache_items[idx]['checked'] = checked
            elif list_type == 'chat':
                if hasattr(self, 'chat_items') and idx < len(self.chat_items):
                    self.chat_items[idx]['checked'] = checked
            elif list_type == 'workspace':
                if hasattr(self, 'workspace_items') and idx < len(self.workspace_items):
                    self.workspace_items[idx]['checked'] = checked
            
            self.update_selected_label()
        
        def update_mcp_enabled(self, row: int, state: int):
            """更新 MCP 启用状态"""
            enabled = state == Qt.Checked
            mcps = list(self.mcp_config.get('mcpServers', {}).keys())
            
            if row < len(mcps):
                name = mcps[row]
                if name in self.mcp_config['mcpServers']:
                    self.mcp_config['mcpServers'][name]['enabled'] = enabled
        
        def save_mcp_config(self):
            """保存 MCP 配置"""
            mcp_path = PathConfig.get_mcp_path()
            
            try:
                os.makedirs(os.path.dirname(mcp_path), exist_ok=True)
                with open(mcp_path, 'w', encoding='utf-8') as f:
                    json.dump(self.mcp_config, f, ensure_ascii=False, indent=2)
                
                self.msg_info('✅ 成功', 'MCP 配置已保存\n\n重启 Trae IDE 使设置生效')
            except Exception as e:
                self.msg_info('❌ 错误', f'保存失败：{str(e)}')
        
        def open_mcp_dir(self):
            """打开 MCP 目录"""
            mcp_dir = os.path.dirname(PathConfig.get_mcp_path())
            open_folder(mcp_dir)
        
        def export_settings(self):
            """导出设置"""
            export_dir = QFileDialog.getExistingDirectory(self, '选择导出目录')
            if not export_dir:
                return
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = os.path.join(export_dir, f'trae_backup_{timestamp}')
            os.makedirs(backup_dir, exist_ok=True)
            
            # Export each setting item
            for setting in SETTINGS_ITEMS:
                source_path = setting['path']()
                if not os.path.exists(source_path):
                    continue
                
                dest_path = os.path.join(backup_dir, setting['name'])
                try:
                    if os.path.isdir(source_path):
                        shutil.copytree(source_path, dest_path, ignore_errors=True)
                    else:
                        shutil.copy2(source_path, dest_path)
                except:
                    pass
            
            # Save metadata
            metadata = {
                'timestamp': timestamp,
                'version': VERSION,
                'items': [s['name'] for s in SETTINGS_ITEMS]
            }
            
            with open(os.path.join(backup_dir, 'metadata.json'), 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            self.msg_info('✅ 导出完成', f'设置已导出到：\n{backup_dir}')
        
        def import_settings(self):
            """导入设置"""
            import_dir = QFileDialog.getExistingDirectory(self, '选择导入目录')
            if not import_dir:
                return
            
            # Verify metadata
            metadata_path = os.path.join(import_dir, 'metadata.json')
            if not os.path.exists(metadata_path):
                self.msg_info('❌ 错误', '无效的备份目录，缺少 metadata.json')
                return
            
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            except:
                self.msg_info('❌ 错误', '无法读取备份信息')
                return
            
            # Confirm import
            reply = self.msg_confirm('确认导入', f'确定导入以下设置？\n\n{", ".join(metadata.get("items", []))}\n\n这将覆盖现有设置！')
            if reply != QMessageBox.Ok:
                return
            
            # Import
            for setting in SETTINGS_ITEMS:
                source_path = os.path.join(import_dir, setting['name'])
                if not os.path.exists(source_path):
                    continue
                
                dest_path = setting['path']()
                try:
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    
                    if os.path.isdir(source_path):
                        if os.path.exists(dest_path):
                            shutil.rmtree(dest_path, ignore_errors=True)
                        shutil.copytree(source_path, dest_path)
                    else:
                        shutil.copy2(source_path, dest_path)
                except:
                    pass
            
            self.msg_info('✅ 导入完成', '设置已导入，请重启 Trae IDE 使其生效')
        
        def msg_info(self, title: str, text: str):
            """信息对话框"""
            msg = QMessageBox(self)
            msg.setWindowTitle(title)
            msg.setText(text)
            msg.setIcon(QMessageBox.Information)
            msg.setFont(self.get_font(self.base_font_size))
            msg.exec_()
        
        def msg_warning(self, title: str, text: str, buttons=QMessageBox.Ok, default=QMessageBox.Ok):
            """警告对话框"""
            msg = QMessageBox(self)
            msg.setWindowTitle(title)
            msg.setText(text)
            msg.setIcon(QMessageBox.Warning)
            msg.setStandardButtons(buttons)
            msg.setDefaultButton(default)
            msg.setFont(self.get_font(self.base_font_size))
            return msg.exec_()
        
        def msg_confirm(self, title: str, text: str):
            """确认对话框"""
            msg = QMessageBox(self)
            msg.setWindowTitle(title)
            msg.setText(text)
            msg.setIcon(QMessageBox.Question)
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            msg.setDefaultButton(QMessageBox.Cancel)
            msg.setFont(self.get_font(self.base_font_size))
            return msg.exec_()
        
        def closeEvent(self, event):
            """窗口关闭事件"""
            # Save window geometry
            geo = self.geometry()
            self.app_config['window_geometry'] = [geo.x(), geo.y(), geo.width(), geo.height()]
            save_app_config(self.app_config)
            event.accept()
    
    def run_gui():
        """运行 GUI"""
        app = QApplication(sys.argv)
        app.setStyle(QStyleFactory.create('Fusion'))
        
        window = MainWindow()
        window.show()
        
        sys.exit(app.exec_())

except ImportError:
    PYQT5_AVAILABLE = False

# ============================================================================
# CLI Implementation
# ============================================================================

def cli_print_banner():
    """打印横幅"""
    print(f'\n{"=" * 50}')
    print(f'  TraeCacheCleaner {VERSION}')
    print(f'{"=" * 50}\n')

def cli_print_menu():
    """打印菜单"""
    print('\n请选择操作：')
    print('1. 扫描缓存')
    print('2. 清理安全项')
    print('3. 清理选中项')
    print('4. 导出设置')
    print('5. 导入设置')
    print('0. 退出')
    print()

def cli_scan_cache():
    """CLI 扫描缓存"""
    items = []
    print('正在扫描缓存...\n')
    
    for entry in CACHE_ENTRIES:
        path = entry['path']()
        size = scan_dir_size(path)
        if size > 0 or os.path.exists(path):
            items.append({
                'name': entry['name'],
                'path': path,
                'size': size,
                'safe': entry['safe'],
                'checked': False
            })
    
    return items

def cli_print_cache_status(items):
    """打印缓存状态"""
    print(f'{"序号":<5} {"名称":<20} {"安全":<5} {"大小":<15}')
    print('-' * 50)
    
    for idx, item in enumerate(items):
        safe_str = '✅' if item['safe'] else '⚠️'
        print(f'{idx:<5} {item["name"]:<20} {safe_str:<5} {format_size(item["size"]):<15}')
    
    print()

def cli_toggle_selection(items):
    """CLI 切换选择"""
    while True:
        selection = input('输入要选择的序号 (逗号分隔，或 "all" 全选，"safe" 仅安全项，"none" 全不选)：').strip()
        
        if selection.lower() == 'all':
            for item in items:
                item['checked'] = True
            print('已全选所有项\n')
            break
        elif selection.lower() == 'safe':
            for item in items:
                item['checked'] = item['safe']
            print('已选择所有安全项\n')
            break
        elif selection.lower() == 'none':
            for item in items:
                item['checked'] = False
            print('已取消所有选择\n')
            break
        else:
            try:
                indices = [int(x.strip()) for x in selection.split(',')]
                for idx in indices:
                    if 0 <= idx < len(items):
                        items[idx]['checked'] = not items[idx]['checked']
                
                # Print updated status
                for item in items:
                    checked_str = '☑️' if item['checked'] else '☐'
                    safe_str = '✅' if item['safe'] else '⚠️'
                    print(f'{checked_str} {item["name"]:<20} {safe_str}')
                
                print()
                break
            except:
                print('输入无效，请重试\n')

def cli_delete_path(path: str) -> int:
    """删除路径"""
    try:
        size = 0
        if os.path.isdir(path):
            size = scan_dir_size(path)
            shutil.rmtree(path, ignore_errors=True)
        elif os.path.isfile(path):
            size = os.path.getsize(path)
            os.remove(path)
        return size
    except:
        return 0

def cli_clean_selected(items):
    """CLI 清理选中项"""
    to_clean = [item for item in items if item.get('checked', False)]
    
    if not to_clean:
        print('没有选择任何项\n')
        return
    
    print(f'\n将清理以下 {len(to_clean)} 项：')
    for item in to_clean:
        print(f'  - {item["name"]} ({format_size(item["size"])})')
    
    confirm = input('\n确定要清理吗? (y/n): ').strip().lower()
    if confirm != 'y':
        print('已取消\n')
        return
    
    print('\n正在清理...')
    cleaned = 0
    freed = 0
    
    for item in to_clean:
        size = cli_delete_path(item['path'])
        if size > 0:
            cleaned += 1
            freed += size
            print(f'✓ {item["name"]}')
    
    print(f'\n清理完成！已清理 {cleaned} 项，释放 {format_size(freed)} 空间\n')

def cli_export_settings():
    """CLI 导出设置"""
    export_dir = input('输入导出目录路径：').strip()
    
    if not os.path.exists(export_dir):
        print('目录不存在\n')
        return
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join(export_dir, f'trae_backup_{timestamp}')
    os.makedirs(backup_dir, exist_ok=True)
    
    for setting in SETTINGS_ITEMS:
        source_path = setting['path']()
        if not os.path.exists(source_path):
            continue
        
        dest_path = os.path.join(backup_dir, setting['name'])
        try:
            if os.path.isdir(source_path):
                shutil.copytree(source_path, dest_path, ignore_errors=True)
            else:
                shutil.copy2(source_path, dest_path)
            print(f'✓ {setting["name"]}')
        except:
            pass
    
    print(f'\n设置已导出到：{backup_dir}\n')

def cli_import_settings():
    """CLI 导入设置"""
    import_dir = input('输入备份目录路径：').strip()
    
    if not os.path.exists(import_dir):
        print('目录不存在\n')
        return
    
    metadata_path = os.path.join(import_dir, 'metadata.json')
    if not os.path.exists(metadata_path):
        print('无效的备份目录\n')
        return
    
    for setting in SETTINGS_ITEMS:
        source_path = os.path.join(import_dir, setting['name'])
        if not os.path.exists(source_path):
            continue
        
        dest_path = setting['path']()
        try:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            
            if os.path.isdir(source_path):
                if os.path.exists(dest_path):
                    shutil.rmtree(dest_path, ignore_errors=True)
                shutil.copytree(source_path, dest_path)
            else:
                shutil.copy2(source_path, dest_path)
            print(f'✓ {setting["name"]}')
        except:
            pass
    
    print('\n设置已导入，请重启 Trae IDE\n')

def run_cli():
    """运行 CLI"""
    cli_print_banner()
    
    items = []
    
    while True:
        cli_print_menu()
        choice = input('输入选择 (0-5)：').strip()
        
        if choice == '1':
            items = cli_scan_cache()
            if items:
                cli_print_cache_status(items)
                cli_toggle_selection(items)
            else:
                print('未找到缓存\n')
        
        elif choice == '2':
            if not items:
                items = cli_scan_cache()
            
            for item in items:
                item['checked'] = item['safe']
            
            cli_clean_selected(items)
        
        elif choice == '3':
            if not items:
                print('请先扫描缓存\n')
            else:
                cli_clean_selected(items)
        
        elif choice == '4':
            cli_export_settings()
        
        elif choice == '5':
            cli_import_settings()
        
        elif choice == '0':
            print('再见！\n')
            break
        
        else:
            print('选择无效\n')

# ============================================================================
# Entry Point
# ============================================================================

def _find_python_with_pyqt5():
    """查找安装了 PyQt5 的 Python"""
    try:
        # Check conda environments
        conda_envs_dir = os.path.expanduser('~/anaconda3/envs')
        if os.path.exists(conda_envs_dir):
            for env in os.listdir(conda_envs_dir):
                env_python = os.path.join(conda_envs_dir, env, 'Scripts', 'python.exe')
                if os.path.exists(env_python):
                    result = subprocess.run([env_python, '-c', 'import PyQt5'], capture_output=True)
                    if result.returncode == 0:
                        return env_python
        
        # Check conda base
        base_python = os.path.expanduser('~/anaconda3/Scripts/python.exe')
        if os.path.exists(base_python):
            result = subprocess.run([base_python, '-c', 'import PyQt5'], capture_output=True)
            if result.returncode == 0:
                return base_python
    except:
        pass
    
    return None

def main():
    """主函数"""
    # Parse arguments
    force_cli = '--cli' in sys.argv or '-c' in sys.argv
    force_gui = '--gui' in sys.argv or '-g' in sys.argv
    
    if force_cli:
        run_cli()
    elif force_gui:
        if PYQT5_AVAILABLE:
            run_gui()
        else:
            print('❌ 错误：未找到 PyQt5，无法运行 GUI 模式')
            sys.exit(1)
    else:
        # Auto-detect mode
        if PYQT5_AVAILABLE:
            run_gui()
        else:
            # Try to find Python with PyQt5
            python_path = _find_python_with_pyqt5()
            if python_path:
                try:
                    subprocess.Popen([python_path, __file__])
                    sys.exit(0)
                except:
                    pass
            
            # Fallback to CLI
            run_cli()

if __name__ == '__main__':
    main()
