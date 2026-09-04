# OneDay / 一日

> 不用打字，只要闲聊。把你的生活记录成故事。
> No typing, just chat. Turn your life into stories.

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

### 启动正式版 / Run Production App
```bash
cd app
python3 server.py
# 或双击 / or double-click: 启动 OneDay.command
```
浏览器打开 / Open in browser: http://localhost:8765

### 查看 Demo / View Demo
直接用浏览器打开 `demo/index.html` 即可体验演示版本。
Simply open `demo/index.html` in your browser to experience the demo.

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
