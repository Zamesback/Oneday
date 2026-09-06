#!/bin/bash
# OneDay 一日 - 启动脚本
# 双击启动 OneDay 应用

cd "$(dirname "$0")"

# 检查是否已经在运行
if lsof -ti:8765 > /dev/null 2>&1; then
    echo "✅ OneDay 已经在运行中"
    echo "   正在打开浏览器..."
    open "http://localhost:8765/"
    exit 0
fi

echo "========================================"
echo "  OneDay 一日 启动中..."
echo "========================================"
echo ""
echo "  🌅 欢迎使用 OneDay"
echo "  📅 今天是你的 Day One"
echo ""
echo "  前端地址: http://localhost:8765"
echo "  数据目录: $(pwd)/data"
echo "  按 Ctrl+C 停止服务"
echo ""
echo "========================================"
echo ""

# 启动服务器
python3 server.py &
SERVER_PID=$!

# 等待服务器启动
sleep 2

# 打开浏览器
open "http://localhost:8765/"

# 等待服务器进程
wait $SERVER_PID
