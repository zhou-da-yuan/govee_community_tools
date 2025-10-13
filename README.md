# Govee Community Tools

![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

本工具旨在帮助GoveeHome测试人员高效创建测试数据，账号管理等功能。通过图形界面（GUI）和后台逻辑模块的结合，您可轻松完成账户生成、邮件验证、批量操作等任务。

## 📁 项目结构

```
govee_community_tools/
├── .venv/                    # 虚拟环境目录
├── assets/                   # 静态资源文件
├── config/                   # 配置相关文件
│   ├── __init__.py
│   ├── _version_.py
│   ├── admin_settings.py
│   └── settings.py
├── core/                     # 核心功能模块
│   ├── __init__.py
│   ├── account_generator.py
│   ├── auth.py
│   ├── email_verifier.py
│   ├── operations.py
│   ├── session_manager.py
│   └── session_state.py
├── core_admin/               # 后台功能模块
│   ├── __init__.py
│   ├── admin_auth.py
│   ├── admin_operations.py
│   └── admin_session.py
├── data/                     # 数据存储目录
│   └── history/              # 历史记录
├── gui/                      # 图形用户界面
│   ├── pages/                # 功能界面
│       ├── account_tool.py       # 账号工具页面
│       ├── batch_page.py         # 批量账号操作页面
│       ├── single_account.py     # 账号操作页面
│       └── history_page.py       # 操作历史页面
│   ├── widgets/              # 界面组件
│       ├── aid_popup.py          # AID弹窗组件
│       ├── help_viewer.py        # 帮助文档组件
│       ├── log_text.py           # 日志组件
│       ├── placeholder_entry.py  # 输入框灰色文字提示组件
│       └── tooltip.py            # 鼠标悬停文字提示组件
│   ├── __init__.py
│   └── main_window.py        # 主界面
├── logs/                     # 日志文件
│   └── app.log
├── resources/                # 资源文件
│   ├── accounts_dev.json     # DEV环境账号配置
│   ├── accounts_pda.json     # PDA 环境账号配置
│   └── help.md               # 使用帮助文档
├── utils/                    # 工具函数
│   ├── __init__.py
│   ├── file_loader.py
│   ├── history.py
│   └── logger.py
├── .gitignore
├── build.py                  # 构建脚本
├── clean.py                  # 清理脚本
├── main.py                   # 主程序入口
├── requirements.txt          # 依赖包列表
└── README.md                 # 本文件
```

## 🧩 功能概述

- **批量账号操作**：使用不同的账号进行一次所选操作，可设置需要使用的账号数。
- **账号操作**：使用指定的账号进行多次所选操作，可设置操作次数。
- **账户生成**：自动创建 Govee 社区账户。
- **获取账号验证码**：自动获取验证码。
- **GUI 界面**：通过图形界面简化操作流程。
- **日志记录**：详细记录运行状态和错误信息。
- **数据持久化**：支持本地存储历史记录和配置。

## 🛠️ 安装与使用

### 1. 克隆项目
```bash
git clone https://github.com/yourusername/govee_community_tools.git
cd govee_community_tools
```

### 2. 创建虚拟环境并安装依赖
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### 3. 运行主程序
```bash
python main.py
```

### 4. 启动 GUI
启动后将自动打开图形界面窗口，可进行账户管理、任务调度等操作。

## 🔧 配置说明

- `config/settings.py`：全局配置项（如 API 地址、超时时间等）
- `config/admin_settings.py`：管理员专用设置
- `resources/accounts_dev.json` 和 `accounts_pda.json`：分别用于开发和生产环境的账号池
- `data/history/`：自动保存操作历史

## 📚 使用帮助

详细使用指南请参阅：[resources/help.md](resources/help.md)

## 📂 日志系统

所有运行日志均记录在 `logs/app.log` 中，便于调试和监控。

## 🧹 清理与维护

- 使用 `clean.py` 清理临时文件和缓存
- 使用 `build.py` 打包发布版本（如有需要）

## ✅ 依赖项

查看 `requirements.txt` 获取完整的依赖列表。


## 🤝 贡献

欢迎提交 Issue 或 Pull Request！请遵循以下步骤：
1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/xxx`)
3. 提交更改 (`git commit -m 'Add some awesome feature'`)
4. 推送到远程 (`git push origin feature/xxx`)
5. 创建 Pull Request

---

> ⚠️ 注意：本工具仅用于合法合规用途，请勿用于任何违反服务条款的行为。
