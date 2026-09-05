# OneDay / 一日

> 不用打字，只要闲聊。把你的生活记录成故事。
> No typing, just chat. Turn your life into stories.

![OneDay 主海报](marketing/posters/01-主海报/08-主海报-三元素组合版.png)

---

## 🌅 关于 OneDay / About OneDay

**中文：**

OneDay 是一个 AI 驱动的个人生活管理平台。你不需要手动录入任何数据——每天花 5-10 分钟跟 AI 说说话，它会帮你记录待办、项目、灵感、朋友、运动，并且在每个清晨为你生成一张专属于你的卡片，用你自己的方式开启新的一天。

这个产品源于一个简单的习惯：每天睡前跟 AI 复盘当天发生的一切。久而久之发现，你要能表达就要想得透，想得透才能说得出，说得出它才能记得住——而记得住，就衍生出了 OneDay 的一切。

**English:**

OneDay is an AI-powered personal life management platform. You don't need to manually input anything — spend 5-10 minutes chatting with AI every day, and it will help you record todos, projects, inspirations, friends, and exercise. Every morning, it generates a card unique to you, helping you start a new day in your own way.

This product originated from a simple habit: reviewing the day with AI before bed every night. Over time, I realized that to express yourself, you need to think clearly; to think clearly, you need to speak up; when you speak up, it can remember — and from remembering, everything about OneDay was born.

---

## ✨ 核心亮点 / Core Features

### 1. 不用打字，只要闲聊 / No Typing, Just Chat
一切通过和 AI 生活助手对话完成。它会自动帮你整理待办、项目、灵感、运动、朋友，你只需要说。
Everything is done through conversation with your AI life assistant. It automatically organizes your todos, projects, inspirations, exercise, and friends — you just need to talk.

### 2. 每日专属卡片 / Daily Exclusive Card
AI 结合你的状态、待办、节气、天气，每天生成一张独一无二的卡片。一年 365 天，你就有 365 张专属于你的卡片，记录你度过的每一天。
AI combines your state, todos, solar terms, and weather to generate a unique card every day. 365 days a year, you'll have 365 cards unique to you, recording every day you've lived.

### 3. Plog — 把日子录成播客 / Plog — Podcast as a Log
每一次闲聊，AI 都会帮你收集灵感。从灵感主题到节目大纲，一键录制，快速生成一期属于你的播客，把你的生活用语音的方式记录下来。
Every chat, AI helps you collect inspirations. From inspiration topic to show outline, one-click recording, quickly generate your own podcast, recording your life through voice.

### 4. 朋友图谱 / Friends Graph
AI 在闲聊中自动捕捉你提到的人，记录身份、关系和互动。被提及越多的人，在图谱里的节点越大——让你直观看到谁在你生活里最重要。
AI automatically captures people you mention in chats, recording identity, relationships, and interactions. The more someone is mentioned, the larger their node in the graph — letting you visually see who matters most in your life.

---

## 🖼 界面展示 / Screenshots

### 开屏页 · 千人千面 / Splash Page · Unique for Everyone

| 创业者 · 路演日 | 程序员 · 深夜写代码 |
|:---:|:---:|
| ![阿杰-创业者](marketing/sources/开屏页案例/桌面版-完整UI-1-阿杰-创业者-路演日.png) | ![小宇-程序员](marketing/sources/开屏页案例/桌面版-完整UI-2-小宇-程序员-深夜写代码.png) |

| 设计师 · 音乐节 | 白领 · 下班放松 |
|:---:|:---:|
| ![小林-设计师](marketing/sources/开屏页案例/桌面版-完整UI-3-小林-设计师-音乐节.png) | ![老张-白领](marketing/sources/开屏页案例/桌面版-完整UI-4-老张-白领-下班放松.png) |

### 核心模块 / Core Modules

| Plog 灵感 | 每日卡片 |
|:---:|:---:|
| ![Plog灵感](marketing/posters/04-模块介绍/09-模块介绍-1-Plog灵感.png) | ![每日卡片](marketing/posters/04-模块介绍/09-模块介绍-2-每日卡片.png) |

| 朋友图谱 |
|:---:|
| ![朋友图谱](marketing/posters/04-模块介绍/09-模块介绍-3-朋友图谱.png) |

---

## 📁 目录结构 / Project Structure

```
OneDay 一日/
├── app/                    # 正式版应用 / Production App
│   ├── index.html          # 前端应用 / Frontend
│   ├── server.py           # 后端服务（端口 8765）/ Backend (port 8765)
│   ├── 启动 OneDay.command  # 双击启动脚本 / Double-click launcher
│   ├── assets/             # 静态资源（壁纸等）/ Static assets
│   ├── data/               # 数据文件（JSON）/ Data files
│   ├── images/             # 图片资源 / Images
│   └── backups/            # 历史备份 / Backups
│
├── demo/                   # Demo 演示版 / Demo version
│   ├── index.html          # 主页面 / Main page
│   ├── plog-demo.html      # Plog 功能演示 / Plog demo
│   ├── index-friends.html  # 朋友图谱演示 / Friends graph demo
│   ├── index-cards.html    # 卡片集演示 / Cards collection demo
│   └── assets/             # 演示资源 / Demo assets
│
├── docs/                   # 设计文档 / Design Documents
│   ├── PRODUCT.md          # 产品定位 / Product positioning
│   ├── ARCHITECTURE.md     # 架构设计 / Architecture
│   ├── DESIGN.md           # 设计规范 / Design guidelines
│   ├── DATA_MODEL.md       # 数据模型 / Data model
│   ├── ROADMAP.md          # 路线图 / Roadmap
│   ├── CHANGELOG.md        # 变更日志 / Changelog
│   └── TASK.md             # 任务清单 / Task list
│
└── marketing/              # 宣传物料 / Marketing Materials
    ├── posters/            # 最终海报 / Final posters
    │   ├── 01-主海报/       # Main posters
    │   ├── 02-产品界面/     # Product UI
    │   ├── 03-人物演示/     # Persona demos
    │   └── 04-模块介绍/     # Module intros
    ├── sources/            # 素材源文件 / Source assets
    ├── html/               # 海报 HTML 源文件 / Poster HTML
    └── 历史版本/            # Historical versions
```

---

## 🚀 快速开始 / Getting Started

> ⚠️ **重要：必须先启动后端服务器，才能访问 localhost:8765**
> 不要直接双击 `index.html` 打开（file:// 协议下 API 调用会全部失败）。
>
> ⚠️ **Important: You must start the backend server first before accessing localhost:8765**
> Do NOT directly double-click `index.html` (API calls will fail under file:// protocol).

### 环境要求 / Requirements
- Python 3.7+（macOS 自带 / macOS comes with Python pre-installed）
- 现代浏览器（Chrome / Safari / Edge）

### 启动正式版 / Run Production App

**方式一：命令行 / Command Line**
```bash
cd app
python3 server.py
```

**方式二：macOS 双击启动 / macOS Double-click**
```
直接双击 app/启动 OneDay.command
```

启动成功后会显示：
```
OneDay / 一日 后端已启动
端口: 8765
访问: http://localhost:8765
```

然后在浏览器打开 / Then open in browser: **http://localhost:8765**

### 查看 Demo / View Demo
Demo 是纯静态页面，可以直接用浏览器打开 `demo/index.html` 体验。
Demo is a static page — simply open `demo/index.html` in your browser.

### 常见问题 / FAQ

**Q: 打开 localhost:8765 显示"无法访问此网站"怎么办？**
A: 说明后端服务器没有启动。请先在终端运行 `cd app && python3 server.py`，看到启动成功提示后再访问。

**Q: 提示 "python3: command not found" 怎么办？**
A: 说明电脑没装 Python。macOS 用户运行 `xcode-select --install` 安装，或从 https://www.python.org/downloads/ 下载安装。

**Q: 提示 "Address already in use" 怎么办？**
A: 8765 端口被占用了。可以修改 `app/server.py` 里的 `PORT = 8765` 为其他端口，或关闭占用端口的程序。

**Q: 直接双击 index.html 能打开但功能不正常？**
A: 正常现象。直接打开用的是 file:// 协议，AI 对话、定时任务、数据保存等功能都需要后端服务器支持。请用上面的方式启动服务器后访问。

**Q: 浏览器显示 "无法访问此网站" 或 "连接不安全"？**
A: 请检查地址栏是不是 `https://`（带 s）。我们的本地服务器是 HTTP 协议，必须用 `http://localhost:8765/`（不带 s）访问。有些浏览器会自动把 http 升级成 https，导致访问失败，手动改成 http 即可。

**Q: 怎么从零开始使用，不要预设的演示数据？**
A: 项目自带了演示数据（`app/data/` 目录），方便你快速体验。如果想从零开始：
1. 关闭服务器
2. 把 `app/data/` 目录重命名为 `app/data-demo/`（备份演示数据）
3. 把 `app/data-empty/` 目录重命名为 `app/data/`
4. 重新启动服务器，就是全新的空数据版本了

或者直接删除 `app/data/` 目录下的所有 `.json` 文件（保留 `settings.json`），重启服务器也会自动创建空数据。

---

## 🎨 设计风格 / Design Style

OneDay 采用 **Nothing × One** 混搭风格：
- **黑白红三原色** — 简洁、年轻、有态度
- **中文 Noto Serif SC 衬线体** — 温暖、有质感
- **英文 Space Mono 等宽体** — 电子感、个性
- **每日专属开屏图** — 年轻、大胆、千人千面

OneDay uses a **Nothing × One** mixed style:
- **Black, white, and red** — clean, young, with attitude
- **Noto Serif SC for Chinese** — warm, textured
- **Space Mono for English** — electronic,个性
- **Daily exclusive splash images** — young, bold, unique for everyone

---

## 🛠 技术栈 / Tech Stack

- **前端 / Frontend**: 原生 HTML + CSS + JavaScript（单页应用）
- **后端 / Backend**: Python Flask（轻量本地服务）
- **数据存储 / Data**: JSON 文件（本地存储，无需数据库）
- **AI 能力 / AI**: 支持接入 DeepSeek / 豆包等大模型 API

---

## 🗺 路线图 / Roadmap

- [x] 核心框架搭建 / Core framework
- [x] 开屏页 + 每日卡片 / Splash + Daily cards
- [x] 待办 + 重要事件 / Todos + Projects
- [x] Plog 灵感 + 录制 / Plog inspiration + recording
- [x] 朋友图谱 / Friends graph
- [x] AI 对话界面 / AI chat interface
- [x] 深色模式 / Dark mode
- [ ] AI 大模型真实接入 / Real AI model integration
- [ ] AI 生成个性化每日壁纸 / AI-generated daily wallpaper
- [ ] AI 生成专属每日寄语 / AI-generated daily message
- [ ] 系统日历对接 / System calendar integration
- [ ] 语音输入 / Voice input
- [ ] 移动端适配 / Mobile adaptation

---

## 📄 开源协议 / License

MIT License — 详见 [LICENSE](LICENSE) 文件。
MIT License — see [LICENSE](LICENSE) for details.

---

## 💌 联系 / Contact

如果你喜欢 OneDay，欢迎 Star 和贡献代码！
If you like OneDay, feel free to Star and contribute!

---

*OneDay / 一日 — 陪伴你过好每一天。*
*OneDay — accompanying you through every day.*
