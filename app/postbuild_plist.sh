#!/bin/bash
# OneDay 桌面版打包后处理：向 Info.plist 注入 macOS 权限声明
# PyInstaller 的 BUNDLE info_plist 参数在部分版本不生效，用 PlistBuddy 直接注入最可靠。
# 用法：bash postbuild_plist.sh [path/to/OneDay 一日.app]
set -e
APP="${1:-"$(dirname "$0")/dist/OneDay 一日.app"}"
PLIST="$APP/Contents/Info.plist"

add_or_set() {
  local key="$1" value="$2"
  if /usr/libexec/PlistBuddy -c "Print :$key" "$PLIST" >/dev/null 2>&1; then
    /usr/libexec/PlistBuddy -c "Set :$key $value" "$PLIST"
  else
    /usr/libexec/PlistBuddy -c "Add :$key $value" "$PLIST"
  fi
}

add_or_set "NSMicrophoneUsageDescription" "string 'OneDay 需要访问麦克风，用于语音记录你的每日生活与对话。'"
add_or_set "NSSpeechRecognitionUsageDescription" "string 'OneDay 需要语音识别权限，将你的语音转换为文字并记录。'"
add_or_set "NSAppleEventsUsageDescription" "string 'OneDay 需要访问系统事件以提供窗口控制。'"
add_or_set "LSApplicationCategoryType" "string 'public.app-category.productivity'"

echo "✅ Info.plist 权限声明已注入: $PLIST"
