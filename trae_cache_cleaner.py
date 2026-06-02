# TraeCacheCleaner

Trae IDE 缓存清理工具，支持 **图形界面（GUI）** 和 **命令行（CLI）** 两种模式，单文件架构！

## 功能特性

——以下部分内容为开发环境演示，具体请以实际为准。

### GUI 模式
| 标签页 | 功能 |
|--------|------|
| 缓存清理 | 22 项缓存可勾选清理，安全项默认选中 |
| 对话记录 | 显示所有对话历史记录，可按时间/大小/名称排序，逐项删除 |
| 工作区 | 显示工作区存储和 Worktrees，可勾选删除 |
| 扩展 | 显示已安装扩展信息（名称、版本、发布者、大小、安装路径） |
| MCP | 可视化管理 MCP 服务器配置，自动检测系统预装 MCP |
| 设置 | 导出/导入用户配置文件 |

### CLI 模式
- 扫描并显示缓存状态
- 清理安全项
- 清理所有选中项
- 导出设置
- 导入设置

## 运行方式

程序以 **GUI 为默认模式**，无论哪种启动方式都会优先打开图形界面。
只有当当前环境和系统中都找不到 PyQt5 时，才会降级为命令行模式。

### 方式一：双击 EXE（推荐）

`TraeCacheCleaner.exe` — 已内置 PyQt5，**任何 Windows 电脑即开即用 GUI**。

### 方式二：双击 run.bat

```bash
run.bat
```
自动调用当前环境的 Python，按策略优先启动 GUI。

### 方式三：直接运行 Python 脚本

```bash
python trae_cache_cleaner.py
```
程序会自动检测当前 Python 环境：
- 有 PyQt5 → 直接启动 GUI
- 无 PyQt5 → 自动搜索系统中安装了 PyQt5 的 Python（如 conda base 环境），找到后自动以 GUI 模式启动
- 全系统都找不到 PyQt5 → 降级为 CLI 模式

### 强制指定模式

```bash
python trae_cache_cleaner.py --cli     # 强制命令行
python trae_cache_cleaner.py --gui     # 强制 GUI（无 PyQt5 时报错退出）
```

## 环境要求

- **Python 3.8+** （单.py文件运行必选）
- **PyQt5 5.15+** （可选，用于 GUI 模式）

## 启动策略

程序以 **GUI 优先** 为原则自动选择模式：

```
当前 Python 有 PyQt5？
  ├─ 是 → 启动 GUI
  └─ 否 → 系统中有其他 Python 装了 PyQt5？
            ├─ 是 → 自动调用该 Python 启动 GUI
            └─ 否 → 降级为 CLI 模式
```

CLI 模式仅在系统全局都找不到 PyQt5 时才会触发，日常使用无需关心依赖问题。

## 安装依赖

### 使用 pip（推荐）

```bash
pip install PyQt5
```

### 使用 conda

```bash
conda install pyqt5
```

### 使用 requirements.txt（如果有）

```bash
pip install -r requirements.txt
```

## 跨版本路径适配

自动适配 **Trae 国际版** 和 **Trae CN 国内版** 的路径差异：

### 缓存数据扫描
| 版本 | 路径 |
|------|------|
| 国内版 (Trae CN) | `%APPDATA%\Trae CN\...` |
| 国际版 (Trae) | `%APPDATA%\Trae\...` |

### 扩展插件扫描
| 版本 | 路径 |
|------|------|
| 国内版 (Trae CN) | `%USERPROFILE%\.trae-cn\extensions` |
| 国际版 (Trae) | `%USERPROFILE%\.trae\extensions` |
| 系统级 | `%APPDATA%\Trae CN\extensions`、`%LOCALAPPDATA%\Trae CN\extensions` |

### 对话记录扫描
| 版本 | 路径 |
|------|------|
| 国内版 (Trae CN) | `%APPDATA%\Trae CN\User\History`（哈希目录） |
| 国际版 (Trae) | `%APPDATA%\Trae\User\History` 或 `.trae\History` |

### 工作区扫描
| 版本 | 路径 |
|------|------|
| 传统工作区 | `%APPDATA%\Trae CN\User\workspaceStorage` |
| Worktrees 工作区 | `%USERPROFILE%\.trae-cn\worktrees`、`.trae\worktrees` |

程序会自动扫描所有可能的路径，去重后合并显示，无需手动配置。

## 项目结构

```
TraeCacheCleaner-PyQt/
├── trae_cache_cleaner.py      # 主程序（GUI + CLI 双模式）
├── TraeCacheCleaner.ico       # 程序图标
├── run.bat                    # Windows 启动脚本
├── requirements.txt           # 依赖声明
└── README.md                  # 说明文档
```

## 防呆设计

### 1. 防呆模式（默认启用）

**防呆模式**是本工具的核心安全机制，**默认开启**，旨在防止误删重要数据。

#### 工作原理
- 每个缓存项都有**安全级别**标记：
  - **安全项**（✅ 图标）：日志、缓存等通用数据，可放心清理
  - **危险项**（⚠️ 图标）：IndexedDB、本地存储等，可能包含用户数据
- 防呆模式开启时，**危险项复选框自动禁用**，用户无法勾选
- 防呆模式关闭时，危险项变为可选，但会弹出**二次确认对话框**

#### 使用建议
```
日常清理 → 保持防呆模式开启 → 只清理安全项
深度清理 → 关闭防呆模式 → 按需勾选危险项
```
> ⚠️ 关闭防呆模式前请确认：您真的不需要那些数据了吗？

#### 关闭防呆模式的操作流程
1. 点击顶部「防呆模式（推荐）」复选框取消勾选
2. 弹出警告对话框，说明关闭后的风险
3. 点击「确定」确认关闭 → 危险项变为可选
4. 点击「取消」放弃操作 → 保持防呆模式
   > 对话框中「取消」为默认选项，防止误操作

### 2. 安全级别标识

| 图标 | 含义 | 说明 |
|------|------|------|
| ✅ | 安全项 | 可以放心清理，不会影响用户数据 |
| ⚠️ | 危险项 | 可能包含用户数据，清理需谨慎。防呆模式下自动禁用 |
| 🗑️ | 删除项 | 对话记录/工作区，删除后不可恢复 |

### 3. 悬浮提示（Tooltip）

将鼠标悬停在任何可操作的项目上，会弹出详细的悬浮提示信息：

#### 缓存清理项
```
名称: 浏览器缓存
描述: Chromium内核缓存
路径: %APPDATA%\Trae CN\Cache
大小: 123.45 MB
安全级别: ✅ 安全项
```

#### 对话记录
```
📝 对话记录（删除此项仅移除对话历史，不会删除源文件）
关联文件: BillMapper.java
文件路径: D:/Alfrid/Desktop/project/.../BillMapper.java
最后编辑: 2026-04-23 15:30
────────────────────────────────
⚠️ 删除后不可恢复！
```

#### 工作区
```
项目: 播放器
来源: workspaceStorage
项目路径: D:/Alfrid/Desktop/播放器
────────────────────────────────
⚠️ 删除可能影响项目设置！
```

#### 扩展插件
```
名称: Python
发布者: ms-python
版本: 2025.12.0
大小: 45.2 MB
安装路径: %USERPROFILE%\.trae-cn\extensions\...
```

> 提示：悬浮提示中的「关联文件」表示这段对话记录与哪个文件相关，删除对话记录**不会删除该文件本身**。

### 4. 二次确认

所有**执行清理/删除操作前**都会弹出确认对话框，显示：
- 将要删除的项目数量（如「确定删除选中的 5 项缓存？」）
- 明确的警告信息（红色标注不可恢复）
- 「取消」按钮为默认选项（按 Enter 不会误执行）

![确认对话框示意]
```
┌──────────────────────────────┐
│  ⚠️ 确认删除                 │
│                              │
│  确定删除选中的 5 项缓存？    │
│                              │
│  ⚠️ 注意：清理后无法恢复！    │
│                              │
│       [取消]  [确定]         │
│        ↑默认                  │
└──────────────────────────────┘
```

### 5. 已选项目实时统计

界面顶部实时显示当前勾选情况：
- **已选择: 256.78 MB (12 项)** — 加粗显示，方便评估清理量
- 勾选/取消任意项目时自动更新
- 帮助您判断是否需要清理这么多数据

## 功能说明

### 缓存清理
- 自动扫描 Trae IDE 的缓存目录
- 安全项（如日志、缓存）默认勾选
- 危险项（如 IndexedDB、本地存储）需手动勾选（防呆模式关闭时）

### MCP 管理
- 可视化显示所有 MCP 服务器配置
- 可启用/禁用服务器
- 修改配置后点击「保存配置」生效

### 设置导出/导入
- 支持导出：settings.json、mcp.json、keybindings.json、globalStorage、workspaceStorage、snippets、rules
- 导出目录包含时间戳和元数据文件
- 导入时可选择性恢复项目

## 主题适配

程序启动时自动检测系统主题：
- **浅色主题**：浅色背景 + 深色文字
- **深色主题**：深色背景 + 浅色文字

## 跨平台支持

- Windows（推荐）：完全支持
- macOS/Linux：未测试，可能需要修改路径检测

## 注意事项

### 清理前
1. ✅ **建议先关闭 Trae IDE**，部分缓存文件可能被占用导致无法删除
2. 🖱️ **善用悬浮提示**：将所有项目都悬停看一遍，确认每项内容再清理
3. 🛡️ **保持防呆模式开启**：日常清理不需要关闭防呆模式
4. 📊 **参考已选统计**：观察顶部「已选择」大小，评估清理收益

### 清理中
5. ⚠️ **清理操作不可逆**，删除后无法恢复
6. 🗑️ **对话记录**仅删除对话历史，不会影响源文件
7. 🏗️ **工作区**删除可能影响项目设置（如打开的文件记录）

### 清理后
8. 🔄 MCP 配置修改后需要**重启 Trae IDE** 生效
9. 📥 设置导入会**覆盖现有配置**，请先备份原配置
10. 🔒 防呆模式默认启用，如需清理危险项请先关闭

> 第一次使用建议先扫描看看有哪些数据，再决定清理哪些项目。

## 开发

如需修改或扩展功能：

```bash
# 安装依赖
pip install PyQt5

# 运行程序
python trae_cache_cleaner.py
```

## 打包为独立 EXE

可使用 PyInstaller 将程序打包为独立的 `.exe` 文件，无需 Python 环境即可运行。

### 方式一：直接运行打包脚本（推荐）

双击 `build.bat`，脚本会自动检测当前环境的 Python，缺少依赖则自动安装并打包。

### 方式二：手动打包

```bash
# 确保已安装 PyQt5 和 PyInstaller
pip install PyQt5 pyinstaller

# 打包（包含 PyQt5，支持 GUI + CLI 双模式）
pyinstaller --onefile --console --name "TraeCacheCleaner" ^
            --icon "TraeCacheCleaner.ico" ^
            --add-data "TraeCacheCleaner.ico;." ^
            trae_cache_cleaner.py
```

### 打包说明

| 选项 | 说明 |
|------|------|
| `--onefile` | 生成单个 exe 文件 |
| `--console` | 保留控制台窗口（CLI 模式需要） |
| `--icon` | 设置程序图标 |

> **为什么需要 PyQt5 环境打包？**
> 程序代码中 `ScanThread(QThread)` 和 `CleanThread(QThread)` 继承自 `QThread`，
> 这些类在无 PyQt5 的环境中无法编译。在安装 PyQt5 的环境中打包可确保 exe 同时支持 GUI 和 CLI 双模式，
> 且在无 PyQt5 的机器上也能自动降级为 CLI 模式运行。

### 输出

打包完成后 exe 位于 `output\TraeCacheCleaner.exe`，可直接运行或分发。

```bash
# GUI 模式（默认，需系统有 PyQt5 或 exe 已包含）
output\TraeCacheCleaner.exe

# CLI 模式
output\TraeCacheCleaner.exe --cli
```

## 项目结构

```
TraeCacheCleaner-PyQt/
├── trae_cache_cleaner.py      # 主程序（GUI + CLI 双模式）
├── TraeCacheCleaner.ico       # 程序图标
├── run.bat                    # Windows 启动脚本
├── build.bat                  # PyInstaller 打包脚本
├── requirements.txt           # 依赖声明
├── output/                    # 打包输出目录
│   └── TraeCacheCleaner.exe   # 独立可执行文件（~37MB）
└── README.md                  # 说明文档
```

## 更新日志

### v1.3
- 📊 新增已选项目大小统计，实时显示勾选数量和大小
- 🔄 对话记录支持按时间/大小/名称排序
- 🖱️ 完善所有项目的悬浮提示，显示完整路径、时间和安全说明
- 🌙 深色主题全面适配，修复所有弹出窗口文字颜色
- 🛡️ 防呆模式交互优化：关闭时弹窗警告，默认取消
- 🔍 扩展扫描适配国际版/国内版双路径
- 💬 对话记录扫描路径修复（chatSessions → History）
- 🧹 缓存项从 18 项扩展至 22 项

### v1.2
- ✨ 合并 GUI 和 CLI 为单文件架构
- 🔧 添加 `--gui/-g` 参数强制使用 GUI 模式
- 🎯 优化启动逻辑，自动检测可用模式

### v1.1
- 添加防呆模式，默认启用
- 增加安全级别标识（✅/⚠️/🗑️）
- 完善悬浮提示信息
- 添加"仅选安全项"按钮
- 更新窗口图标
- 更新为通用部署方式

### v1.0
- 初始版本
- 基础缓存清理功能
- MCP 管理功能
- 设置导入/导出功能

## 常见问题

### Q: 在我的电脑上找不到 Trae IDE 的缓存路径怎么办？

A: 程序会自动检测标准路径。如果位置不同，可能需要手动修改代码中的路径配置。

### Q: 可以用在 Linux/macOS 上吗？

A: 目前主要针对 Windows 优化，但核心功能可能在其他平台上也能工作，需要修改路径检测逻辑。

### Q: 运行 `python trae_cache_cleaner.py` 进不了 GUI？

A: 这种情况基本不会发生。程序会自动搜索系统中所有安装了 PyQt5 的 Python 解释器（如 conda base 环境），找到后自动调用它启动 GUI。仅当全系统都找不到 PyQt5 时才降级 CLI。

   如果确实进了 CLI，最简单的办法是直接双击 `output\TraeCacheCleaner.exe`（已内置 PyQt5）。

### Q: 程序运行报错说找不到 PyQt5 怎么办？

A: 直接用打包好的 `output\TraeCacheCleaner.exe` 即可，已包含 PyQt5。如需从源码运行，请安装 PyQt5：`pip install PyQt5`。
