#!/bin/bash
cd "$(dirname "$0")"
echo "========================================"
echo "  Zams CRM 启动中..."
echo "========================================"
echo ""
echo "  前端地址: http://localhost:8765"
echo "  数据文件: data.xlsx"
echo "  按 Ctrl+C 停止服务"
echo ""
python3 server.py
