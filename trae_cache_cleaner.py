# -*- coding: utf-8 -*-
"""
TraeCacheCleaner - Python/PyQt5 Version (带命令行回退)
Trae IDE 缓存清理 + MCP 可视化管理 + 用户设置导出/导入
"""

import os
import sys
import json
import shutil
import time
import ctypes
from pathlib import Path
from datetime import datetime
from urllib.parse import unquote, urlparse

VERSION = "q_v0.1.3"

# 检查 PyQt5 是否可用
try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
        QListWidget, QListWidgetItem, QCheckBox, QLabel, QPushButton,
        QProgressBar, QMessageBox, QFileDialog, QGroupBox, QHeaderView,
        QTableWidget, QTableWidgetItem, QAbstractItemView, QLineEdit, QSpacerItem,
        QSizePolicy, QTreeWidget, QTreeWidgetItem
    )
    from PyQt5.QtCore import (
        Qt, QThread, pyqtSignal, QSize, QFileInfo, QDir
    )
    from PyQt5.QtGui import QFont, QIcon, QPalette, QColor
    HAS_PYQT5 = True
except ImportError:
    HAS_PYQT5 = False

# 获取当前工作目录（处理各种启动场景）
def get_current_directory():
    """获取当前脚本所在目录（支持多种启动方式）"""
    # 优先使用 __file__
    if '__file__' in globals():
        return os.path.dirname(os.path.abspath(__file__))
    # 回退到当前工作目录
    return os.getcwd()

# Git相关工具函数
def is_git_installed():
    """检查Git是否已安装"""
    try:
        import subprocess
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def get_git_version():
    """获取Git版本"""
    try:
        import subprocess
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return "未知"

def get_git_config(key):
    """获取Git配置项"""
    try:
        import subprocess
        result = subprocess.run(['git', 'config', '--get', key], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return None

# 路径配置
class PathConfig:
    @staticmethod
    def get_appdata():
        return os.path.expandvars('%APPDATA%')
    
    @staticmethod
    def get_userprofile():
        return os.path.expandvars('%USERPROFILE%')
    
    @staticmethod
    def get_trae_root():
        return os.path.join(PathConfig.get_appdata(), 'Trae CN')
    
    @staticmethod
    def get_trae_user():
        return os.path.join(PathConfig.get_trae_root(), 'User')
    
    @staticmethod
    def get_mcp_path():
        return os.path.join(PathConfig.get_trae_user(), 'mcp.json')
    
    @staticmethod
    def get_rules_path():
        return os.path.join(PathConfig.get_trae_user(), 'rules')
    
    @staticmethod
    def get_workspace_storage():
        return os.path.join(PathConfig.get_trae_user(), 'workspaceStorage')
    
    @staticmethod
    def get_chat_sessions():
        return os.path.join(PathConfig.get_trae_user(), 'History')
    
    @staticmethod
    def get_extensions():
        return os.path.join(PathConfig.get_userprofile(), '.trae', 'extensions')
    
    @staticmethod
    def get_app_dir():
        """获取应用程序所在目录"""
        return get_current_directory()

# 缓存项定义
CACHE_ENTRIES = [
    {"label": "缓存数据", "sub": "Trae CN\\CachedData", "hint": "编辑器功能缓存", "safe": True},
    {"label": "浏览器缓存", "sub": "Trae CN\\Cache", "hint": "Chromium内核缓存", "safe": True},
    {"label": "CacheStorage", "sub": "Trae CN\\CacheStorage", "hint": "Cache Storage API存储", "safe": True},
    {"label": "代码缓存", "sub": "Trae CN\\Code Cache", "hint": "V8编译缓存", "safe": True},
    {"label": "日志文件", "sub": "Trae CN\\logs", "hint": "运行时日志", "safe": True},
    {"label": "GPU缓存", "sub": "Trae CN\\GPUCache", "hint": "GPU着色器缓存", "safe": True},
    {"label": "崩溃报告", "sub": "Trae CN\\Crashpad", "hint": "崩溃转储文件", "safe": False},
    {"label": "二进制存储", "sub": "Trae CN\\blob_storage", "hint": "二进制数据存储", "safe": False},
    {"label": "Web存储", "sub": "Trae CN\\WebStorage", "hint": "Web视图存储", "safe": False},
    {"label": "文件系统", "sub": "Trae CN\\FileSystem", "hint": "文件系统API存储", "safe": False},
    {"label": "IndexedDB", "sub": "Trae CN\\IndexedDB", "hint": "IndexedDB数据库", "safe": False},
    {"label": "本地存储", "sub": "Trae CN\\Local Storage", "hint": "LocalStorage", "safe": False},
    {"label": "会话存储", "sub": "Trae CN\\Session Storage", "hint": "SessionStorage", "safe": False},
    {"label": "Service Worker", "sub": "Trae CN\\Service Worker", "hint": "Service Worker缓存", "safe": False},
    {"label": "共享字典", "sub": "Trae CN\\Shared Dictionary", "hint": "拼写检查字典", "safe": False},
    {"label": "Web分区", "sub": "Trae CN\\Partitions", "hint": "Web视图分区", "safe": False},
    {"label": "共享ProtoDB", "sub": "Trae CN\\shared_proto_db", "hint": "共享协议数据库", "safe": False},
    {"label": "网络缓存", "sub": "Trae CN\\Network", "hint": "网络配置缓存", "safe": False},
    {"label": "词典文件", "sub": "Trae CN\\Dictionaries", "hint": "词典文件", "safe": False},
    {"label": "视频解码统计", "sub": "Trae CN\\VideoDecodeStats", "hint": "视频解码统计数据", "safe": False},
    {"label": "扩展状态", "sub": "Trae CN\\Local Extension Settings", "hint": "扩展本地设置存储", "safe": False},
    {"label": "通知状态", "sub": "Trae CN\\Notification State", "hint": "通知状态数据", "safe": False},
]

# 设置项定义（用于导入/导出）
SETTINGS_ITEMS = [
    {"name": "用户设置", "path": "settings.json", "is_dir": False},
    {"name": "快捷键设置", "path": "keybindings.json", "is_dir": False},
    {"name": "MCP配置", "path": "mcp.json", "is_dir": False},
    {"name": "全局规则", "path": "rules", "is_dir": True},
    {"name": "全局存储", "path": "globalStorage", "is_dir": True},
    {"name": "工作区存储", "path": "workspaceStorage", "is_dir": True},
    {"name": "对话记录", "path": "History", "is_dir": True},
    {"name": "代码片段", "path": "snippets", "is_dir": True},
]

# 工具函数
def format_size(bytes_size):
    """格式化文件大小"""
    if bytes_size == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB"]
    size = float(bytes_size)
    unit_idx = 0
    while size >= 1024 and unit_idx < 3:
        size /= 1024
        unit_idx += 1
    return f"{size:.2f} {units[unit_idx]}"

def scan_dir_size(path):
    """扫描目录大小（支持文件和目录）"""
    if not os.path.exists(path):
        return 0
    if os.path.isfile(path):
        try:
            return os.path.getsize(path)
        except:
            return 0
    total = 0
    try:
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isfile(item_path):
                total += os.path.getsize(item_path)
            elif os.path.isdir(item_path):
                total += scan_dir_size(item_path)
    except PermissionError:
        pass
    return total

def is_dark_mode():
    """检测系统是否为深色模式"""
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return value == 0
    except Exception:
        return False

if HAS_PYQT5:
    # 扫描线程
    class ScanThread(QThread):
        scan_progress = pyqtSignal(int, str)
        scan_done = pyqtSignal(list)
        
        def __init__(self, scan_type, parent=None):
            super().__init__(parent)
            self.scan_type = scan_type
    
        def run(self):
            if self.scan_type == 'cache':
                self.scan_cache()
            elif self.scan_type == 'chat':
                self.scan_chat()
            elif self.scan_type == 'workspace':
                self.scan_workspace()
            elif self.scan_type == 'extension':
                self.scan_extension()
    
        def scan_cache(self):
            items = []
            appdata = PathConfig.get_appdata()
            for i, entry in enumerate(CACHE_ENTRIES):
                full_path = os.path.join(appdata, entry['sub'])
                size = scan_dir_size(full_path) if os.path.exists(full_path) else 0
                items.append({
                    'label': entry['label'],
                    'path': full_path,
                    'hint': entry['hint'],
                    'size': size,
                    'safe': entry['safe'],
                    'exists': os.path.exists(full_path)
                })
                self.scan_progress.emit(i + 1, entry['label'])
            self.scan_done.emit(items)
    
        def scan_chat(self):
            items = []
            seen_paths = set()
        
            up = PathConfig.get_userprofile()
            ap = PathConfig.get_appdata()
        
            # 扫描多个可能的对话记录位置
            # Trae CN 使用 History 目录存储对话记录（每个会话一个哈希目录）
            # 国际版 Trae 可能使用 chatSessions 或 History
            chat_paths = [
                PathConfig.get_chat_sessions(),  # %APPDATA%/Trae CN/User/History
                os.path.join(ap, 'Trae CN', 'User', 'chatSessions'),
                os.path.join(ap, 'Trae CN', 'User', 'History'),
                os.path.join(up, '.trae', 'History'),
                os.path.join(up, '.trae-cn', 'History'),
                os.path.join(up, '.trae', 'chatSessions'),
                os.path.join(up, '.trae-cn', 'chatSessions'),
                os.path.join(up, 'Trae CN', 'History'),
                os.path.join(up, 'Trae CN', 'chatSessions'),
            ]
        
            for chat_path in chat_paths:
                if chat_path in seen_paths:
                    continue
                seen_paths.add(chat_path)
                if os.path.exists(chat_path):
                    print(f"[DEBUG] 扫描对话记录: {chat_path} (存在: True)")
                    source_tag = os.path.basename(os.path.dirname(chat_path)) if 'User' in chat_path else os.path.basename(chat_path)
                    try:
                        for name in os.listdir(chat_path):
                            full_path = os.path.join(chat_path, name)
                            if os.path.isdir(full_path) and full_path not in seen_paths:
                                seen_paths.add(full_path)
                                size = scan_dir_size(full_path)
                                # 读取 entries.json 获取所属文件资源信息
                                resource_path = ""
                                last_edit_time = 0
                                entries_json = os.path.join(full_path, 'entries.json')
                                if os.path.exists(entries_json):
                                    try:
                                        with open(entries_json, 'r', encoding='utf-8-sig') as f:
                                            entries_data = json.load(f)
                                        resource_path = entries_data.get('resource', '')
                                        entries_list = entries_data.get('entries', [])
                                        if entries_list:
                                            last_edit_time = max(e.get('timestamp', 0) for e in entries_list)
                                    except:
                                        pass
                                # 构建显示名称：优先使用 resource 路径中的文件名
                                display_name = name
                                decoded_path = ''
                                if resource_path:
                                    parsed = urlparse(resource_path)
                                    if parsed.scheme == 'file':
                                        decoded_path = unquote(parsed.path)
                                        display_name = os.path.basename(decoded_path)
                                hint_parts = [f"来源: History"]
                                if resource_path:
                                    parsed = urlparse(resource_path)
                                    if parsed.scheme == 'file':
                                        parts = decoded_path.replace('\\', '/').split('/')
                                        if len(parts) >= 3:
                                            project_hint = '/'.join(parts[:-1])
                                            hint_parts.append(f"位置: {decoded_path}")
                                            hint_parts.append(f"项目: {project_hint}")
                                if last_edit_time:
                                    dt = datetime.fromtimestamp(last_edit_time / 1000)
                                    hint_parts.append(f"最后编辑: {dt.strftime('%Y-%m-%d %H:%M')}")
                                hint_parts.append(f"ID: {name}")
                                items.append({
                                    'label': display_name,
                                    'path': full_path,
                                    'hint': '\n'.join(hint_parts),
                                    'size': size,
                                    'safe': False,
                                    'exists': True,
                                    'last_edit_time': last_edit_time,
                                    'file_path': decoded_path
                                })
                    except:
                        pass
                else:
                    print(f"[DEBUG] 扫描对话记录: {chat_path} (不存在)")
            print(f"[DEBUG] 对话记录扫描完成，共 {len(items)} 项")
            self.scan_done.emit(items)
    
        def scan_workspace(self):
            items = []
            seen_paths = set()
        
            up = PathConfig.get_userprofile()
            ap = PathConfig.get_appdata()
        
            ws_paths = [
                PathConfig.get_workspace_storage(),  # %APPDATA%/Trae CN/User/workspaceStorage
                os.path.join(ap, 'Trae CN', 'User', 'workspaceStorage'),
                os.path.join(up, '.trae', 'workspaceStorage'),
                os.path.join(up, '.trae-cn', 'workspaceStorage'),
                os.path.join(up, '.trae-cn', 'worktrees'),
                os.path.join(up, '.trae', 'worktrees'),
            ]
        
            for ws_path in ws_paths:
                if ws_path in seen_paths or not os.path.exists(ws_path):
                    continue
                seen_paths.add(ws_path)
                source_tag = "workspaceStorage" if "workspaceStorage" in ws_path else "worktrees"
                try:
                    for name in os.listdir(ws_path):
                        full_path = os.path.join(ws_path, name)
                        if os.path.isdir(full_path) and full_path not in seen_paths:
                            seen_paths.add(full_path)
                            size = scan_dir_size(full_path)
                            # 尝试读取 workspace.json 获取项目路径
                            project_path = ""
                            ws_json = os.path.join(full_path, 'workspace.json')
                            if os.path.exists(ws_json):
                                try:
                                    with open(ws_json, 'r', encoding='utf-8-sig') as f:
                                        ws_data = json.load(f)
                                    folder = ws_data.get('folder', '')
                                    if folder:
                                        # URL解码 file:/// 格式的路径
                                        parsed = urlparse(folder)
                                        if parsed.scheme == 'file':
                                            project_path = unquote(parsed.path).lstrip('/')
                                except:
                                    pass
                            # 没有 workspace.json 则直接使用目录名（如 worktrees 中的项目名）
                            display_name = os.path.basename(project_path) if project_path else name
                            hint_parts = [f"来源: {source_tag}"]
                            if project_path:
                                hint_parts.append(f"项目: {project_path}")
                            hint_parts.append(f"ID: {name}")
                            items.append({
                                'label': display_name,
                                'path': full_path,
                                'hint': '\n'.join(hint_parts),
                                'size': size,
                                'safe': False,
                                'exists': True,
                                'project_path': project_path,
                                'source': source_tag
                            })
                except:
                    pass
            self.scan_done.emit(items)
    
        def scan_extension(self):
            items = []
            seen_paths = set()
        
            up = PathConfig.get_userprofile()
            ap = PathConfig.get_appdata()
        
            # 扫描多个可能的扩展安装位置
            ext_paths = [
                PathConfig.get_extensions(),  # ~/.trae/extensions
                os.path.join(up, '.trae-cn', 'extensions'),
                os.path.join(up, '.trae', 'extensions'),
                os.path.join(ap, 'Trae CN', 'User', 'extensions'),
                os.path.join(ap, 'Trae CN', 'extensions'),
                os.path.join(up, 'Trae CN', 'extensions'),
                os.path.join(os.path.expandvars('%LOCALAPPDATA%'), 'Trae CN', 'extensions'),
            ]
        
            print(f"[DEBUG] 扫描扩展路径...")
            for ext_path in ext_paths:
                if ext_path in seen_paths or not os.path.exists(ext_path):
                    if not os.path.exists(ext_path):
                        print(f"[DEBUG] 扩展路径不存在: {ext_path}")
                    continue
                seen_paths.add(ext_path)
                print(f"[DEBUG] 扫描扩展: {ext_path} (存在)")
                try:
                    for name in os.listdir(ext_path):
                        full_path = os.path.join(ext_path, name)
                        if os.path.isdir(full_path) and full_path not in seen_paths:
                            seen_paths.add(full_path)
                            size = scan_dir_size(full_path)
                            # 读取 package.json 获取信息
                            pkg_path = os.path.join(full_path, 'package.json')
                            display_name = name
                            version = ''
                            publisher = ''
                            description = ''
                            if os.path.exists(pkg_path):
                                try:
                                    with open(pkg_path, 'r', encoding='utf-8') as f:
                                        pkg = json.load(f)
                                        display_name = pkg.get('displayName', name)
                                        version = pkg.get('version', '')
                                        publisher = pkg.get('publisher', '')
                                        description = pkg.get('description', '')
                                except:
                                    pass
                            items.append({
                                'label': display_name,
                                'path': full_path,
                                'hint': description or f'{publisher} ({version})',
                                'size': size,
                                'safe': False,
                                'exists': True,
                                'name': name,
                                'version': version,
                                'publisher': publisher
                            })
                except:
                    pass
            print(f"[DEBUG] 扩展扫描完成，共 {len(items)} 项")
            self.scan_done.emit(items)

    # 清理线程
    class CleanThread(QThread):
        clean_progress = pyqtSignal(int, str)
        clean_done = pyqtSignal(int, int)
    
        def __init__(self, items, parent=None):
            super().__init__(parent)
            self.items = items
    
        def run(self):
            cleaned = 0
            freed = 0
            for i, item in enumerate(self.items):
                if item.get('checked', False) and item.get('exists', False):
                    self.clean_progress.emit(i, item['label'])
                    try:
                        if os.path.isfile(item['path']):
                            os.remove(item['path'])
                        else:
                            shutil.rmtree(item['path'])
                        cleaned += 1
                        freed += item.get('size', 0)
                    except Exception as e:
                        print(f"Error deleting {item['path']}: {e}")
            self.clean_done.emit(cleaned, freed)

    # 主窗口
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Trae缓存清理工具")
            self.setGeometry(100, 100, 900, 650)
        
            # 获取应用目录
            self.app_dir = PathConfig.get_app_dir()
            print(f"[DEBUG] 应用目录: {self.app_dir}")
        
            # 设置窗口图标
            icon_path = os.path.join(self.app_dir, 'TraeCacheCleaner.ico')
            print(f"[DEBUG] 图标路径: {icon_path} (存在: {os.path.exists(icon_path)})")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        
            # 检测主题
            self.is_dark = is_dark_mode()
            self.setup_theme()
        
            # 检查Git配置
            print("\n[Git配置检查]")
            if is_git_installed():
                print(f"  Git已安装: {get_git_version()}")
                git_user = get_git_config('user.name')
                git_email = get_git_config('user.email')
                if git_user:
                    print(f"  用户名称: {git_user}")
                else:
                    print("  用户名称: 未配置")
                if git_email:
                    print(f"  用户邮箱: {git_email}")
                else:
                    print("  用户邮箱: 未配置")
            else:
                print("  Git未安装")
        
            # 初始化数据
            self.cache_items = []
            self.chat_items = []
            self.workspace_items = []
            self.extension_items = []
            self.mcp_entries = []
            self.settings_items = []
        
            # 配置文件路径
            self.config_path = os.path.join(self.app_dir, 'app_config.json')
            print(f"[DEBUG] 配置文件路径: {self.config_path}")
        
            # 先加载配置（必须在UI创建之前）
            self.load_app_config()
        
            # 创建UI
            self.init_ui()
        
            # 控制台窗口控制
            self._apply_console_visibility(show_init=True)
        
            # 更新防呆模式复选框状态
            self.safe_mode_check.setChecked(self.safe_mode)
        
            # 开始扫描
            self.start_scans()
    
        def load_app_config(self):
            """加载应用配置"""
            self.safe_mode = True
            self.show_console = True
        
            if os.path.exists(self.config_path):
                try:
                    with open(self.config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        if 'safe_mode' in config:
                            self.safe_mode = config['safe_mode']
                        if 'show_console' in config:
                            self.show_console = config['show_console']
                except Exception as e:
                    print(f"Error loading config: {e}")
    
        def save_app_config(self):
            """保存应用配置"""
            try:
                config = {
                    'safe_mode': self.safe_mode,
                    'show_console': self.show_console
                }
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)
            except Exception as e:
                print(f"Error saving config: {e}")
    
        def _apply_console_visibility(self, show_init=False):
            """应用控制台可见性设置"""
            try:
                kernel32 = ctypes.windll.kernel32
                console = kernel32.GetConsoleWindow()
                if console:
                    if self.show_console:
                        kernel32.ShowWindow(console, 5)  # SW_SHOW
                        if show_init:
                            self._print_console_tips()
                    else:
                        kernel32.ShowWindow(console, 0)  # SW_HIDE
            except:
                pass
    
        def _print_console_tips(self):
            """打印控制台启动提示"""
            sep = "=" * 50
            print(f"\n{sep}")
            print(f"  TraeCacheCleaner v{VERSION}")
            print(f"{sep}")
            print(f"  GUI 模式已启动")
            print(f"  提示: 此控制台窗口可在「设置」中关闭")
            print(f"  CLI 模式: 添加 --cli 参数运行")
            print(f"{sep}\n")
    
        def toggle_console(self, state):
            """切换控制台显示状态"""
            self.show_console = (state == Qt.Checked)
            self.save_app_config()
            self._apply_console_visibility()
    
        def setup_theme(self):
            """设置主题样式"""
            palette = QPalette()
            if self.is_dark:
                palette.setColor(QPalette.Window, QColor(30, 30, 30))
                palette.setColor(QPalette.WindowText, QColor(224, 224, 224))
                palette.setColor(QPalette.Base, QColor(40, 40, 40))
                palette.setColor(QPalette.AlternateBase, QColor(45, 45, 45))
                palette.setColor(QPalette.Text, QColor(224, 224, 224))
                palette.setColor(QPalette.Button, QColor(50, 50, 50))
                palette.setColor(QPalette.ButtonText, QColor(224, 224, 224))
                palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
                palette.setColor(QPalette.HighlightedText, Qt.white)
                palette.setColor(QPalette.ToolTipBase, QColor(40, 40, 40))
                palette.setColor(QPalette.ToolTipText, QColor(224, 224, 224))
                palette.setColor(QPalette.Disabled, QPalette.Text, QColor(128, 128, 128))
                palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(128, 128, 128))
                self.setStyleSheet("""
                    QMainWindow { background: #1e1e1e; }
                    QWidget#central_widget { background: #1e1e1e; }
                    QTabWidget::pane { border: 1px solid #444; background: #1e1e1e; }
                    QTabBar::tab { background: #333; color: #e0e0e0; padding: 8px 16px; border: 1px solid #444; border-bottom: none; }
                    QTabBar::tab:selected { background: #1e1e1e; border-bottom: 1px solid #1e1e1e; }
                    QTabBar::tab:hover { background: #3a3a3a; }
                    QPushButton { background: #444; color: #e0e0e0; border: 1px solid #555; padding: 6px 12px; border-radius: 3px; }
                    QPushButton:hover { background: #555; }
                    QPushButton:pressed { background: #666; }
                    QPushButton:disabled { background: #333; color: #666; border: 1px solid #444; }
                    QGroupBox { border: 1px solid #444; border-radius: 4px; margin-top: 8px; padding-top: 12px; color: #e0e0e0; }
                    QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
                    QLabel { color: #e0e0e0; background: transparent; }
                    QCheckBox { color: #e0e0e0; background: transparent; spacing: 6px; }
                    QCheckBox::indicator { width: 16px; height: 16px; }
                    QListWidget { color: #e0e0e0; background: #282828; border: 1px solid #444; border-radius: 3px; }
                    QListWidget::item { background: #282828; color: #e0e0e0; }
                    QListWidget::item:hover { background: #333; }
                    QListWidget::item:selected { background: #3a3a3a; }
                    QTableWidget { color: #e0e0e0; background: #282828; alternate-background-color: #2d2d2d; border: 1px solid #444; gridline-color: #3a3a3a; }
                    QTableWidget::item { color: #e0e0e0; background: #282828; padding: 4px; }
                    QTableWidget::item:alternate { background: #2d2d2d; }
                    QTableWidget::item:selected { background: #3a3a3a; }
                    QHeaderView::section { background: #333; color: #e0e0e0; padding: 6px 4px; border: 1px solid #444; font-weight: bold; }
                    QHeaderView::section:hover { background: #3a3a3a; }
                    QLineEdit { color: #e0e0e0; background: #333; border: 1px solid #555; padding: 4px 8px; border-radius: 3px; }
                    QLineEdit:focus { border: 1px solid #0078d4; }
                    QTreeWidget { color: #e0e0e0; background: #282828; border: 1px solid #444; }
                    QTreeWidget::item { padding: 4px; }
                    QTreeWidget::item:hover { background: #333; }
                    QTextEdit { color: #e0e0e0; background: #282828; border: 1px solid #444; }
                    QComboBox { color: #e0e0e0; background: #333; border: 1px solid #555; padding: 4px 8px; border-radius: 3px; }
                    QComboBox:hover { background: #3a3a3a; }
                    QComboBox::drop-down { border: none; width: 24px; }
                    QComboBox::down-arrow { image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 6px solid #e0e0e0; margin-right: 6px; }
                    QComboBox QAbstractItemView { color: #e0e0e0; background: #333; border: 1px solid #555; selection-background-color: #0078d4; }
                    QSpinBox { color: #e0e0e0; background: #333; border: 1px solid #555; padding: 4px; border-radius: 3px; }
                    QSpinBox::up-button, QSpinBox::down-button { border: none; background: #444; width: 18px; }
                    QSpinBox::up-arrow { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-bottom: 5px solid #e0e0e0; }
                    QSpinBox::down-arrow { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid #e0e0e0; }
                    QScrollBar:vertical { background: #2a2a2a; width: 12px; border: none; }
                    QScrollBar::handle:vertical { background: #555; min-height: 30px; border-radius: 4px; margin: 2px; }
                    QScrollBar::handle:vertical:hover { background: #666; }
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
                    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
                    QScrollBar:horizontal { background: #2a2a2a; height: 12px; border: none; }
                    QScrollBar::handle:horizontal { background: #555; min-width: 30px; border-radius: 4px; margin: 2px; }
                    QScrollBar::handle:horizontal:hover { background: #666; }
                    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
                    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: none; }
                    QProgressBar { color: #e0e0e0; background: #333; border: 1px solid #555; border-radius: 3px; text-align: center; }
                    QProgressBar::chunk { background: #0078d4; border-radius: 2px; }
                    QMenu { color: #e0e0e0; background: #2d2d2d; border: 1px solid #444; }
                    QMenu::item { padding: 6px 24px; }
                    QMenu::item:selected { background: #0078d4; }
                    QMenu::separator { height: 1px; background: #444; margin: 4px 8px; }
                    QToolTip { color: #e0e0e0; background: #333; border: 1px solid #555; padding: 4px 8px; }
                    QStatusBar { color: #e0e0e0; background: #252525; }
                    QStatusBar::item { border: none; }
                """)
            else:
                self.setStyleSheet("""
                    QTabWidget::pane { border: 1px solid #ccc; }
                    QPushButton { padding: 6px 12px; }
                """)
            self.setPalette(palette)
    
        def init_ui(self):
            """初始化UI"""
            central_widget = QWidget()
            central_widget.setObjectName("central_widget")
            self.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)
        
            # 标签页
            self.tab_widget = QTabWidget()
        
            # 缓存清理标签
            self.cache_tab = QWidget()
            self.init_cache_tab()
            self.tab_widget.addTab(self.cache_tab, "缓存清理")
        
            # 对话记录标签
            self.chat_tab = QWidget()
            self.init_chat_tab()
            self.tab_widget.addTab(self.chat_tab, "对话记录")
        
            # 工作区标签
            self.workspace_tab = QWidget()
            self.init_workspace_tab()
            self.tab_widget.addTab(self.workspace_tab, "工作区")
        
            # 扩展标签
            self.extension_tab = QWidget()
            self.init_extension_tab()
            self.tab_widget.addTab(self.extension_tab, "扩展")
        
            # MCP管理标签
            self.mcp_tab = QWidget()
            self.init_mcp_tab()
            self.tab_widget.addTab(self.mcp_tab, "MCP")
        
            # 设置标签
            self.settings_tab = QWidget()
            self.init_settings_tab()
            self.tab_widget.addTab(self.settings_tab, "设置")
        
            layout.addWidget(self.tab_widget)
        
            # 状态栏
            self.status_bar = self.statusBar()
            self.status_bar.showMessage("就绪")
    
        def init_cache_tab(self):
            """初始化缓存清理标签"""
            layout = QVBoxLayout(self.cache_tab)
        
            # 顶部提示栏
            hint_bar = QHBoxLayout()
        
            # 防呆模式
            self.safe_mode_check = QCheckBox("防呆模式（推荐）")
            self.safe_mode_check.setChecked(True)
            self.safe_mode_check.stateChanged.connect(self.toggle_safe_mode)
            self.safe_mode_check.setToolTip("启用后，危险项将被自动禁用并排除")
            hint_bar.addWidget(self.safe_mode_check)
        
            hint_bar.addStretch()
        
            # 大小统计
            self.total_size_label = QLabel("总大小: 0 B")
            hint_bar.addWidget(self.total_size_label)
        
            self.selected_size_label = QLabel("已选择: 0 B")
            self.selected_size_label.setStyleSheet("font-weight: bold;")
            hint_bar.addWidget(self.selected_size_label)
        
            self.selected_count_label = QLabel("(0 项)")
            hint_bar.addWidget(self.selected_count_label)
        
            layout.addLayout(hint_bar)
        
            # 防呆模式说明
            safe_hint = QLabel("💡 防呆模式下，危险项将被自动禁用，防止误删重要数据")
            safe_hint.setStyleSheet("color: #666; font-size: 12px;")
            layout.addWidget(safe_hint)
        
            # 列表
            self.cache_list = QListWidget()
            self.cache_list.setSelectionMode(QAbstractItemView.NoSelection)
            layout.addWidget(self.cache_list)
        
            # 按钮栏
            btn_layout = QHBoxLayout()
            self.select_all_btn = QPushButton("全选")
            self.select_all_btn.clicked.connect(self.select_all_cache)
            self.select_all_btn.setToolTip("选中所有可清理项")
            btn_layout.addWidget(self.select_all_btn)
        
            self.select_safe_btn = QPushButton("仅选安全项")
            self.select_safe_btn.clicked.connect(self.select_only_safe)
            self.select_safe_btn.setToolTip("只选中安全的缓存项（日志、缓存等）")
            btn_layout.addWidget(self.select_safe_btn)
        
            self.clean_btn = QPushButton("开始清理")
            self.clean_btn.clicked.connect(self.clean_cache)
            self.clean_btn.setToolTip("删除选中的缓存项（不可恢复）")
            btn_layout.addWidget(self.clean_btn)
        
            btn_layout.addStretch()
            layout.addLayout(btn_layout)
    
        def init_chat_tab(self):
            """初始化对话记录标签"""
            layout = QVBoxLayout(self.chat_tab)
        
            # 提示信息
            hint_label = QLabel("<b>⚠️ 警告：删除对话记录后不可恢复，请谨慎操作！</b>")
            hint_label.setStyleSheet("color: #ff9800;")
            hint_label.setToolTip("AI对话记录包含您与AI的所有对话历史，删除后无法恢复")
            layout.addWidget(hint_label)
        
            self.chat_list = QListWidget()
            self.chat_list.setSelectionMode(QAbstractItemView.NoSelection)
            layout.addWidget(self.chat_list)
        
            # 排序栏
            sort_layout = QHBoxLayout()
            sort_label = QLabel("排序:")
            sort_label.setStyleSheet("font-size: 12px;")
            sort_layout.addWidget(sort_label)
        
            self.sort_time_btn = QPushButton("按时间")
            self.sort_time_btn.setCheckable(True)
            self.sort_time_btn.setChecked(True)
            self.sort_time_btn.clicked.connect(lambda: self.sort_chat('time'))
            self.sort_time_btn.setToolTip("按最后编辑时间排序（最新在前）")
            sort_layout.addWidget(self.sort_time_btn)
        
            self.sort_size_btn = QPushButton("按大小")
            self.sort_size_btn.setCheckable(True)
            self.sort_size_btn.clicked.connect(lambda: self.sort_chat('size'))
            self.sort_size_btn.setToolTip("按文件大小排序（最大在前）")
            sort_layout.addWidget(self.sort_size_btn)
        
            self.sort_name_btn = QPushButton("按名称")
            self.sort_name_btn.setCheckable(True)
            self.sort_name_btn.clicked.connect(lambda: self.sort_chat('name'))
            self.sort_name_btn.setToolTip("按文件名排序（A-Z）")
            sort_layout.addWidget(self.sort_name_btn)
        
            sort_layout.addStretch()
            layout.addLayout(sort_layout)
        
            btn_layout = QHBoxLayout()
            self.select_all_chat_btn = QPushButton("全选")
            self.select_all_chat_btn.clicked.connect(self.select_all_chat)
            self.select_all_chat_btn.setToolTip("选中所有对话记录")
            btn_layout.addWidget(self.select_all_chat_btn)
        
            self.clean_chat_btn = QPushButton("删除选中")
            self.clean_chat_btn.clicked.connect(self.clean_chat)
            self.clean_chat_btn.setToolTip("删除选中的对话记录（不可恢复）")
            btn_layout.addWidget(self.clean_chat_btn)
        
            self.chat_total_label = QLabel("总大小: 0 B")
            btn_layout.addWidget(self.chat_total_label)
        
            btn_layout.addStretch()
            layout.addLayout(btn_layout)
    
        def init_workspace_tab(self):
            """初始化工作区标签"""
            layout = QVBoxLayout(self.workspace_tab)
        
            # 提示信息
            hint_label = QLabel("<b>⚠️ 警告：删除工作区存储可能影响项目设置，请谨慎操作！</b>")
            hint_label.setStyleSheet("color: #ff9800;")
            hint_label.setToolTip("工作区存储包含项目特定的设置和状态信息")
            layout.addWidget(hint_label)
        
            self.workspace_list = QListWidget()
            self.workspace_list.setSelectionMode(QAbstractItemView.NoSelection)
            layout.addWidget(self.workspace_list)
        
            btn_layout = QHBoxLayout()
            self.select_all_ws_btn = QPushButton("全选")
            self.select_all_ws_btn.clicked.connect(self.select_all_workspace)
            self.select_all_ws_btn.setToolTip("选中所有工作区存储")
            btn_layout.addWidget(self.select_all_ws_btn)
        
            self.clean_ws_btn = QPushButton("删除选中")
            self.clean_ws_btn.clicked.connect(self.clean_workspace)
            self.clean_ws_btn.setToolTip("删除选中的工作区存储（可能影响项目设置）")
            btn_layout.addWidget(self.clean_ws_btn)
        
            self.ws_total_label = QLabel("总大小: 0 B")
            btn_layout.addWidget(self.ws_total_label)
        
            btn_layout.addStretch()
            layout.addLayout(btn_layout)
    
        def init_extension_tab(self):
            """初始化扩展标签"""
            layout = QVBoxLayout(self.extension_tab)
        
            # 提示信息
            hint_label = QLabel("扩展插件仅显示扫描信息，不提供直接删除功能")
            hint_label.setStyleSheet("color: #666; font-size: 12px;")
            layout.addWidget(hint_label)
        
            self.extension_table = QTableWidget()
            self.extension_table.setColumnCount(5)
            self.extension_table.setHorizontalHeaderLabels(["名称", "发布者", "版本", "大小", "安装路径"])
            self.extension_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            layout.addWidget(self.extension_table)
        
            self.ext_total_label = QLabel("总大小: 0 B")
            layout.addWidget(self.ext_total_label)
    
        def init_mcp_tab(self):
            """初始化MCP管理标签"""
            layout = QVBoxLayout(self.mcp_tab)
        
            # MCP列表
            self.mcp_table = QTableWidget()
            self.mcp_table.setColumnCount(4)
            self.mcp_table.setHorizontalHeaderLabels(["启用", "名称", "描述", "路径/命令"])
            self.mcp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            layout.addWidget(self.mcp_table)
        
            # 按钮栏
            btn_layout = QHBoxLayout()
            self.save_mcp_btn = QPushButton("保存配置")
            self.save_mcp_btn.clicked.connect(self.save_mcp_config)
            btn_layout.addWidget(self.save_mcp_btn)
        
            self.open_mcp_dir_btn = QPushButton("打开配置目录")
            self.open_mcp_dir_btn.clicked.connect(self.open_mcp_dir)
            btn_layout.addWidget(self.open_mcp_dir_btn)
        
            btn_layout.addStretch()
            layout.addLayout(btn_layout)
    
        def init_settings_tab(self):
            """初始化设置标签"""
            layout = QVBoxLayout(self.settings_tab)
        
            # 设置列表
            group1 = QGroupBox("配置导出/导入")
            g1_layout = QVBoxLayout(group1)
            self.settings_list = QListWidget()
            self.settings_list.setSelectionMode(QAbstractItemView.NoSelection)
            g1_layout.addWidget(self.settings_list)
        
            btn_layout = QHBoxLayout()
            self.export_btn = QPushButton("导出设置")
            self.export_btn.clicked.connect(self.export_settings)
            btn_layout.addWidget(self.export_btn)
        
            self.import_btn = QPushButton("导入设置")
            self.import_btn.clicked.connect(self.import_settings)
            btn_layout.addWidget(self.import_btn)
            btn_layout.addStretch()
            g1_layout.addLayout(btn_layout)
            layout.addWidget(group1)
        
            # 程序选项
            group2 = QGroupBox("程序选项")
            g2_layout = QVBoxLayout(group2)
        
            self.console_check = QCheckBox("启动时显示控制台窗口（默认开启）")
            self.console_check.setChecked(self.show_console)
            self.console_check.setToolTip("关闭后下次启动将隐藏控制台黑窗口")
            self.console_check.stateChanged.connect(self.toggle_console)
            g2_layout.addWidget(self.console_check)
        
            layout.addWidget(group2)
        
            # 关于
            group3 = QGroupBox("关于")
            g3_layout = QVBoxLayout(group3)
            about_text = QLabel(
                f"<b>TraeCacheCleaner</b> v{VERSION}<br><br>"
                "Trae IDE 缓存清理工具<br>"
                "支持 GUI / CLI 双模式<br><br>"
                "功能: 缓存清理 / 对话管理 / 工作区管理<br>"
                "扩展扫描 / MCP 配置 / 设置导出导入<br><br>"
                "<a href='https://github.com/FDAlfrid/TraeCacheCleaner'>GitHub</a>"
            )
            about_text.setOpenExternalLinks(True)
            about_text.setWordWrap(True)
            g3_layout.addWidget(about_text)
            layout.addWidget(group3)
        
            layout.addStretch()
    
        def start_scans(self):
            """启动后台扫描"""
            # 扫描缓存
            self.cache_scan_thread = ScanThread('cache')
            self.cache_scan_thread.scan_done.connect(self.on_cache_scan_done)
            self.cache_scan_thread.start()
        
            # 扫描对话
            self.chat_scan_thread = ScanThread('chat')
            self.chat_scan_thread.scan_done.connect(self.on_chat_scan_done)
            self.chat_scan_thread.start()
        
            # 扫描工作区
            self.ws_scan_thread = ScanThread('workspace')
            self.ws_scan_thread.scan_done.connect(self.on_workspace_scan_done)
            self.ws_scan_thread.start()
        
            # 扫描扩展
            self.ext_scan_thread = ScanThread('extension')
            self.ext_scan_thread.scan_done.connect(self.on_extension_scan_done)
            self.ext_scan_thread.start()
        
            # 加载MCP配置
            self.load_mcp_config()
        
            # 加载设置项
            self.load_settings_items()
    
        def on_cache_scan_done(self, items):
            """缓存扫描完成"""
            self.cache_items = items
            self.update_cache_list()
    
        def on_chat_scan_done(self, items):
            """对话扫描完成"""
            self.chat_items = items
            self.sort_chat('time')
    
        def on_workspace_scan_done(self, items):
            """工作区扫描完成"""
            self.workspace_items = items
            self.update_workspace_list()
    
        def on_extension_scan_done(self, items):
            """扩展扫描完成"""
            self.extension_items = items
            self.update_extension_table()
    
        def update_cache_list(self):
            """更新缓存列表"""
            self.cache_list.clear()
            total_size = 0
        
            for item in self.cache_items:
                list_item = QListWidgetItem()
                widget = QWidget()
                layout = QHBoxLayout(widget)
            
                checkbox = QCheckBox()
                # 防呆模式下，危险项不可选中
                if self.safe_mode and not item['safe']:
                    checkbox.setEnabled(False)
                    checkbox.setChecked(False)
                    item['checked'] = False
                else:
                    checkbox.setEnabled(True)  # 显式启用
                    checkbox.setChecked(item.get('checked', item['safe'] and item['exists']))
                    item['checked'] = checkbox.isChecked()
                checkbox.stateChanged.connect(lambda state, it=item: self.update_item_checked(it, state))
                layout.addWidget(checkbox)
            
                # 安全级别标识
                safety_icon = QLabel("✅" if item['safe'] else "⚠️")
                safety_icon.setToolTip("安全项" if item['safe'] else "危险项（可能包含用户数据）")
                layout.addWidget(safety_icon)
            
                label = QLabel(f"{item['label']} ({format_size(item['size'])})")
                # 悬浮提示包含详细信息
                tooltip = f"<b>名称:</b> {item['label']}\n" \
                        f"<b>描述:</b> {item['hint']}\n" \
                        f"<b>路径:</b> {item['path']}\n" \
                        f"<b>安全级别:</b> {'安全' if item['safe'] else '危险'}\n" \
                        f"<b>状态:</b> {'存在' if item['exists'] else '不存在'}"
                label.setToolTip(tooltip)
                layout.addWidget(label)
            
                layout.addStretch()
                list_item.setSizeHint(widget.sizeHint())
                self.cache_list.addItem(list_item)
                self.cache_list.setItemWidget(list_item, widget)
            
                total_size += item['size']
        
            # 计算选中项的大小和数量
            selected_items = [item for item in self.cache_items if item.get('checked', False) and item['exists']]
            selected_size = sum(item['size'] for item in selected_items)
            selected_count = len(selected_items)
        
            self.total_size_label.setText(f"总大小: {format_size(total_size)}")
            self.selected_size_label.setText(f"已选择: {format_size(selected_size)}")
            self.selected_count_label.setText(f"({selected_count} 项)")
    
        def sort_chat(self, sort_by):
            """排序对话记录"""
            # 更新按钮状态
            for btn in [self.sort_time_btn, self.sort_size_btn, self.sort_name_btn]:
                btn.setChecked(btn == self.sort_time_btn and sort_by == 'time'
                            or btn == self.sort_size_btn and sort_by == 'size'
                            or btn == self.sort_name_btn and sort_by == 'name')
        
            if sort_by == 'time':
                self.chat_items.sort(key=lambda x: x.get('last_edit_time', 0), reverse=True)
            elif sort_by == 'size':
                self.chat_items.sort(key=lambda x: x.get('size', 0), reverse=True)
            elif sort_by == 'name':
                self.chat_items.sort(key=lambda x: x.get('label', '').lower())
        
            self.update_chat_list()
    
        def update_chat_list(self):
            """更新对话列表"""
            total_size = 0
        
            self.chat_list.setVisible(False)
            self.chat_list.setUpdatesEnabled(False)
            self.chat_list.clear()
        
            for idx, item in enumerate(self.chat_items):
                list_item = QListWidgetItem()
                widget = QWidget()
                layout = QHBoxLayout(widget)
                layout.setContentsMargins(4, 4, 4, 4)
                layout.setSpacing(6)
            
                checkbox = QCheckBox()
                checkbox.setChecked(item.get('checked', False))
                checkbox.stateChanged.connect(lambda state, it=item: self.update_item_checked(it, state))
                layout.addWidget(checkbox)
            
                warning_icon = QLabel("🗑️")
                warning_icon.setToolTip("删除后不可恢复")
                layout.addWidget(warning_icon)
            
                file_name = item['label']
                label = QLabel(f"{file_name} ({format_size(item['size'])})")
                layout.addWidget(label)
            
                layout.addStretch()
            
                hint = item.get('hint', '')
                file_path = item.get('file_path', '')
                last_edit = item.get('last_edit_time', 0)
            
                tooltip_parts = [
                    "<b>📝 对话记录</b>（删除此项仅移除对话历史，不会删除源文件）",
                    f"<b>关联文件:</b> {file_name}"
                ]
                if file_path:
                    tooltip_parts.append(f"<b>文件路径:</b> {file_path}")
                if last_edit:
                    dt = datetime.fromtimestamp(last_edit / 1000)
                    tooltip_parts.append(f"<b>最后编辑:</b> {dt.strftime('%Y-%m-%d %H:%M')}")
                tooltip_parts.append(f"<b>大小:</b> {format_size(item['size'])}")
                if hint:
                    for line in hint.split('\n'):
                        if ':' in line:
                            k, v = line.split(':', 1)
                            k = k.strip()
                            if k not in ('文件', '大小'):
                                tooltip_parts.append(f"<b>{k}:</b> {v}")
                tooltip_parts.append("<hr>")
                tooltip_parts.append("<b style='color:red'>⚠️ 删除后不可恢复！</b>")
                label.setToolTip('<br>'.join(tooltip_parts))
                warning_icon.setToolTip('<br>'.join(tooltip_parts))
                checkbox.setToolTip('<br>'.join(tooltip_parts))
            
                list_item.setSizeHint(widget.sizeHint())
                self.chat_list.addItem(list_item)
                self.chat_list.setItemWidget(list_item, widget)
            
                total_size += item['size']
            
                if idx % 200 == 0:
                    QApplication.processEvents()
        
            self.chat_total_label.setText(f"总大小: {format_size(total_size)}")
            self.chat_list.setUpdatesEnabled(True)
            self.chat_list.setVisible(True)
    
        def update_workspace_list(self):
            """更新工作区列表"""
            self.workspace_list.clear()
            total_size = 0
        
            for item in self.workspace_items:
                list_item = QListWidgetItem()
                widget = QWidget()
                layout = QHBoxLayout(widget)
            
                checkbox = QCheckBox()
                checkbox.setChecked(False)
                item['checked'] = False
                checkbox.stateChanged.connect(lambda state, it=item: self.update_item_checked(it, state))
                layout.addWidget(checkbox)
            
                # 警告图标
                warning_icon = QLabel("⚠️")
                warning_icon.setToolTip("可能影响项目设置")
                layout.addWidget(warning_icon)
            
                label = QLabel(f"{item['label']} ({format_size(item['size'])})")
                hint = item.get('hint', '')
                tooltip_parts = [f"<b>项目:</b> {item['label']}",
                            f"<b>大小:</b> {format_size(item['size'])}"]
                if hint:
                    for line in hint.split('\n'):
                        if ':' in line:
                            k, v = line.split(':', 1)
                            tooltip_parts.append(f"<b>{k}:</b> {v}")
                tooltip_parts.append(f"<b>警告:</b> 删除可能影响项目设置！")
                label.setToolTip('<br>'.join(tooltip_parts))
                layout.addWidget(label)
            
                layout.addStretch()
                list_item.setSizeHint(widget.sizeHint())
                self.workspace_list.addItem(list_item)
                self.workspace_list.setItemWidget(list_item, widget)
            
                total_size += item['size']
        
            self.ws_total_label.setText(f"总大小: {format_size(total_size)}")
    
        def update_extension_table(self):
            """更新扩展表格"""
            self.extension_table.setRowCount(len(self.extension_items))
            total_size = 0
        
            for i, item in enumerate(self.extension_items):
                cell_items = []
                for col, text in [(0, item['label']), (1, item['publisher']), (2, item['version']), (3, format_size(item['size']))]:
                    ci = QTableWidgetItem(text)
                    if self.is_dark:
                        ci.setForeground(QColor(224, 224, 224))
                        ci.setBackground(QColor(40, 40, 40))
                    cell_items.append(ci)
                self.extension_table.setItem(i, 0, cell_items[0])
                self.extension_table.setItem(i, 1, cell_items[1])
                self.extension_table.setItem(i, 2, cell_items[2])
                self.extension_table.setItem(i, 3, cell_items[3])
                path_item = QTableWidgetItem(item.get('path', ''))
                if self.is_dark:
                    path_item.setForeground(QColor(224, 224, 224))
                    path_item.setBackground(QColor(40, 40, 40))
                path_item.setToolTip(item.get('path', ''))
                self.extension_table.setItem(i, 4, path_item)
                total_size += item['size']
        
            self.ext_total_label.setText(f"总大小: {format_size(total_size)}")
    
        def load_mcp_config(self):
            """加载MCP配置并自动识别预装MCP"""
            mcp_path = os.path.join(PathConfig.get_trae_user(), 'mcp', 'mcp.json')
            self.mcp_entries = []
        
            # 先加载配置文件
            if os.path.exists(mcp_path):
                try:
                    with open(mcp_path, 'r', encoding='utf-8-sig') as f:
                        data = json.load(f)
                        servers = data.get('mcpServers', {})
                        for name, config in servers.items():
                            self.mcp_entries.append({
                                'name': name,
                                'command': config.get('command', ''),
                                'args': config.get('args', ''),
                                'cwd': config.get('cwd', ''),
                                'url': config.get('url', ''),
                                'description': config.get('description', ''),
                                'enabled': config.get('enabled', True),
                                'is_url_type': bool(config.get('url'))
                            })
                except Exception as e:
                    print(f"Error loading MCP config: {e}")
        
            # 自动识别其他可能的MCP路径
            self.detect_mcp_locations()
        
            self.update_mcp_table()
    
        def detect_mcp_locations(self):
            """自动检测系统中可能存在的MCP服务"""
            known_mcp_names = set(entry['name'] for entry in self.mcp_entries)
            mcp_candidates = []
        
            # 1. 检查 PATH 环境变量中的MCP相关命令
            path_dirs = os.environ.get('PATH', '').split(os.pathsep)
            for dir_path in path_dirs:
                if os.path.isdir(dir_path):
                    try:
                        for filename in os.listdir(dir_path):
                            lower_name = filename.lower()
                            # 检测MCP相关程序：包含mcp、fallow、trae、coprocessor、git
                            if ('mcp' in lower_name or lower_name.startswith('fallow') or 
                                lower_name.startswith('trae') or lower_name.startswith('coprocessor') or
                                lower_name.startswith('git')):
                                name = os.path.splitext(filename)[0]
                                if name not in known_mcp_names:
                                    desc = f"自动检测: PATH中的服务 ({name})"
                                    if 'git' in lower_name:
                                        desc = f"自动检测: Git工具 ({name}) - 可用于版本控制"
                                    mcp_candidates.append({
                                        'name': name,
                                        'command': os.path.join(dir_path, filename),
                                        'description': desc,
                                        'enabled': False
                                    })
                    except:
                        pass
        
            # 2. 检查用户目录下的常见MCP位置
            user_dir = os.path.expanduser('~')
            common_mcp_dirs = [
                os.path.join(user_dir, '.mcp'),
                os.path.join(user_dir, 'mcp'),
                os.path.join(user_dir, 'bin', 'mcp'),
                os.path.join(user_dir, 'fallow'),
                os.path.join(user_dir, '.fallow'),
                os.path.join(user_dir, 'trae', 'mcp'),
            ]
            for mcp_dir in common_mcp_dirs:
                if os.path.isdir(mcp_dir):
                    try:
                        for filename in os.listdir(mcp_dir):
                            if filename.lower().endswith('.exe') or os.access(os.path.join(mcp_dir, filename), os.X_OK):
                                name = os.path.splitext(filename)[0]
                                if name not in known_mcp_names:
                                    mcp_candidates.append({
                                        'name': name,
                                        'command': os.path.join(mcp_dir, filename),
                                        'description': f"自动检测: 用户目录服务 ({name})",
                                        'enabled': False
                                    })
                    except:
                        pass
        
            # 3. 检查系统程序目录
            program_dirs = [
                os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'MCP'),
                os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'MCP'),
                os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'Fallow'),
                os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'Fallow'),
                os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'Trae'),
                os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'Trae'),
            ]
            for program_dir in program_dirs:
                if os.path.isdir(program_dir):
                    try:
                        for root, dirs, files in os.walk(program_dir):
                            for filename in files:
                                if filename.lower().endswith('.exe'):
                                    name = os.path.splitext(filename)[0]
                                    if name.lower() != 'uninstall' and name not in known_mcp_names:
                                        mcp_candidates.append({
                                            'name': name,
                                            'command': os.path.join(root, filename),
                                            'description': f"自动检测: 系统程序服务 ({name})",
                                            'enabled': False
                                        })
                    except:
                        pass
        
            # 4. 检查 Trae 的 MCP 目录
            trae_user = PathConfig.get_trae_user()
            mcp_dir = os.path.join(trae_user, 'mcp')
            if os.path.isdir(mcp_dir):
                try:
                    for filename in os.listdir(mcp_dir):
                        if filename.lower().endswith('.exe'):
                            name = os.path.splitext(filename)[0]
                            if name not in known_mcp_names:
                                mcp_candidates.append({
                                    'name': name,
                                    'command': os.path.join(mcp_dir, filename),
                                    'description': f"自动检测: Trae MCP目录 ({name})",
                                    'enabled': False
                                })
                except:
                    pass
        
            # 添加检测到的MCP（去重）
            for candidate in mcp_candidates:
                if candidate['name'] not in known_mcp_names:
                    self.mcp_entries.append({
                        'name': candidate['name'],
                        'command': candidate['command'],
                        'args': '',
                        'cwd': os.path.dirname(candidate['command']),
                        'url': '',
                        'description': candidate['description'],
                        'enabled': candidate['enabled'],
                        'is_url_type': False
                    })
                    known_mcp_names.add(candidate['name'])
    
        def update_mcp_table(self):
            """更新MCP表格"""
            self.mcp_table.setRowCount(len(self.mcp_entries))
        
            for i, entry in enumerate(self.mcp_entries):
                # 启用复选框（使用容器确保背景正确）
                checkbox = QCheckBox()
                checkbox.setChecked(entry['enabled'])
                checkbox.stateChanged.connect(lambda state, idx=i: self.update_mcp_enabled(idx, state))
                if self.is_dark:
                    checkbox.setStyleSheet("background: transparent;")
                self.mcp_table.setCellWidget(i, 0, checkbox)
            
                for col, text in [(1, entry['name']), (2, entry['description']), (3, entry['cwd'] or entry['command'] or entry['url'])]:
                    item = QTableWidgetItem(text)
                    if self.is_dark:
                        item.setForeground(QColor(224, 224, 224))
                        item.setBackground(QColor(40, 40, 40))
                    self.mcp_table.setItem(i, col, item)
    
        def load_settings_items(self):
            """加载设置项"""
            trae_user = PathConfig.get_trae_user()
            self.settings_items = []
        
            for item in SETTINGS_ITEMS:
                full_path = os.path.join(trae_user, item['path'])
                size = scan_dir_size(full_path) if os.path.exists(full_path) else 0
                self.settings_items.append({
                    'name': item['name'],
                    'path': item['path'],
                    'full_path': full_path,
                    'is_dir': item['is_dir'],
                    'size': size,
                    'exists': os.path.exists(full_path),
                    'checked': True
                })
        
            self.update_settings_list()
    
        def update_settings_list(self):
            """更新设置列表"""
            self.settings_list.clear()
        
            for item in self.settings_items:
                list_item = QListWidgetItem()
                widget = QWidget()
                layout = QHBoxLayout(widget)
            
                checkbox = QCheckBox()
                checkbox.setChecked(item['checked'])
                checkbox.stateChanged.connect(lambda state, it=item: self.update_item_checked(it, state))
                layout.addWidget(checkbox)
            
                label = QLabel(f"{item['name']} ({format_size(item['size'])})")
                layout.addWidget(label)
            
                layout.addStretch()
                list_item.setSizeHint(widget.sizeHint())
                self.settings_list.addItem(list_item)
                self.settings_list.setItemWidget(list_item, widget)
    
        def update_item_checked(self, item, state):
            """更新项目选中状态"""
            item['checked'] = (state == Qt.Checked)
            # 更新选中统计
            self.update_cache_list()
    
        def update_mcp_enabled(self, idx, state):
            """更新MCP启用状态"""
            if idx < len(self.mcp_entries):
                self.mcp_entries[idx]['enabled'] = (state == Qt.Checked)
    
        def select_all_cache(self):
            """全选/取消全选缓存"""
            all_checked = all(item.get('checked', False) for item in self.cache_items if item['exists'])
            new_state = not all_checked
        
            for item in self.cache_items:
                if item['exists']:
                    item['checked'] = new_state
        
            self.update_cache_list()
    
        def select_all_chat(self):
            """全选/取消全选对话"""
            all_checked = all(item.get('checked', False) for item in self.chat_items)
            new_state = not all_checked
        
            for item in self.chat_items:
                item['checked'] = new_state
        
            self.update_chat_list()
    
        def select_all_workspace(self):
            """全选/取消全选工作区"""
            all_checked = all(item.get('checked', False) for item in self.workspace_items)
            new_state = not all_checked
        
            for item in self.workspace_items:
                item['checked'] = new_state
        
            self.update_workspace_list()
    
        def toggle_safe_mode(self, state):
            """切换防呆模式"""
            new_safe_mode = (state == Qt.Checked)
        
            if not new_safe_mode and self.safe_mode:
                reply = self.msg_warning(
                    "⚠️ 关闭防呆模式",
                    "<font color='black'>关闭防呆模式后，危险项将变为可选状态。<br><br>"
                    "<b style='color:red'>⚠️ 危险项可能包含您的重要数据（如 IndexedDB、本地存储等），"
                    "<br>删除后将无法恢复！</b><br><br>"
                    "确定要关闭防呆模式吗？</font>",
                    QMessageBox.Ok | QMessageBox.Cancel,
                    QMessageBox.Cancel
                )
            
                if reply != QMessageBox.Ok:
                    self.safe_mode_check.setChecked(True)
                    return
        
            self.safe_mode = new_safe_mode
        
            # 保存配置到文件
            self.save_app_config()
        
            if self.safe_mode:
                for item in self.cache_items:
                    if not item['safe']:
                        item['checked'] = False
        
            self.update_cache_list()
    
        def _exec_dialog(self, method, title, message, *args):
            """统一执行对话框，临时移除深色样式避免文字与背景同色"""
            old_style = self.styleSheet()
            if self.is_dark:
                self.setStyleSheet("")
                if not message.startswith('<'):
                    message = f"<font color='black'>{message}</font>"
            result = method(self, title, message, *args)
            self.setStyleSheet(old_style)
            return result

        def msg_warning(self, title, message, buttons=QMessageBox.Ok, default=QMessageBox.Ok):
            return self._exec_dialog(QMessageBox.warning, title, message, buttons, default)

        def msg_info(self, title, message):
            return self._exec_dialog(QMessageBox.information, title, message)

        def msg_confirm(self, title, message):
            return self._exec_dialog(QMessageBox.question, title, message, QMessageBox.Ok | QMessageBox.Cancel)

        def get_directory(self, title):
            """打开目录选择对话框（修复深色模式文字问题）"""
            old_style = self.styleSheet()
            if self.is_dark:
                self.setStyleSheet("")
            result = QFileDialog.getExistingDirectory(self, title)
            self.setStyleSheet(old_style)
            return result

        def msg_custom(self, title, text, widget_callback=None):
            """创建自定义对话框（修复深色模式文字问题）"""
            old_style = self.styleSheet()
            if self.is_dark:
                self.setStyleSheet("")
            dialog = QMessageBox(self)
            dialog.setWindowTitle(title)
            dialog.setText(f"<font color='black'>{text}</font>")
            if widget_callback:
                widget_callback(dialog)
            dialog.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            result = dialog.exec_()
            self.setStyleSheet(old_style)
            return result, dialog
    
        def select_only_safe(self):
            """仅选择安全项"""
            for item in self.cache_items:
                if item['exists']:
                    item['checked'] = item['safe']
            self.update_cache_list()
    
        def clean_cache(self):
            """清理缓存"""
            selected = [item for item in self.cache_items if item.get('checked', False)]
            if not selected:
                self.msg_warning("提示", "请先勾选要清理的项目")
                return
        
            reply = self.msg_confirm(
                "确认清理",
                f"<font color='black'>确定清理选中的 <b>{len(selected)} 项</b>缓存？<br><br>"
                "<b style='color:red'>注意：清理后无法恢复！</b></font>"
            )
        
            if reply == QMessageBox.Ok:
                self.clean_thread = CleanThread(selected)
                self.clean_thread.clean_progress.connect(self.on_clean_progress)
                self.clean_thread.clean_done.connect(self.on_clean_done)
                self.clean_thread.start()
                self.clean_btn.setEnabled(False)
    
        def clean_chat(self):
            """清理对话"""
            selected = [item for item in self.chat_items if item.get('checked', False)]
            if not selected:
                self.msg_warning("提示", "请先勾选要删除的对话")
                return
        
            if self.safe_mode:
                reply = self.msg_confirm(
                    "防呆模式",
                    f"<font color='black'>当前处于防呆模式，删除对话记录可能导致数据丢失！<br><br>"
                    f"确定要继续删除选中的 <b>{len(selected)} 项</b>对话记录吗？<br><br>"
                    "<b style='color:red'>注意：删除后无法恢复！</b></font>"
                )
            else:
                reply = self.msg_confirm(
                    "确认删除",
                    f"<font color='black'>确定删除选中的 <b>{len(selected)} 项</b>对话记录？<br><br>"
                    "<b style='color:red'>注意：删除后无法恢复！</b></font>"
                )
        
            if reply == QMessageBox.Ok:
                self.clean_thread = CleanThread(selected)
                self.clean_thread.clean_progress.connect(self.on_clean_progress)
                self.clean_thread.clean_done.connect(self.on_chat_clean_done)
                self.clean_thread.start()
                self.clean_chat_btn.setEnabled(False)
    
        def clean_workspace(self):
            """清理工作区"""
            selected = [item for item in self.workspace_items if item.get('checked', False)]
            if not selected:
                self.msg_warning("提示", "请先勾选要删除的工作区")
                return
        
            if self.safe_mode:
                reply = self.msg_confirm(
                    "防呆模式",
                    f"<font color='black'>当前处于防呆模式，删除工作区存储可能影响项目设置！<br><br>"
                    f"确定要继续删除选中的 <b>{len(selected)} 项</b>工作区数据吗？<br><br>"
                    "<b style='color:red'>注意：删除后无法恢复！</b></font>"
                )
            else:
                reply = self.msg_confirm(
                    "确认删除",
                    f"<font color='black'>确定删除选中的 <b>{len(selected)} 项</b>工作区数据？<br><br>"
                    "<b style='color:red'>注意：删除后无法恢复！</b></font>"
                )
        
            if reply == QMessageBox.Ok:
                self.clean_thread = CleanThread(selected)
                self.clean_thread.clean_progress.connect(self.on_clean_progress)
                self.clean_thread.clean_done.connect(self.on_workspace_clean_done)
                self.clean_thread.start()
                self.clean_ws_btn.setEnabled(False)
    
        def on_clean_progress(self, idx, name):
            """清理进度"""
            self.status_bar.showMessage(f"正在清理: {name}")
    
        def on_clean_done(self, cleaned, freed):
            """缓存清理完成"""
            self.status_bar.showMessage(f"完成！清理了 {cleaned} 项，释放 {format_size(freed)}")
            self.clean_btn.setEnabled(True)
            self.start_scans()
    
        def on_chat_clean_done(self, cleaned, freed):
            """对话清理完成"""
            self.status_bar.showMessage(f"完成！删除了 {cleaned} 项，释放 {format_size(freed)}")
            self.clean_chat_btn.setEnabled(True)
            self.chat_scan_thread = ScanThread('chat')
            self.chat_scan_thread.scan_done.connect(self.on_chat_scan_done)
            self.chat_scan_thread.start()
    
        def on_workspace_clean_done(self, cleaned, freed):
            """工作区清理完成"""
            self.status_bar.showMessage(f"完成！删除了 {cleaned} 项，释放 {format_size(freed)}")
            self.clean_ws_btn.setEnabled(True)
            self.ws_scan_thread = ScanThread('workspace')
            self.ws_scan_thread.scan_done.connect(self.on_workspace_scan_done)
            self.ws_scan_thread.start()
    
        def save_mcp_config(self):
            """保存MCP配置"""
            mcp_path = PathConfig.get_mcp_path()
            data = {'mcpServers': {}}
        
            for entry in self.mcp_entries:
                server = {'enabled': entry['enabled']}
                if entry['is_url_type']:
                    server['url'] = entry['url']
                else:
                    server['command'] = entry['command']
                    if entry['args']:
                        server['args'] = entry['args']
                    if entry['cwd']:
                        server['cwd'] = entry['cwd']
                if entry['description']:
                    server['description'] = entry['description']
                data['mcpServers'][entry['name']] = server
        
            try:
                with open(mcp_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                self.msg_info("保存成功", "MCP配置已保存")
            except Exception as e:
                self.msg_warning("保存失败", f"保存失败: {str(e)}")
    
        def open_mcp_dir(self):
            """打开MCP配置目录"""
            os.startfile(os.path.dirname(PathConfig.get_mcp_path()))
    
        def export_settings(self):
            """导出设置"""
            selected = [item for item in self.settings_items if item.get('checked', False) and item['exists']]
            if not selected:
                self.msg_warning("提示", "请先勾选要导出的项目")
                return
        
            export_dir = self.get_directory("选择导出目录")
            if not export_dir:
                return
        
            # 创建带时间戳的目录
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target_dir = os.path.join(export_dir, f"TraeSettings_{timestamp}")
            os.makedirs(target_dir, exist_ok=True)
        
            # 导出选中项
            exported = []
            for item in selected:
                src = item['full_path']
                dst = os.path.join(target_dir, item['path'])
                try:
                    if item['is_dir']:
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
                    exported.append(item['name'])
                except Exception as e:
                    print(f"Error exporting {item['name']}: {e}")
        
            # 生成元数据文件
            meta = {
                'export_time': datetime.now().isoformat(),
                'items': exported
            }
            with open(os.path.join(target_dir, '_export_meta.txt'), 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
        
            self.msg_info("导出成功", f"成功导出 {len(exported)} 项设置\n\n位置: {target_dir}")
    
        def import_settings(self):
            """导入设置"""
            import_dir = self.get_directory("选择导入目录")
            if not import_dir:
                return
        
            # 检查元数据文件
            meta_path = os.path.join(import_dir, '_export_meta.txt')
            if not os.path.exists(meta_path):
                self.msg_warning("错误", "未找到有效的导出目录")
                return
        
            # 加载元数据
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
            except:
                self.msg_warning("错误", "无法读取元数据文件")
                return
        
            # 显示可导入项
            trae_user = PathConfig.get_trae_user()
            available_items = []
            for item_name in meta.get('items', []):
                for template in SETTINGS_ITEMS:
                    if template['name'] == item_name:
                        full_path = os.path.join(trae_user, template['path'])
                        src_path = os.path.join(import_dir, template['path'])
                        if os.path.exists(src_path):
                            available_items.append({
                                'name': item_name,
                                'path': template['path'],
                                'full_path': full_path,
                                'src_path': src_path,
                                'is_dir': template['is_dir'],
                                'checked': True
                            })
                        break
        
            if not available_items:
                self.msg_warning("提示", "没有可导入的项目")
                return
        
            # 创建确认对话框（带项目列表）
            checkboxes = []
            def setup_import_dialog(dialog):
                dialog.setDetailedText("")
                widget = QWidget()
                layout = QVBoxLayout(widget)
                for item in available_items:
                    cb = QCheckBox(item['name'])
                    cb.setChecked(True)
                    checkboxes.append((cb, item))
                    layout.addWidget(cb)
                dialog.layout().addWidget(widget, dialog.layout().rowCount(), 0, 1, dialog.layout().columnCount())
        
            result, _ = self.msg_custom("确认导入", "以下项目将被覆盖，确定继续？", setup_import_dialog)
        
            if result == QMessageBox.Ok:
                imported = 0
                for cb, item in checkboxes:
                    if cb.isChecked():
                        try:
                            dst = item['full_path']
                            src = item['src_path']
                            
                            if os.path.exists(dst):
                                if item['is_dir']:
                                    shutil.rmtree(dst)
                                else:
                                    os.remove(dst)
                            
                            if item['is_dir']:
                                shutil.copytree(src, dst)
                            else:
                                shutil.copy2(src, dst)
                            imported += 1
                        except Exception as e:
                            print(f"Error importing {item['name']}: {e}")
            
            self.msg_info("导入成功", f"成功导入 {imported} 项设置\n\n请重启 Trae IDE 生效")


# ==================== CLI 模式 ====================

def cli_print_banner():
    print("=" * 60)
    print("  TraeCacheCleaner - 命令行版本")
    print("=" * 60)
    print()

def cli_print_menu():
    print("请选择要执行的操作:")
    print("  [1] 扫描并显示缓存状态")
    print("  [2] 清理安全项（推荐）")
    print("  [3] 清理所有选中项")
    print("  [4] 导出设置")
    print("  [5] 导入设置")
    print("  [0] 退出")
    print()

def cli_scan_cache():
    appdata = os.path.expandvars('%APPDATA%')
    items = []
    for entry in CACHE_ENTRIES:
        full_path = os.path.join(appdata, entry['sub'])
        size = scan_dir_size(full_path) if os.path.exists(full_path) else 0
        items.append({
            **entry,
            'path': full_path,
            'size': size,
            'exists': os.path.exists(full_path),
            'selected': entry['safe']
        })
    return items

def cli_print_cache_status(items):
    print("\n缓存状态:")
    print("-" * 80)
    print(f"{'#':<3} {'状态':<5} {'安全':<5} {'大小':<12} {'名称':<20} {'路径':<30}")
    print("-" * 80)
    total_size = 0
    for idx, item in enumerate(items, 1):
        status = "[x]" if item['exists'] else "[ ]"
        safe = "[S]" if item['safe'] else "[D]"
        size_str = format_size(item['size'])
        if item['selected']:
            size_str = f"*{size_str}"
        else:
            size_str = f" {size_str}"
        print(f"{idx:<3} {status:<5} {safe:<5} {size_str:<12} {item['label']:<20} {item['path']}")
        total_size += item['size']
    print("-" * 80)
    print(f"\n总大小: {format_size(total_size)}")
    print("* = 已选中")
    print("[S] = 安全项, [D] = 危险项\n")

def cli_toggle_selection(items):
    print("\n选择要清理的项目:")
    print("格式: 1,3,5 或 2-6 或 all 或 none 或 safe")
    user_input = input("请输入: ").strip()
    
    if user_input.lower() == 'all':
        for item in items:
            item['selected'] = True
    elif user_input.lower() == 'none':
        for item in items:
            item['selected'] = False
    elif user_input.lower() == 'safe':
        for item in items:
            item['selected'] = item['safe']
    else:
        for item in items:
            item['selected'] = False
        selections = user_input.replace(' ', '').split(',')
        for sel in selections:
            if '-' in sel:
                start, end = map(int, sel.split('-'))
                for i in range(start, end+1):
                    if 1 <= i <= len(items):
                        items[i-1]['selected'] = True
            else:
                try:
                    idx = int(sel)
                    if 1 <= idx <= len(items):
                        items[idx-1]['selected'] = True
                except ValueError:
                    pass

def cli_delete_path(path):
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        return True
    except Exception as e:
        print(f"删除失败: {path} - {e}")
        return False

def cli_clean_selected(items):
    selected = [x for x in items if x['selected'] and x['exists']]
    if not selected:
        print("没有选择要清理的项目！")
        return
    
    print(f"\n即将清理 {len(selected)} 项:")
    for item in selected:
        print(f"  - {item['label']} ({format_size(item['size'])})")
    
    confirm = input("\n确认删除？(y/N): ").strip().lower()
    if confirm != 'y':
        print("取消操作。")
        return
    
    deleted = 0
    freed = 0
    print("\n清理中...")
    for item in selected:
        print(f" 删除: {item['label']}...")
        if cli_delete_path(item['path']):
            deleted += 1
            freed += item['size']
    
    print(f"\n清理完成！已清理 {deleted} 项，释放 {format_size(freed)}")

def cli_export_settings():
    print("\n设置导出")
    print("-" * 60)
    
    trae_user = os.path.join(os.path.expandvars('%APPDATA%'), 'Trae CN', 'User')
    export_dir = input("请输入导出目录 (默认: .): ").strip() or '.'
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_dir = os.path.join(export_dir, f"TraeSettings_{timestamp}")
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    exported = []
    print("\n选择要导出的项目 (默认全选):")
    for idx, item in enumerate(SETTINGS_ITEMS, 1):
        src_path = os.path.join(trae_user, item['path'])
        if os.path.exists(src_path):
            choice = input(f" [{idx}] {item['name']}? (Y/n): ").strip().lower()
            if choice != 'n':
                dst_path = os.path.join(target_dir, item['path'])
                if item['is_dir']:
                    shutil.copytree(src_path, dst_path)
                else:
                    shutil.copy2(src_path, dst_path)
                exported.append(item['name'])
    
    if exported:
        meta = {'export_time': datetime.now().isoformat(), 'items': exported}
        with open(os.path.join(target_dir, '_export_meta.txt'), 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        print(f"\n成功导出到: {target_dir}")
    else:
        print("\n没有导出任何项目。")
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)

def cli_import_settings():
    print("\n设置导入")
    print("-" * 60)
    
    source_dir = input("请输入导出目录路径: ").strip()
    meta_path = os.path.join(source_dir, '_export_meta.txt')
    
    if not os.path.exists(meta_path):
        print("未找到有效的导出目录！")
        return
    
    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
    except:
        print("无法读取元数据！")
        return
    
    trae_user = os.path.join(os.path.expandvars('%APPDATA%'), 'Trae CN', 'User')
    print(f"\n导出时间: {meta['export_time']}")
    print(f"包含项目: {', '.join(meta['items'])}")
    
    confirm = input("\n确认导入？这将覆盖现有配置！(y/N): ").strip().lower()
    if confirm != 'y':
        print("取消操作。")
        return
    
    imported = 0
    for item_name in meta['items']:
        for item in SETTINGS_ITEMS:
            if item['name'] == item_name:
                src_path = os.path.join(source_dir, item['path'])
                dst_path = os.path.join(trae_user, item['path'])
                if os.path.exists(src_path):
                    if os.path.exists(dst_path):
                        if item['is_dir']:
                            shutil.rmtree(dst_path)
                        else:
                            os.remove(dst_path)
                    if item['is_dir']:
                        shutil.copytree(src_path, dst_path)
                    else:
                        shutil.copy2(src_path, dst_path)
                    print(f"  已导入: {item['name']}")
                    imported += 1
                break
    
    print(f"\n成功导入 {imported} 项！请重启 Trae IDE 以生效。")

def run_cli():
    """运行命令行版本"""
    cli_print_banner()
    
    while True:
        cli_print_menu()
        choice = input("请选择 [0-5]: ").strip()
        
        if choice == '0':
            print("再见！")
            break
        
        elif choice == '1':
            items = cli_scan_cache()
            cli_print_cache_status(items)
        
        elif choice == '2':
            items = cli_scan_cache()
            for item in items:
                item['selected'] = item['safe']
            cli_print_cache_status(items)
            cli_clean_selected(items)
        
        elif choice == '3':
            items = cli_scan_cache()
            cli_print_cache_status(items)
            cli_toggle_selection(items)
            cli_print_cache_status(items)
            cli_clean_selected(items)
        
        elif choice == '4':
            cli_export_settings()
        
        elif choice == '5':
            cli_import_settings()
        
        else:
            print("无效选择！")
        
        print()

def run_gui():
    """运行GUI版本"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

def _find_python_with_pyqt5():
    """尝试查找安装了 PyQt5 的 Python 解释器"""
    import subprocess
    candidates = []
    
    # 从当前 Python 往上找 conda base 环境的 python.exe
    # 例如 E:\...\envs\bilibili\python.exe → E:\...\python.exe (base)
    parts = sys.executable.replace('\\', '/').rsplit('/', 2)
    if len(parts) >= 3 and parts[-2].lower() == 'envs':
        base_candidate = '/'.join(parts[:-2]) + '/python.exe'
        if os.path.exists(base_candidate):
            candidates.append(base_candidate)
    
    # 已知的 conda 安装路径
    known_paths = [
        os.path.expandvars('%USERPROFILE%\\miniconda3\\python.exe'),
        os.path.expandvars('%USERPROFILE%\\anaconda3\\python.exe'),
        'E:\\ProgramData\\miniconda3\\python.exe',
        'C:\\ProgramData\\miniconda3\\python.exe',
        'C:\\tools\\miniconda3\\python.exe',
    ]
    for p in known_paths:
        if p not in candidates and os.path.exists(p):
            candidates.append(p)
    
    for py in candidates:
        try:
            result = subprocess.run(
                [py, '-c', 'import PyQt5'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return py
        except:
            continue
    return None

if __name__ == '__main__':
    use_cli = '--cli' in sys.argv or '-c' in sys.argv
    use_gui = '--gui' in sys.argv or '-g' in sys.argv
    
    if use_cli:
        run_cli()
    elif HAS_PYQT5:
        run_gui()
    elif use_gui:
        print("错误：当前 Python 环境没有 PyQt5，无法启动 GUI 模式")
        print("请安装 PyQt5: pip install PyQt5")
        sys.exit(1)
    else:
        # 当前 Python 无 PyQt5，尝试找一个有 PyQt5 的解释器启动 GUI
        pyqt5_python = _find_python_with_pyqt5()
        if pyqt5_python:
            import subprocess
            print(f"当前环境无 PyQt5，正在尝试使用: {pyqt5_python}")
            print()
            try:
                subprocess.run([pyqt5_python, __file__, '--gui'])
                sys.exit(0)
            except Exception:
                pass
        
        print("未检测到 PyQt5，自动切换到命令行模式...")
        print("安装 PyQt5 可使用图形界面: pip install PyQt5")
        print()
        run_cli()
