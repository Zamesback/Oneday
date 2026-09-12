# OneDay 一日 — Android 版构建说明

OneDay 的安卓版 = **Android WebView 壳 + 原生语音桥**。前端就是仓库里的 `app/index.html`
（已内置移动端布局、IndexedDB 持久化、Android 原生语音桥适配），壳负责：
- 用系统 WebView 加载本地页面（纯前端模式，无需任何后端/服务器）
- 用系统 `SpeechRecognizer` 做连续语音识别，推送给页面（页面自动走 `startAndroidVoice` 分支）

## 环境要求
- macOS / Windows / Linux 均可
- [Android Studio](https://developer.android.com/studio)（较新版本即可，自带 JDK 与 Gradle）
- 或：已有 Android SDK + JDK 17，用命令行 `./gradlew assembleDebug`

## 构建步骤（Android Studio）
1. 用 Android Studio 打开本目录（`android/`）
2. 等待 Gradle 同步完成（首次会自动下载依赖，需网络）
3. 菜单 Build → Build APK(s)，或直接点 ▶ 运行到真机/模拟器
4. 产物位置：`android/app/build/outputs/apk/debug/app-debug.apk`

## 安装（侧载）
1. 手机上开启「允许安装未知来源应用」
2. 把 `app-debug.apk` 传到手机（微信/网盘/USB 均可），点击安装
3. 首次使用：进入设置页配置你的 LLM API Key（DeepSeek 或豆包）
4. 点底部中间红色「对话」按钮开始语音闲聊

## 权限说明
- 麦克风：语音识别必需（首次点录音时系统会弹窗授权）
- 网络：连接你配置的 LLM API 需要
- 所有数据存在手机本地（WebView IndexedDB），不上传任何服务器

## 内置资源更新
前端改版后，把 `app/index.html` 和 `app/assets/` 重新拷贝到
`android/app/src/main/assets/` 再重新构建即可：
```bash
cp app/index.html android/app/src/main/assets/index.html
cp -R app/assets android/app/src/main/assets/assets
```

## 已知边界
- 连续语音识别依赖系统 SpeechRecognizer，长录音在部分机型上会自动分段，
  页面端已做文本累积，不会丢字
- 生图（每日开屏页）：DeepSeek 只支持对话，生图需在设置里配多模态
  或免费生图通道（与桌面版一致）
