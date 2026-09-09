#!/bin/bash
# AgentNexus 看板入口 — 一键启动服务并打开看板
cd /Users/zames/Desktop/agent-collab-dev

if lsof -ti:8766 > /dev/null 2>&1; then
    echo "服务已在运行，直接打开看板..."
else
    echo "启动服务..."
    nohup python3 server.py > /tmp/collab_server.log 2>&1 &
    sleep 2
fi

open http://localhost:8766
sleep 1
# 自动关闭终端窗口
osascript -e 'tell application "Terminal" to close front window' 2>/dev/null
exit 0
