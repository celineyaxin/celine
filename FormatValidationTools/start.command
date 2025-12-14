#!/bin/bash
# 论文格式验证工具 - Mac/Linux 启动脚本
# 双击此文件即可启动（首次需要右键选择打开）

cd "$(dirname "$0")"

echo "========================================"
echo "学位论文格式验证工具"
echo "========================================"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3，请先安装 Python"
    echo "下载地址: https://www.python.org/downloads/"
    read -p "按回车键退出..."
    exit 1
fi

# 检查并安装依赖
echo "检查依赖..."
pip3 install -q -r requirements.txt

# 启动应用
echo "启动中，浏览器将自动打开..."
python3 app.py

