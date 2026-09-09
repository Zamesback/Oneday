#!/bin/bash
# OneDay 服务器看门狗
# 每分钟检查一次服务器状态，如果挂了自动重启

APP_DIR="/Users/zames/Desktop/Project/OneDay 一日/app"
LOG_FILE="/tmp/oneday-server.log"
WATCHDOG_LOG="/tmp/oneday-watchdog.log"
PORT=8765

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 看门狗已启动" >> "$WATCHDOG_LOG"

while true; do
    # 检查端口是否被占用
    if ! lsof -ti:$PORT > /dev/null 2>&1; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  服务器挂了，正在自动重启..." >> "$WATCHDOG_LOG"
        
        # 杀掉可能残留的进程
        pkill -9 -f "python3 server.py" 2>/dev/null
        sleep 1
        
        # 重启服务器
        cd "$APP_DIR" && nohup python3 server.py >> "$LOG_FILE" 2>&1 &
        sleep 3
        
        # 验证是否重启成功
        if lsof -ti:$PORT > /dev/null 2>&1; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 服务器已自动重启，PID: $(lsof -ti:$PORT)" >> "$WATCHDOG_LOG"
        else
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ 自动重启失败，请手动检查" >> "$WATCHDOG_LOG"
        fi
    fi
    
    # 每分钟检查一次
    sleep 60
done
