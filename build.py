# build.py
import os
import sys
from PyInstaller.__main__ import run

from config.__version__ import __version__, __author__, __email__

# 项目路径
project_dir = os.path.dirname(os.path.abspath(__file__))

# 构建参数
spec_name = f"GoveeCommunityTool"
entry_point = "main.py"

# PyInstaller 参数
args = [
    entry_point,
    '--name=' + spec_name,
    '--windowed',           # 不显示控制台（适合 GUI）
    '--icon=assets/icon.ico',  # 可选：添加图标（建议 256x256 .ico）
    '--add-data=resources;resources',  # 复制 accounts 文件夹
    '--add-data=data/accounts;data/accounts',          # 复制 data/history 等
    '--clean',              # 清理缓存
    '--onefile',            # 打包成单个 exe（推荐）
    '--noconfirm'           # 覆盖输出
]

# Windows 下需要转换路径分隔符
if os.name == 'nt':
    def fix_path(p):
        return p.replace('/', '\\') if '/' in p else p
    args = [fix_path(arg) for arg in args]

print("🚀 开始打包...")
print("参数:", args)

# 调用 PyInstaller
run(args)

print("✅ 打包完成！")
print(f"可执行文件位于：dist/{spec_name}.exe")