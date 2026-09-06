#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OneDay / 一日 - 轻量后端
AI 驱动的个人工作管理平台
端口: 8765
"""

import http.server
import json
import os
import sys
import urllib.parse
import datetime
import threading
import subprocess
import re
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_DIR = os.path.join(BASE_DIR, 'data')
PORT = 8765

os.makedirs(JSON_DIR, exist_ok=True)

# ===== 数据存储层 =====

def load_json(filename, default=None):
    path = os.path.join(JSON_DIR, filename)
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载 {filename} 失败: {e}")
    return default if default is not None else []

def save_json(filename, data):
    path = os.path.join(JSON_DIR, filename)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存 {filename} 失败: {e}")
        return False

def gen_id(prefix):
    return prefix + '_' + str(int(datetime.datetime.now().timestamp() * 1000)) + '_' + str(random.randint(100, 999))

# ===== 节气与节日计算 =====

# 24节气（21世纪 C 值，用于公式 [Y*D+C]-L）
SOLAR_TERMS_C = {
    '小寒': 5.4055, '大寒': 20.12, '立春': 3.87, '雨水': 18.73,
    '惊蛰': 5.63, '春分': 20.646, '清明': 4.81, '谷雨': 20.1,
    '立夏': 5.52, '小满': 21.04, '芒种': 5.678, '夏至': 21.37,
    '小暑': 7.108, '大暑': 22.83, '立秋': 7.5, '处暑': 23.13,
    '白露': 7.646, '秋分': 23.042, '寒露': 8.318, '霜降': 23.438,
    '立冬': 7.438, '小雪': 22.36, '大雪': 7.18, '冬至': 21.94,
}

# 节气顺序
SOLAR_TERMS_ORDER = list(SOLAR_TERMS_C.keys())

# 常见节日（月-日）
FESTIVALS = {
    '01-01': '元旦', '02-14': '情人节', '03-08': '妇女节', '03-12': '植树节',
    '04-01': '愚人节', '05-01': '劳动节', '05-04': '青年节', '06-01': '儿童节',
    '07-01': '建党节', '08-01': '建军节', '09-10': '教师节', '10-01': '国庆节',
    '12-24': '平安夜', '12-25': '圣诞节',
}

def get_solar_term(date=None):
    """获取指定日期的节气（如果当天是节气则返回节气名，否则返回最近的节气和距离天数）"""
    if date is None:
        date = datetime.date.today()
    
    year = date.year
    y = year % 100
    d = 0.2422
    l = y // 4  # 闰年数
    
    # 计算每个节气的日期
    term_dates = {}
    for i, (name, c) in enumerate(SOLAR_TERMS_C.items()):
        month = (i // 2) + 1
        day = int(y * d + c) - l
        # 修正特殊年份（2026年部分节气需要+1）
        if year == 2026 and name in ['立春', '惊蛰', '清明', '立夏', '芒种', '小暑', '立秋', '白露', '寒露', '立冬', '大雪', '小寒']:
            day += 0  # 公式已较准确，特殊情况可微调
        term_dates[name] = datetime.date(year, month, day)
    
    # 检查当天是否是节气
    today_str = date.strftime('%m-%d')
    for name, term_date in term_dates.items():
        if term_date == date:
            return {'is_today': True, 'name': name, 'days_until': 0}
    
    # 找下一个节气
    future_terms = [(name, td) for name, td in term_dates.items() if td > date]
    if future_terms:
        next_name, next_date = min(future_terms, key=lambda x: x[1])
        days_until = (next_date - date).days
        return {'is_today': False, 'name': next_name, 'days_until': days_until, 'next_date': next_date.isoformat()}
    
    # 如果今年都过了，返回明年第一个节气
    return {'is_today': False, 'name': '小寒', 'days_until': (datetime.date(year+1, 1, 5) - date).days}

def get_festival(date=None):
    """获取指定日期的节日"""
    if date is None:
        date = datetime.date.today()
    date_str = date.strftime('%m-%d')
    return FESTIVALS.get(date_str, '')

def get_date_context(date=None):
    """获取日期上下文（节气+节日+星期），用于 AI 生成寄语"""
    if date is None:
        date = datetime.date.today()
    
    weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    term = get_solar_term(date)
    festival = get_festival(date)
    
    context = {
        'date': date.isoformat(),
        'weekday': weekday_names[date.weekday()],
        'month': date.month,
        'day': date.day,
    }
    
    if term['is_today']:
        context['solar_term'] = term['name']
        context['solar_term_is_today'] = True
    else:
        context['next_solar_term'] = term['name']
        context['days_until_solar_term'] = term['days_until']
        context['solar_term_is_today'] = False
    
    if festival:
        context['festival'] = festival
    
    return context

# ===== 模块配置 =====
MODULES = {
    'projects': {'file': 'projects.json', 'prefix': 'proj', 'label': '重要事件'},
    'todos': {'file': 'todos.json', 'prefix': 'todo', 'label': '待办'},
    'inspirations': {'file': 'inspirations.json', 'prefix': 'insp', 'label': '灵感'},
    'exercises': {'file': 'exercises.json', 'prefix': 'exer', 'label': '运动'},
    'friends': {'file': 'friends.json', 'prefix': 'friend', 'label': '朋友'},
    'relationships': {'file': 'relationships.json', 'prefix': 'rel', 'label': '关系'},
    'chats': {'file': 'chats.json', 'prefix': 'chat', 'label': '对话'},
    'inputs': {'file': 'inputs.json', 'prefix': 'input', 'label': '每日想法'},
    'cards': {'file': 'cards.json', 'prefix': 'card', 'label': '每日卡片'},
}

def load_module(name):
    if name not in MODULES:
        return []
    return load_json(MODULES[name]['file'], [])

def save_module(name, data):
    if name not in MODULES:
        return False
    return save_json(MODULES[name]['file'], data)

# ===== 每日卡片 =====

def generate_daily_card():
    """生成当日卡片，从开屏页配置、待办、运动、对话中提取数据"""
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    cards = load_module('cards')
    
    # 检查今天是否已有卡片
    for card in cards:
        if card.get('date') == today:
            return card
    
    # 收集数据
    todos = load_module('todos')
    exercises = load_module('exercises')
    chats = load_module('chats')
    settings = load_settings()
    
    todos_today = [t for t in todos if (t.get('due_date') or t.get('date', '')).startswith(today)]
    todos_completed = [t for t in todos_today if t.get('status') == 'done']
    exercises_today = [e for e in exercises if e.get('date', '').startswith(today)]
    
    # 从最近的对话中提取亮点
    highlights = []
    for chat in chats[:10]:
        if chat.get('role') == 'user' and len(chat.get('content', '')) > 10:
            highlights.append(chat['content'][:50])
            if len(highlights) >= 3:
                break
    
    # 获取壁纸配置
    wallpaper = settings.get('wallpaper', 'default')
    quote = settings.get('dailyQuote', '把你的故事讲好，世界会听。')
    mood = settings.get('todayMood', 'neutral')
    
    card = {
        'id': gen_id('card'),
        'date': today,
        'wallpaper': wallpaper,
        'quote': quote,
        'mood': mood,
        'todos_completed': len(todos_completed),
        'todos_total': len(todos_today),
        'highlights': highlights,
        'exercise': exercises_today[0].get('type', '') if exercises_today else '',
        'created_at': datetime.datetime.now().isoformat(),
    }
    
    cards.insert(0, card)
    save_module('cards', cards)
    return card

def get_card_stats():
    """获取卡片统计信息"""
    cards = load_module('cards')
    total = len(cards)
    
    # 计算连续天数
    streak = 0
    today = datetime.datetime.now().date()
    card_dates = set()
    for card in cards:
        try:
            d = datetime.datetime.strptime(card.get('date', ''), '%Y-%m-%d').date()
            card_dates.add(d)
        except:
            pass
    
    check_date = today
    while check_date in card_dates:
        streak += 1
        check_date -= datetime.timedelta(days=1)
    
    # 按月份统计
    monthly = {}
    for card in cards:
        month = card.get('date', '')[:7]
        if month:
            monthly[month] = monthly.get(month, 0) + 1
    
    return {
        'total': total,
        'streak': streak,
        'monthly': monthly,
    }

# ===== 朋友提及频率 =====

def update_friend_mention(name, context=''):
    """更新朋友的提及次数"""
    friends = load_module('friends')
    found = False
    
    for friend in friends:
        if friend.get('name') == name:
            friend['mention_count'] = friend.get('mention_count', 0) + 1
            friend['last_mentioned'] = datetime.datetime.now().isoformat()
            if context and context not in friend.get('context_tags', []):
                friend.setdefault('context_tags', []).append(context)
            found = True
            break
    
    if not found:
        # 自动创建草稿朋友
        friends.insert(0, {
            'id': gen_id('friend'),
            'name': name,
            'identity': '',
            'relationship': '',
            'notes': '',
            'status': 'draft',
            'source': 'ai_extract',
            'mention_count': 1,
            'last_mentioned': datetime.datetime.now().isoformat(),
            'first_mentioned': datetime.datetime.now().isoformat(),
            'context_tags': [context] if context else [],
            'createdAt': datetime.datetime.now().isoformat(),
        })
    
    save_module('friends', friends)
    return friends

def get_friends_graph_data():
    """获取关系图谱数据，节点大小=提及次数"""
    friends = load_module('friends')
    relationships = load_module('relationships')
    
    nodes = []
    for friend in friends:
        mention_count = friend.get('mention_count', 0)
        # 节点大小基于提及次数，最小10，最大60
        size = min(60, max(10, 10 + mention_count * 2))
        nodes.append({
            'id': friend.get('id'),
            'name': friend.get('name'),
            'size': size,
            'mention_count': mention_count,
            'relationship': friend.get('relationship', 'unknown'),
            'status': friend.get('status', 'draft'),
            'last_mentioned': friend.get('last_mentioned', ''),
        })
    
    links = []
    for rel in relationships:
        links.append({
            'source': rel.get('source_id', ''),
            'target': rel.get('target_id', ''),
            'type': rel.get('type', 'knows'),
            'strength': rel.get('strength', 1),
        })
    
    return {
        'nodes': nodes,
        'links': links,
        'total_friends': len(friends),
        'total_mentions': sum(f.get('mention_count', 0) for f in friends),
    }

def extract_names_from_text(text):
    """简单的中文人名提取（基于常见姓氏和模式，实际应由AI完成）"""
    surnames = '赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳酆鲍史唐费廉岑薛雷贺倪汤滕殷罗毕郝邬安常乐于时傅皮卞齐康伍余元卜顾孟平黄和穆萧尹姚邵湛汪祁毛禹狄米贝明臧计伏成戴谈宋茅庞熊纪舒屈项祝董梁杜阮蓝闵席季麻强贾路娄危江童颜郭梅盛林刁钟徐邱骆高夏蔡田樊胡凌霍虞万支柯昝管卢莫经房裘缪干解应宗丁宣贲邓郁单杭洪包诸左石崔吉钮龚程嵇邢滑裴陆荣翁荀羊於惠甄曲家封芮羿储靳汲邴糜松井段富巫乌焦巴弓牧隗山谷车侯宓蓬全郗班仰秋仲伊宫宁仇栾暴甘钭厉戎祖武符刘景詹束龙叶幸司韶郜黎蓟薄印宿白怀蒲邰从鄂索咸籍赖卓蔺屠蒙池乔阴郁胥能苍双闻莘党翟谭贡劳逄姬申扶堵冉宰郦雍却璩桑桂濮牛寿通边扈燕冀郏浦尚农温别庄晏柴瞿阎充慕连茹习宦艾鱼容向古易慎戈廖庾终暨居衡步都耿满弘匡国文寇广禄阙东欧殳沃利蔚越夔隆师巩厍聂晁勾敖融冷訾辛阚那简饶空曾毋沙乜养鞠须丰巢关蒯相查后荆红游竺权逯盖益桓公'
    names = []
    # 简单匹配：2-4个汉字，首字为姓氏
    for i in range(len(text) - 1):
        if text[i] in surnames:
            for length in range(2, 5):
                if i + length <= len(text):
                    candidate = text[i:i+length]
                    if all('一' <= c <= '鿿' for c in candidate):
                        # 排除常见词
                        if candidate not in ['什么', '怎么', '这个', '那个', '我们', '你们', '他们', '今天', '明天', '昨天']:
                            if candidate not in names:
                                names.append(candidate)
                        break
    return names[:10]  # 最多返回10个




# ===== 设置 =====

DEFAULT_SETTINGS = {
    'morningTime': '07:30',
    'eveningTime': '22:00',
    'exerciseReminderTime': '20:00',
    'aiStyle': 'encouraging',
    'apiKey': '',
    'apiProvider': 'deepseek',
    'wallpaperMode': 'static',
    'notificationsEnabled': True,
    'userName': '',
}

def load_settings():
    s = load_json('settings.json', {})
    merged = DEFAULT_SETTINGS.copy()
    merged.update(s)
    return merged

def save_settings(settings):
    return save_json('settings.json', settings)

# ===== 系统通知 =====

def send_notification(title, message):
    """发送 macOS 系统通知"""
    try:
        script = f'display notification "{message}" with title "{title}"'
        subprocess.run(['osascript', '-e', script], capture_output=True, timeout=5)
        return True
    except Exception as e:
        print(f"发送通知失败: {e}")
        return False


# ===== AI Agent Harness 框架 =====
# OneDay AI 生活伙伴的完整 Prompt 模板和调用框架
# 支持模拟模式和真实 API 模式（DeepSeek / 豆包）

AI_AGENT_SYSTEM_PROMPT = """你是 OneDay，用户的 AI 生活伙伴。

## 你的角色
- 你不是一个冰冷的助手，你是用户的生活伙伴、倾听者、记录者
- 用户会跟你闲聊，告诉你他的一天、心情、想法、计划
- 你的语气是温暖、鼓励、自然的，像一个懂他的朋友
- 不要太官方，不要太机械，用自然的口语化表达

## 你的核心能力
1. **倾听与回应**：回应用户说的话，给予情感支持和建议
2. **信息捕捉**：从用户的话中自动识别并提取以下信息：
   - 待办事项（todos）：用户说要做什么、需要做什么、记得做什么、要参加什么会议、什么评审、什么截止日期、什么汇报。**只要是未来要做的事情，都应该识别成待办！**
   - 重要事件/项目（projects）：用户提到的正在跟进的长期项目、目标、客户关系（注意：具体的会议、评审、截止日期应该识别成待办，不是项目）
   - 灵感（inspirations）：用户突然想到的想法、创意、点子
   - 朋友/人物（friends）：用户提到的人名、身份、关系
   - 运动（exercise）：用户提到运动、跑步、健身等（没有提到就 status=none）
   - 情绪状态（mood）：用户当前的心情状态
3. **主动关心**：在合适的时候提醒用户、鼓励用户、给出建议

## 输出格式（严格遵守 JSON 格式）
你必须返回一个 JSON 对象，包含以下字段：
{
  "reply": "你对用户说的话，自然温暖的回应",
  "extracted": {
    "todos": [
      {"title": "待办内容", "due_date": "2026-09-06", "priority": "high/medium/low"}
    ],
    "projects": [{"name": "项目名", "stage": "跟进中", "notes": "备注"}],
    "inspirations": ["灵感1", "灵感2"],
    "friends": [{"name": "人名", "identity": "身份", "relationship": "关系"}],
    "exercise": {"status": "done/mentioned/none", "detail": "运动详情"},
    "mood": "happy/neutral/tired/angry/sad"
  },
  "suggestion": "可选的建议或提醒，没有就空字符串"
}

## 待办日期识别规则（非常重要）
- 用户说"明天做XX"，due_date 就是明天的日期（格式 YYYY-MM-DD）
- 用户说"后天做XX"，due_date 就是后天的日期
- 用户说"下周一/下周X做XX"，due_date 就是对应的日期
- 用户说"这周内做XX"，due_date 就是本周日的日期
- 用户说"月底做XX"，due_date 就是本月最后一天
- 用户说"9月25号有XX"、"9月25日XX"，due_date 就是 2026-09-25
- **会议、评审、汇报、截止日期、review 都要识别成待办！** 比如"下周四review PPT"、"9月25号商飞评审会"都要识别成待办
- 用户没有明确说时间，due_date 就是今天的日期
- priority 根据用户语气判断：紧急/重要=high，普通=medium，随便/low
- 今天的日期是：{{TODAY}}

## 重要规则
- 只返回 JSON，不要返回其他任何文字
- reply 要自然，不要说"我帮你记了..."这种机械的话，而是自然地回应
- 提取信息要准确，不要过度提取，不要把闲聊内容当成待办
- **【强制】todos 必须返回对象数组！每个待办必须是 {"title": "...", "due_date": "YYYY-MM-DD", "priority": "high/medium/low"} 格式，绝对不能返回纯字符串！**
- **待办一定要识别日期！** 用户说"明天/后天/下周"时，due_date 要对应到具体日期，不要都放今天；用户没说时间时，due_date 才是今天
- 如果用户只是闲聊，没有具体信息，extracted 里的数组就为空
- 情绪判断要基于用户的语气和内容
- 你是鼓励型的伙伴，多给正面反馈，但不要虚假
"""

def build_ai_context(user_message, history):
    """构建发送给 AI 的完整上下文"""
    settings = load_settings()
    name = settings.get('userName', '')
    
    # 获取用户当前数据摘要
    todos = load_module('todos')
    pending_todos = [t for t in todos if t.get('status') != 'done'][-5:]
    projects = load_module('projects')
    active_projects = [p for p in projects if p.get('status') not in ('done', 'cancelled')][-3:]
    friends = load_module('friends')[-5:]
    
    context_parts = []
    
    # 用户信息
    if name:
        context_parts.append(f"用户称呼：{name}")
    
    # 当前待办
    if pending_todos:
        context_parts.append(f"用户当前未完成的待办：{', '.join([t.get('title','') for t in pending_todos])}")
    
    # 当前项目
    if active_projects:
        context_parts.append(f"用户正在跟进的项目：{', '.join([p.get('name','') for p in active_projects])}")
    
    # 最近提到的人
    if friends:
        context_parts.append(f"用户最近提到的人：{', '.join([f.get('name','') for f in friends])}")
    
    context_str = "\n".join(context_parts) if context_parts else "暂无用户数据"
    
    # 构建历史对话（最近5轮）
    history_str = ""
    if history:
        recent = history[-10:]
        for msg in recent:
            role = "用户" if msg.get('role') == 'user' else "你"
            content = msg.get('content', '')[:200]
            history_str += f"{role}: {content}\n"
    
    full_prompt = f"""## 用户背景信息
{context_str}

## 最近对话历史
{history_str if history_str else '（暂无历史）'}

## 用户当前说的话
{user_message}

请按照上面的 JSON 格式回应。"""
    
    return full_prompt

def call_real_ai(system_prompt, user_prompt):
    """调用真实 AI API（DeepSeek / 豆包）
    预留接口，用户配置 API Key 后启用
    """
    settings = load_settings()
    provider = settings.get('apiProvider', 'mock')
    api_key = settings.get('apiKey', '')
    
    if not api_key or provider == 'mock':
        return None
    
    try:
        import urllib.request
        import json
        
        if provider == 'deepseek':
            url = 'https://api.deepseek.com/v1/chat/completions'
            model = 'deepseek-chat'
        elif provider == 'doubao':
            url = 'https://ark.cn-beijing.volces.com/api/v3/chat/completions'
            model = settings.get('model', 'doubao-pro-32k')
        else:
            return None
        
        payload = {
            'model': model,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            'temperature': 0.7,
            'max_tokens': 2000,
            'response_format': {'type': 'json_object'}
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            content = result['choices'][0]['message']['content']
            return json.loads(content)
            
    except Exception as e:
        print(f"调用真实 AI 失败: {e}")
        return None

def check_api_key():
    """检查 API Key 是否有效
    返回: {'valid': bool, 'message': str, 'provider': str}
    """
    settings = load_settings()
    provider = settings.get('apiProvider', 'mock')
    api_key = settings.get('apiKey', '')
    
    if not api_key or provider == 'mock':
        return {
            'valid': False,
            'message': '未配置 API Key',
            'provider': provider,
            'checked_at': datetime.datetime.now().isoformat()
        }
    
    try:
        import urllib.request
        import json
        
        if provider == 'deepseek':
            url = 'https://api.deepseek.com/v1/chat/completions'
            model = 'deepseek-chat'
        elif provider == 'doubao':
            url = 'https://ark.cn-beijing.volces.com/api/v3/chat/completions'
            model = settings.get('model', 'doubao-pro-32k')
        else:
            return {
                'valid': False,
                'message': f'不支持的提供商: {provider}',
                'provider': provider,
                'checked_at': datetime.datetime.now().isoformat()
            }
        
        # 用最小的请求来测试 API Key
        payload = {
            'model': model,
            'messages': [
                {'role': 'user', 'content': 'hi'}
            ],
            'max_tokens': 1
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
        )
        
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode('utf-8'))
            if 'choices' in result:
                return {
                    'valid': True,
                    'message': 'API Key 有效',
                    'provider': provider,
                    'checked_at': datetime.datetime.now().isoformat()
                }
            else:
                return {
                    'valid': False,
                    'message': f'API 返回异常: {json.dumps(result, ensure_ascii=False)[:100]}',
                    'provider': provider,
                    'checked_at': datetime.datetime.now().isoformat()
                }
                
    except urllib.error.HTTPError as e:
        error_msg = f'HTTP {e.code}'
        try:
            error_data = json.loads(e.read().decode('utf-8'))
            if 'error' in error_data:
                error_msg = error_data['error'].get('message', error_msg)
        except:
            pass
        return {
            'valid': False,
            'message': error_msg,
            'provider': provider,
            'checked_at': datetime.datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'valid': False,
            'message': f'检查失败: {str(e)}',
            'provider': provider,
            'checked_at': datetime.datetime.now().isoformat()
        }

def parse_ai_response(raw_response):
    """解析 AI 返回的 JSON，容错处理"""
    if isinstance(raw_response, dict):
        return raw_response
    
    if isinstance(raw_response, str):
        try:
            # 尝试直接解析
            return json.loads(raw_response)
        except:
            # 尝试提取 JSON 部分
            import re
            json_match = re.search(r'\{[\s\S]*\}', raw_response)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
    
    # 解析失败，返回默认结构
    return {
        'reply': raw_response if isinstance(raw_response, str) else '嗯，我在听。',
        'extracted': {
            'todos': [],
            'projects': [],
            'inspirations': [],
            'friends': [],
            'exercise': None,
            'mood': 'neutral'
        },
        'suggestion': ''
    }

def parse_due_date(date_str):
    """解析待办的截止日期，支持相对时间（明天、后天、下周一等）"""
    if not date_str:
        return datetime.date.today().isoformat()
    
    today = datetime.date.today()
    date_str = str(date_str).strip().lower()
    
    # 已经是 YYYY-MM-DD 格式
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
        return date_str
    except:
        pass
    
    # 相对时间解析
    if date_str in ['今天', '今日', 'today', 'today']:
        return today.isoformat()
    elif date_str in ['明天', '明日', 'tomorrow']:
        return (today + datetime.timedelta(days=1)).isoformat()
    elif date_str in ['后天', '后日', 'the day after tomorrow']:
        return (today + datetime.timedelta(days=2)).isoformat()
    elif date_str in ['大后天']:
        return (today + datetime.timedelta(days=3)).isoformat()
    
    # 下周X
    weekday_map = {'一': 0, '二': 1, '三': 2, '四': 3, '五': 4, '六': 5, '日': 6, '天': 6}
    for cn, wd in weekday_map.items():
        if date_str in [f'下周{cn}', f'下周{cn}', f'next {cn}']:
            days_ahead = (wd - today.weekday() + 7) % 7
            if days_ahead == 0:
                days_ahead = 7
            return (today + datetime.timedelta(days=days_ahead)).isoformat()
    
    # 本周X
    for cn, wd in weekday_map.items():
        if date_str in [f'本周{cn}', f'这周{cn}']:
            days_ahead = (wd - today.weekday()) % 7
            return (today + datetime.timedelta(days=days_ahead)).isoformat()
    
    # 周末
    if date_str in ['周末', '这周末', '本周六']:
        days_ahead = (5 - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        return (today + datetime.timedelta(days=days_ahead)).isoformat()
    
    # 月底
    if date_str in ['月底', '本月底', '月末']:
        if today.month == 12:
            next_month = datetime.date(today.year + 1, 1, 1)
        else:
            next_month = datetime.date(today.year, today.month + 1, 1)
        return (next_month - datetime.timedelta(days=1)).isoformat()
    
    # 默认返回今天
    return today.isoformat()

def extract_date_from_text(text):
    """从待办字符串里提取日期信息（容错处理）"""
    if not text:
        return datetime.date.today().isoformat()
    
    text = str(text).lower()
    today = datetime.date.today()
    
    # 检查常见的日期关键词（按优先级排序，长的在前）
    date_keywords = [
        ('大后天', '大后天'),
        ('后天', '后天'),
        ('明天', '明天'),
        ('今天', '今天'),
        ('今日', '今天'),
        ('下个星期一', '下周一'),
        ('下个星期二', '下周二'),
        ('下个星期三', '下周三'),
        ('下个星期四', '下周四'),
        ('下个星期五', '下周五'),
        ('下个星期六', '下周六'),
        ('下个星期日', '下周日'),
        ('下个礼拜一', '下周一'),
        ('下个礼拜二', '下周二'),
        ('下个礼拜三', '下周三'),
        ('下个礼拜四', '下周四'),
        ('下个礼拜五', '下周五'),
        ('下个礼拜六', '下周六'),
        ('下个礼拜天', '下周日'),
        ('下周一', '下周一'),
        ('下周二', '下周二'),
        ('下周三', '下周三'),
        ('下周四', '下周四'),
        ('下周五', '下周五'),
        ('下周六', '下周六'),
        ('下周日', '下周日'),
        ('本周一', '本周一'),
        ('本周二', '本周二'),
        ('本周三', '本周三'),
        ('本周四', '本周四'),
        ('本周五', '本周五'),
        ('本周六', '本周六'),
        ('本周日', '本周日'),
        ('这周一', '本周一'),
        ('这周二', '本周二'),
        ('这周三', '本周三'),
        ('这周四', '本周四'),
        ('这周五', '本周五'),
        ('这周六', '本周六'),
        ('这周日', '本周日'),
        ('礼拜一', '本周一'),
        ('礼拜二', '本周二'),
        ('礼拜三', '本周三'),
        ('礼拜四', '本周四'),
        ('礼拜五', '本周五'),
        ('礼拜六', '本周六'),
        ('礼拜天', '本周日'),
        ('周末', '周末'),
        ('这周末', '周末'),
        ('月底', '月底'),
        ('月末', '月底'),
    ]
    
    for keyword, normalized in date_keywords:
        if keyword in text:
            return parse_due_date(normalized)
    
    # 检查单独的"周X"格式（如"周三"、"周四"）
    # 逻辑：如果今天已经过了周X，就指下周；否则指本周
    weekday_map = {'一': 0, '二': 1, '三': 2, '四': 3, '五': 4, '六': 5, '日': 6, '天': 6}
    for cn, wd in weekday_map.items():
        if f'周{cn}' in text:
            if today.weekday() >= wd:
                days_ahead = (wd - today.weekday() + 7) % 7
                if days_ahead == 0:
                    days_ahead = 7
                return (today + datetime.timedelta(days=days_ahead)).isoformat()
            else:
                days_ahead = (wd - today.weekday()) % 7
                return (today + datetime.timedelta(days=days_ahead)).isoformat()
    
    # 检查 YYYY-MM-DD 格式
    import re
    date_match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', text)
    if date_match:
        try:
            year, month, day = int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))
            return datetime.date(year, month, day).isoformat()
        except:
            pass
    
    # 检查中文日期格式（如 9月15日、9月15号）
    cn_date_match = re.search(r'(\d{1,2})\s*月\s*(\d{1,2})\s*[日号]', text)
    if cn_date_match:
        try:
            month, day = int(cn_date_match.group(1)), int(cn_date_match.group(2))
            if 1 <= month <= 12 and 1 <= day <= 31:
                year = today.year
                if datetime.date(year, month, day) < today:
                    year += 1
                return datetime.date(year, month, day).isoformat()
        except:
            pass
    
    # 检查 MM-DD 格式（如 9-10、09/10）
    date_match2 = re.search(r'(\d{1,2})[-/](\d{1,2})', text)
    if date_match2:
        try:
            month, day = int(date_match2.group(1)), int(date_match2.group(2))
            if 1 <= month <= 12 and 1 <= day <= 31:
                year = today.year
                if datetime.date(year, month, day) < today:
                    year += 1
                return datetime.date(year, month, day).isoformat()
        except:
            pass
    
    # 默认返回今天
    return datetime.date.today().isoformat()

def clean_todo_title(title):
    """清理待办标题里的日期描述"""
    if not title:
        return title
    
    import re
    
    # 移除常见的日期描述（按优先级排序，长的在前）
    patterns_to_remove = [
        # 括号里的日期
        r'[（(]\s*(大后天|后天|明天|今天|今日|下个星期[一二三四五六日天]|下个礼拜[一二三四五六日天]|下周[一二三四五六日天]|本周[一二三四五六日天]|这周[一二三四五六日天]|礼拜[一二三四五六日天]|周[一二三四五六日天]|周末|这周末|月底|月末|\d{1,2}月\d{1,2}[日号]|\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2})\s*[)）]',
        # 结尾的日期
        r'\s*(大后天|后天|明天|今天|今日|下个星期[一二三四五六日天]|下个礼拜[一二三四五六日天]|下周[一二三四五六日天]|本周[一二三四五六日天]|这周[一二三四五六日天]|礼拜[一二三四五六日天]|周[一二三四五六日天]|周末|这周末|月底|月末|\d{1,2}月\d{1,2}[日号]|\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2})\s*$',
        # 开头的日期
        r'^(大后天|后天|明天|今天|今日|下个星期[一二三四五六日天]|下个礼拜[一二三四五六日天]|下周[一二三四五六日天]|本周[一二三四五六日天]|这周[一二三四五六日天]|礼拜[一二三四五六日天]|周[一二三四五六日天]|周末|这周末|月底|月末|\d{1,2}月\d{1,2}[日号]|\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2})\s*',
        # 中间的日期（后面跟动词或标点）
        r'\s*(大后天|后天|明天|今天|今日|下个星期[一二三四五六日天]|下个礼拜[一二三四五六日天]|下周[一二三四五六日天]|本周[一二三四五六日天]|这周[一二三四五六日天]|礼拜[一二三四五六日天]|周[一二三四五六日天]|周末|这周末|月底|月末|\d{1,2}月\d{1,2}[日号])\s*(要|去|做|跟|和|提交|准备|开会|汇报|写|，|,|。)',
    ]
    
    for pattern in patterns_to_remove:
        title = re.sub(pattern, r'\2' if r'\2' in pattern else '', title)
    
    # 清理多余的空格和标点
    title = re.sub(r'\s+', ' ', title)
    title = re.sub(r'^[，,。.、]+|[，,。.、]+$', '', title)
    
    return title.strip()

# ===== 保存提取的信息 =====
def save_extracted_info(extracted):
    """把 AI 提取的信息保存到对应模块"""
    saved = {'todos': 0, 'projects': 0, 'inspirations': 0, 'friends': 0, 'exercise': 0}
    
    # 保存待办
    if extracted.get('todos'):
        todos = load_module('todos')
        for todo_item in extracted['todos']:
            # 支持字符串格式（向后兼容）和对象格式
            if isinstance(todo_item, str):
                title = todo_item
                # 从字符串里提取日期信息（容错处理）
                due_date = extract_date_from_text(todo_item)
                priority = 'medium'
                # 清理标题里的日期描述
                title = clean_todo_title(title)
            elif isinstance(todo_item, dict):
                title = todo_item.get('title', '')
                due_date = parse_due_date(todo_item.get('due_date', ''))
                priority = todo_item.get('priority', 'medium')
            else:
                continue
            
            if title and len(title) > 1:
                todos.insert(0, {
                    'id': gen_id('todo'),
                    'title': title,
                    'priority': priority,
                    'status': 'pending',
                    'source': 'ai_extract',
                    'due_date': due_date,
                    'date': datetime.datetime.now().isoformat()
                })
                saved['todos'] += 1
        save_module('todos', todos)
    
    # 保存项目
    if extracted.get('projects'):
        projects = load_module('projects')
        for proj in extracted['projects']:
            if isinstance(proj, dict) and proj.get('name'):
                projects.insert(0, {
                    'id': gen_id('project'),
                    'name': proj['name'],
                    'stage': proj.get('stage', '规划中'),
                    'priority': 'medium',
                    'customer': proj.get('customer', ''),
                    'amount': proj.get('amount', ''),
                    'deadline': proj.get('deadline', ''),
                    'nextAction': proj.get('nextAction', ''),
                    'notes': proj.get('notes', ''),
                    'status': 'active',
                    'source': 'ai_extract',
                    'date': datetime.datetime.now().isoformat()
                })
                saved['projects'] += 1
        save_module('projects', projects)
    
    # 保存灵感
    if extracted.get('inspirations'):
        inspirations = load_module('inspirations')
        for insp_text in extracted['inspirations']:
            if insp_text and len(insp_text) > 1:
                inspirations.insert(0, {
                    'id': gen_id('insp'),
                    'content': insp_text,
                    'source': 'ai_extract',
                    'date': datetime.datetime.now().isoformat()
                })
                saved['inspirations'] += 1
        save_module('inspirations', inspirations)
    
    # 保存朋友
    if extracted.get('friends'):
        friends = load_module('friends')
        existing_names = [f.get('name') for f in friends]
        for friend in extracted['friends']:
            if isinstance(friend, dict) and friend.get('name'):
                if friend['name'] not in existing_names:
                    friends.insert(0, {
                        'id': gen_id('friend'),
                        'name': friend['name'],
                        'identity': friend.get('identity', ''),
                        'relationship': friend.get('relationship', ''),
                        'notes': '',
                        'status': 'draft',
                        'mention_count': 1,
                        'source': 'ai_extract',
                        'date': datetime.datetime.now().isoformat()
                    })
                    saved['friends'] += 1
                else:
                    # 已存在，增加提及次数
                    for f in friends:
                        if f.get('name') == friend['name']:
                            f['mention_count'] = f.get('mention_count', 0) + 1
                            break
        save_module('friends', friends)
    
    # 保存运动
    if extracted.get('exercise'):
        exercise = extracted['exercise']
        if isinstance(exercise, dict) and exercise.get('status') == 'done':
            exercises = load_module('exercises')
            today_str = datetime.date.today().isoformat()
            today_ex = [e for e in exercises if e.get('date', '').startswith(today_str) and e.get('status') == 'done']
            if not today_ex:
                exercises.insert(0, {
                    'id': gen_id('exercise'),
                    'status': 'done',
                    'detail': exercise.get('detail', '运动打卡'),
                    'source': 'ai_extract',
                    'date': datetime.datetime.now().isoformat()
                })
                saved['exercise'] += 1
                save_module('exercises', exercises)
    
    return saved

def chat_with_ai_harness(message, history):
    """AI Agent Harness 主入口
    优先调用真实 AI，失败则回退到模拟模式
    """
    # 构建上下文
    user_prompt = build_ai_context(message, history)
    
    # 替换系统提示词里的日期占位符
    today_str = datetime.date.today().isoformat()
    system_prompt = AI_AGENT_SYSTEM_PROMPT.replace('{{TODAY}}', today_str)
    
    # 尝试调用真实 AI
    ai_result = call_real_ai(system_prompt, user_prompt)
    
    if ai_result:
        # 真实 AI 模式
        parsed = parse_ai_response(ai_result)
        reply = parsed.get('reply', '嗯，我在听。')
        extracted = parsed.get('extracted', {})
        suggestion = parsed.get('suggestion', '')
        
        # 保存提取的信息
        saved = save_extracted_info(extracted)
        
        # 附加建议
        if suggestion:
            reply += f"\n\n{suggestion}"
        
        return reply, extracted, saved
    else:
        # 回退到模拟模式
        reply, extracted = chat_with_ai(message, history)
        saved = save_extracted_info(extracted)
        return reply, extracted, saved

# ===== 天气获取 =====

# 常见城市和风天气 LocationID 映射
CITY_LOCATION_MAP = {
    '北京': '101010100', '上海': '101020100', '广州': '101280101', '深圳': '101280601',
    '杭州': '101210101', '南京': '101190101', '成都': '101270101', '武汉': '101200101',
    '西安': '101110101', '重庆': '101040100', '天津': '101030100', '苏州': '101190401',
    '厦门': '101230201', '长沙': '101250101', '青岛': '101120201', '大连': '101070201',
    '沈阳': '101070101', '济南': '101120101', '郑州': '101180101', '合肥': '101220101',
    '福州': '101230101', '南昌': '101240101', '昆明': '101290101', '贵阳': '101260101',
    '南宁': '101300101', '海口': '101310101', '兰州': '101160101', '西宁': '101150101',
    '银川': '101170101', '乌鲁木齐': '101130101', '拉萨': '101140101', '呼和浩特': '101080101',
    '太原': '101100101', '石家庄': '101090101', '哈尔滨': '101050101', '长春': '101060101',
}

# 天气缓存
_weather_cache = {'data': None, 'date': None}

def get_weather():
    """获取当天天气（和风天气 API，带缓存）"""
    global _weather_cache
    today = datetime.date.today().isoformat()
    
    # 如果今天已经缓存过，直接返回
    if _weather_cache['date'] == today and _weather_cache['data']:
        return _weather_cache['data']
    
    settings = load_settings()
    api_key = settings.get('weatherApiKey', '')
    city = settings.get('weatherCity', '上海')
    
    if not api_key:
        return {'enabled': False, 'message': '未配置天气API Key'}
    
    # 获取城市 LocationID
    location = CITY_LOCATION_MAP.get(city, city)
    
    try:
        import urllib.request
        url = f'https://devapi.qweather.com/v7/weather/now?location={location}&key={api_key}'
        req = urllib.request.Request(url, headers={'User-Agent': 'OneDay/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        if data.get('code') == '200' and data.get('now'):
            now = data['now']
            weather_data = {
                'enabled': True,
                'city': city,
                'temp': now.get('temp', ''),
                'feels_like': now.get('feelsLike', ''),
                'text': now.get('text', ''),
                'wind_dir': now.get('windDir', ''),
                'wind_scale': now.get('windScale', ''),
                'humidity': now.get('humidity', ''),
                'icon': now.get('icon', ''),
                'update_time': data.get('updateTime', ''),
            }
            _weather_cache = {'data': weather_data, 'date': today}
            return weather_data
        else:
            return {'enabled': False, 'message': f'天气API返回错误: {data.get("code", "unknown")}'}
    except Exception as e:
        print(f'获取天气失败: {e}')
        return {'enabled': False, 'message': f'获取天气失败: {str(e)}'}

def get_weather_text():
    """获取天气的文本描述，用于 AI 生成寄语"""
    weather = get_weather()
    if not weather.get('enabled'):
        return ''
    return f"{weather['city']} {weather['text']}，{weather['temp']}°C，体感{weather['feels_like']}°C，{weather['wind_dir']}{weather['wind_scale']}级，湿度{weather['humidity']}%"

# ===== 晨间/晚间 AI 生成 =====

def generate_morning_greeting_ai():
    """用 AI 生成早间问候（更个性化，结合天气+节气+待办+项目）"""
    settings = load_settings()
    name = settings.get('userName', '')
    
    # 尝试真实 AI
    if settings.get('apiKey') and settings.get('apiProvider') != 'mock':
        try:
            todos = load_module('todos')
            pending = [t for t in todos if t.get('status') != 'done'][-5:]
            projects = load_module('projects')
            active = [p for p in projects if p.get('status') not in ('done', 'cancelled')][-3:]
            
            # 获取天气和节气
            weather_text = get_weather_text()
            date_context = get_date_context()
            
            # 构建节气/节日描述
            term_desc = ''
            if date_context.get('solar_term_is_today'):
                term_desc = f"今天是{date_context['solar_term']}"
            elif date_context.get('next_solar_term'):
                term_desc = f"距离{date_context['next_solar_term']}还有{date_context['days_until_solar_term']}天"
            
            festival_desc = f"今天是{date_context['festival']}" if date_context.get('festival') else ''
            
            context = f"""用户称呼：{name}
今天是{date_context['date']} {date_context['weekday']}
{term_desc}
{festival_desc if festival_desc else ''}
{weather_text if weather_text else ''}
今天有 {len(pending)} 个待办，{len(active)} 个进行中的项目。
待办：{', '.join([t.get('title','') for t in pending]) if pending else '无'}
项目：{', '.join([p.get('name','') for p in active]) if active else '无'}"""
            
            prompt = f"""你是 OneDay，用户的 AI 生活伙伴。现在是早上，请给用户生成一段温暖、个性化的早间问候寄语。

{context}

要求：
1. 称呼用户的名字
2. 自然地结合今天的天气、节气或节日（如果有）
3. 提到今天的待办或项目（自然地带过，不要罗列）
4. 语气温暖、鼓励、有活力，像朋友一样
5. 60-100字
6. 只返回寄语文字，不要其他内容，不要加引号"""
            
            result = call_real_ai("你是 OneDay，温暖的 AI 生活伙伴。", prompt)
            greeting = ''
            if result and isinstance(result, str):
                greeting = result
            elif result and isinstance(result, dict) and result.get('reply'):
                greeting = result['reply']
            
            if greeting:
                # 保存当天的寄语，供开屏页使用
                save_daily_greeting(greeting)
                return greeting
        except Exception as e:
            print(f"AI 早间问候生成失败: {e}")
    
    # 回退到模拟模式
    greeting = generate_morning_greeting()
    save_daily_greeting(greeting)
    return greeting

def save_daily_greeting(greeting):
    """保存当天的 AI 寄语"""
    settings = load_settings()
    today = datetime.date.today().isoformat()
    settings['dailyGreeting'] = {
        'content': greeting,
        'date': today,
        'generated_at': datetime.datetime.now().isoformat(),
    }
    save_settings(settings)

def get_daily_greeting():
    """获取当天的寄语（如果没有生成过，返回默认语录）"""
    settings = load_settings()
    today = datetime.date.today().isoformat()
    
    greeting_data = settings.get('dailyGreeting', {})
    if greeting_data.get('date') == today and greeting_data.get('content'):
        return greeting_data['content']
    
    # 如果今天还没生成，返回默认语录
    return get_daily_quote()

def generate_evening_prompt_ai():
    """用 AI 生成晚间总结提示"""
    settings = load_settings()
    name = settings.get('userName', '')
    
    # 尝试真实 AI
    if settings.get('apiKey') and settings.get('apiProvider') != 'mock':
        try:
            prompt = f"""你是 OneDay，用户的 AI 生活伙伴。现在是晚上，请给用户生成一段温暖的晚间问候，引导用户聊聊今天。

用户称呼：{name}

要求：
1. 称呼用户的名字
2. 关心用户今天过得怎么样
3. 语气温暖、放松、像朋友
4. 50字以内
5. 只返回问候文字，不要其他内容"""
            
            result = call_real_ai("你是 OneDay，温暖的 AI 生活伙伴。", prompt)
            if result and isinstance(result, str):
                return result
            elif result and isinstance(result, dict) and result.get('reply'):
                return result['reply']
        except Exception as e:
            print(f"AI 晚间问候生成失败: {e}")
    
    # 回退到模拟模式
    return generate_evening_prompt()


# ===== AI 模拟（规则匹配） =====

def extract_info_from_text(text):
    """从文本中规则匹配提取信息（模拟 AI）"""
    result = {
        'todos': [],
        'projects': [],
        'inspirations': [],
        'friends': [],
        'exercise': None,
        'mood': 'neutral',
        'summary': '',
    }
    
    # 提取待办：包含"要做"、"需要"、"记得"、"别忘了"等
    todo_patterns = [
        r'(?:要|需要|记得|别忘了|待办|todo)[：: ]?(.+?)(?:[。，,；;]|$)',
        r'(?:明天|今天|下周|这周)[要需](.+?)(?:[。，,；;]|$)',
    ]
    for pattern in todo_patterns:
        matches = re.findall(pattern, text)
        for m in matches:
            m = m.strip()
            if m and len(m) > 2 and len(m) < 100:
                result['todos'].append(m)
    
    # 提取灵感：包含"想到"、"灵感"、"idea"、"可以"等
    insp_patterns = [
        r'(?:想到|灵感|idea|有个想法|突然想)[：: ]?(.+?)(?:[。，,；;]|$)',
    ]
    for pattern in insp_patterns:
        matches = re.findall(pattern, text)
        for m in matches:
            m = m.strip()
            if m and len(m) > 2:
                result['inspirations'].append(m)
    
    # 提取运动：包含"跑步"、"运动"、"健身"、"打卡"等
    if re.search(r'(跑步|运动|健身|打卡|锻炼|游泳|瑜伽)', text):
        if re.search(r'(跑了|运动了|健身了|打卡了|完成|今天.*?公里)', text):
            result['exercise'] = {'status': 'done', 'detail': text[:50]}
        else:
            result['exercise'] = {'status': 'mentioned', 'detail': text[:50]}
    
    # 提取人名（简单规则：2-4个中文字，前面有"叫"、"是"、"跟"等）
    name_patterns = [
        r'(?:叫|是|跟|和|找|联系)[：: ]?([\u4e00-\u9fa5]{2,4})(?:[，,。.；; ]|$)',
    ]
    for pattern in name_patterns:
        matches = re.findall(pattern, text)
        for m in matches:
            # 过滤常见非人名
            if m not in ['今天', '明天', '昨天', '我们', '你们', '他们', '自己', '什么', '怎么', '为什么']:
                result['friends'].append(m)
    
    # 情绪判断（简单关键词）
    if re.search(r'(开心|高兴|棒|太好了|顺利|成功|签了|搞定)', text):
        result['mood'] = 'happy'
    elif re.search(r'(累|烦|焦虑|压力|难|搞不定|失败|糟糕|郁闷)', text):
        result['mood'] = 'tired'
    elif re.search(r'(生气|愤怒|讨厌|无语)', text):
        result['mood'] = 'angry'
    
    # 生成摘要
    result['summary'] = f"识别到 {len(result['todos'])} 个待办, {len(result['inspirations'])} 个灵感, {len(result['friends'])} 个人名"
    
    return result

def generate_morning_greeting():
    """生成早间问候（模拟）"""
    settings = load_settings()
    name = settings.get('userName', '')
    hour = datetime.datetime.now().hour
    
    greetings = [
        f"早上好，{name}。新的一天开始了。",
        f"早安，{name}。今天也要好好的。",
        f"{name}，早上好。愿今天顺利。",
        f"新的一天，{name}。慢慢来。",
    ]
    
    greeting = random.choice(greetings)
    
    # 附加今日信息
    todos = load_module('todos')
    pending = [t for t in todos if t.get('status') != 'done']
    projects = load_module('projects')
    active = [p for p in projects if p.get('status') not in ('done', 'cancelled')]
    
    extra = f"\n\n今天有 {len(pending)} 个待办，{len(active)} 个进行中的事件。"
    
    # 天气（模拟）
    weather_options = ["晴", "多云", "阴", "小雨"]
    weather = random.choice(weather_options)
    extra += f"\n今天天气{weather}。"
    
    return greeting + extra

def generate_evening_prompt():
    """生成晚间总结提示（模拟）"""
    settings = load_settings()
    name = settings.get('userName', '')
    
    prompts = [
        f"晚上好，{name}。今天过得怎么样？跟我聊聊吧。",
        f"{name}，今天辛苦了。说说今天做了什么，有什么想法？",
        f"一天结束了，{name}。有什么想跟我说的吗？",
        f"晚上好。今天有什么收获，有什么遗憾？跟我说说。",
    ]
    
    return random.choice(prompts)

def chat_with_ai(message, history):
    """AI 对话（模拟模式，规则匹配 + 鼓励型回应）"""
    settings = load_settings()
    name = settings.get('userName', '')
    
    # 提取信息
    extracted = extract_info_from_text(message)
    
    # 基础回应
    replies = []
    
    if extracted['mood'] == 'happy':
        replies.append(f"太好了！听到你这么说我也开心。")
    elif extracted['mood'] == 'tired':
        replies.append(f"辛苦了，累了就歇歇。不用什么都扛着。")
    elif extracted['mood'] == 'angry':
        replies.append(f"嗯，我听到了。生气是正常的，慢慢说。")
    else:
        replies.append(f"嗯，我在听。")
    
    # 待办反馈
    if extracted['todos']:
        replies.append(f"\n我帮你记了 {len(extracted['todos'])} 个待办：")
        for i, t in enumerate(extracted['todos'][:3], 1):
            replies.append(f"  {i}. {t}")
        if len(extracted['todos']) > 3:
            replies.append(f"  ...还有 {len(extracted['todos'])-3} 个")
    
    # 灵感反馈
    if extracted['inspirations']:
        replies.append(f"\n还有 {len(extracted['inspirations'])} 个灵感，我也记下了。灵感这东西，记下来就跑不掉。")
    
    # 运动反馈
    if extracted['exercise']:
        if extracted['exercise']['status'] == 'done':
            replies.append(f"\n今天运动了！棒，坚持下来不容易。")
        else:
            replies.append(f"\n提到运动了，今天打算动一动吗？")
    
    # 人名反馈
    if extracted['friends']:
        unique_names = list(set(extracted['friends']))
        if unique_names:
            replies.append(f"\n提到了 {len(unique_names)} 个人，我先草记下来，你可以去「朋友」里完善信息。")
    
    # 结尾
    endings = [
        "\n\n还有什么想聊的吗？",
        "\n\n慢慢来，不着急。",
        "\n\n我都记着呢。",
        "\n\n你说，我听着。",
    ]
    replies.append(random.choice(endings))
    
    return '\n'.join(replies), extracted

# ===== 每日壁纸 =====

WALLPAPER_GRADIENTS = [
    'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
    'linear-gradient(135deg, #e0eafc 0%, #cfdef3 100%)',
    'linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%)',
    'linear-gradient(135deg, #f6f7f9 0%, #d8dde3 100%)',
    'linear-gradient(135deg, #ece9e6 0%, #ffffff 100%)',
    'linear-gradient(135deg, #f0f2f5 0%, #d9dee3 100%)',
]

def get_daily_wallpaper():
    """获取每日开屏页数据（AI寄语+天气+节气+渐变背景）"""
    today = datetime.date.today().isoformat()
    # 基于日期选择固定的渐变，保证一天内不变
    day_index = datetime.date.today().toordinal() % len(WALLPAPER_GRADIENTS)
    
    # 获取日期上下文（节气+节日）
    date_context = get_date_context()
    
    # 获取天气
    weather = get_weather()
    
    # 获取 AI 生成的寄语（如果今天还没生成，返回默认语录）
    greeting = get_daily_greeting()
    
    return {
        'date': today,
        'weekday': date_context.get('weekday', ''),
        'type': 'gradient',
        'value': WALLPAPER_GRADIENTS[day_index],
        'quote': greeting,
        'weather': weather if weather.get('enabled') else None,
        'solar_term': {
            'name': date_context.get('solar_term') or date_context.get('next_solar_term', ''),
            'is_today': date_context.get('solar_term_is_today', False),
            'days_until': date_context.get('days_until_solar_term', 0),
        },
        'festival': date_context.get('festival', ''),
    }

QUOTES = [
    "复杂世界里，一个就够了。",
    "今天也要好好的。",
    "慢慢来，比较快。",
    "一天一事，一事一得。",
    "把今天过好，就是把一生过好。",
    "不用急，你已经在走了。",
    "今天的你，比昨天好一点就够了。",
    "日子是过出来的，不是想出来的。",
    "认真生活的人，运气不会太差。",
    "新的一天，旧的自己，但可以有新的开始。",
]

def get_daily_quote():
    day_index = datetime.date.today().toordinal() % len(QUOTES)
    return QUOTES[day_index]

# ===== 定时任务 =====

scheduler_running = False
last_morning_greet = None
last_evening_prompt = None
last_exercise_reminder = None

def check_time(target_str):
    """检查当前时间是否匹配目标时间（HH:MM）"""
    now = datetime.datetime.now()
    target = datetime.datetime.strptime(target_str, '%H:%M').time()
    return now.hour == target.hour and now.minute == target.minute

def scheduler_loop():
    """定时任务循环"""
    global scheduler_running, last_morning_greet, last_evening_prompt, last_exercise_reminder
    scheduler_running = True
    print("[定时任务] 已启动")
    
    while scheduler_running:
        try:
            settings = load_settings()
            today = datetime.date.today().isoformat()
            
            # 早间问候
            if settings.get('notificationsEnabled') and check_time(settings.get('morningTime', '07:30')):
                if last_morning_greet != today:
                    greeting = generate_morning_greeting_ai()
                    send_notification("OneDay 早上好", greeting[:100])
                    # 保存到对话
                    chats = load_module('chats')
                    chats.insert(0, {
                        'id': gen_id('chat'),
                        'role': 'assistant',
                        'content': greeting,
                        'type': 'morning_greeting',
                        'timestamp': datetime.datetime.now().isoformat(),
                    })
                    save_module('chats', chats)
                    last_morning_greet = today
                    print(f"[定时任务] 早间问候已发送")
            
            # 晚间总结提示
            if settings.get('notificationsEnabled') and check_time(settings.get('eveningTime', '22:00')):
                if last_evening_prompt != today:
                    prompt = generate_evening_prompt_ai()
                    send_notification("OneDay 晚上好", prompt[:100])
                    chats = load_module('chats')
                    chats.insert(0, {
                        'id': gen_id('chat'),
                        'role': 'assistant',
                        'content': prompt,
                        'type': 'evening_prompt',
                        'timestamp': datetime.datetime.now().isoformat(),
                    })
                    save_module('chats', chats)
                    last_evening_prompt = today
                    print(f"[定时任务] 晚间提示已发送")
            
            # 运动提醒
            if settings.get('notificationsEnabled') and check_time(settings.get('exerciseReminderTime', '20:00')):
                if last_exercise_reminder != today:
                    # 检查今天是否已运动
                    exercises = load_module('exercises')
                    today_str = datetime.date.today().isoformat()
                    today_exercise = [e for e in exercises if e.get('date', '').startswith(today_str) and e.get('status') == 'done']
                    if not today_exercise:
                        send_notification("OneDay 运动提醒", "今天还没运动哦，动一动吧。")
                        last_exercise_reminder = today
                        print(f"[定时任务] 运动提醒已发送")
        
        except Exception as e:
            print(f"[定时任务] 错误: {e}")
        
        # 每分钟检查一次
        threading.Event().wait(60)

def start_scheduler():
    """启动定时任务"""
    if not scheduler_running:
        t = threading.Thread(target=scheduler_loop, daemon=True)
        t.start()

# ===== 全量数据 =====

def get_all_data():
    return {
        'projects': load_module('projects'),
        'todos': load_module('todos'),
        'inspirations': load_module('inspirations'),
        'exercises': load_module('exercises'),
        'friends': load_module('friends'),
        'relationships': load_module('relationships'),
        'chats': load_module('chats'),
        'inputs': load_module('inputs'),
        'settings': load_settings(),
        'wallpaper': get_daily_wallpaper(),
        'meta': {'version': '3.0', 'name': 'OneDay', 'updatedAt': datetime.datetime.now().isoformat()}
    }

# ===== HTTP 服务器 =====

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def log_message(self, format, *args):
        try:
            msg = str(args[0]) if args else ''
            if '/api/' in msg:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")
        except Exception:
            pass

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == '/api/health':
            self.send_json({'status': 'ok', 'version': '3.0', 'name': 'OneDay', 'time': datetime.datetime.now().isoformat()})
            return

        if path == '/api/work-data':
            self.send_json(get_all_data())
            return

        if path == '/api/wallpaper':
            self.send_json(get_daily_wallpaper())
            return

        if path == '/api/settings':
            self.send_json(load_settings())
            return

        # API Key 自检
        if path == '/api/check-api':
            result = check_api_key()
            # 保存检查结果到 settings
            settings = load_settings()
            settings['apiStatus'] = result
            save_settings(settings)
            self.send_json(result)
            return

        # 卡片统计
        if path == '/api/cards/stats':
            self.send_json(get_card_stats())
            return

        # 朋友关系图谱数据
        if path == '/api/friends/graph':
            self.send_json(get_friends_graph_data())
            return

        # 通用模块 GET
        for module_name in MODULES:
            if path == f'/api/{module_name}':
                self.send_json(load_module(module_name))
                return

        # 静态文件
        if path == '/' or path == '':
            path = '/index.html'
        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length else '{}'
        try:
            data = json.loads(body)
        except:
            data = {}

        if path == '/api/work-data':
            for module_name in MODULES:
                if module_name in data:
                    save_module(module_name, data[module_name])
            if 'settings' in data:
                save_settings(data['settings'])
            self.send_json({'status': 'ok'})
            return

        if path == '/api/settings':
            save_settings(data)
            self.send_json({'status': 'ok'})
            return

        if path == '/api/analyze':
            text = data.get('text', '')
            result = extract_info_from_text(text)
            self.send_json(result)
            return

        if path == '/api/chat':
            message = data.get('message', '')
            history = data.get('history', [])
            
            # 使用 AI Agent Harness（优先真实AI，失败回退模拟）
            reply, extracted, saved = chat_with_ai_harness(message, history)
            
            # 保存用户消息
            chats = load_module('chats')
            chats.insert(0, {
                'id': gen_id('chat'),
                'role': 'user',
                'content': message,
                'timestamp': datetime.datetime.now().isoformat(),
            })
            
            # 保存 AI 回复
            chats.insert(0, {
                'id': gen_id('chat'),
                'role': 'assistant',
                'content': reply,
                'extracted': extracted,
                'saved': saved,
                'timestamp': datetime.datetime.now().isoformat(),
            })
            save_module('chats', chats)
            
            self.send_json({'reply': reply, 'extracted': extracted, 'saved': saved})
            return

        if path == '/api/notify/test':
            send_notification("OneDay 测试", "这是一条测试通知。")
            self.send_json({'status': 'ok'})
            return

        # 生成当日卡片
        if path == '/api/cards/generate':
            card = generate_daily_card()
            self.send_json(card, 201)
            return

        # 从文本中提取朋友并更新提及次数
        if path == '/api/friends/extract':
            text = data.get('text', '')
            context = data.get('context', '')
            # 简单的人名提取（实际应由AI完成）
            names = extract_names_from_text(text)
            for name in names:
                update_friend_mention(name, context)
            self.send_json({'extracted': names, 'status': 'ok'})
            return

        # 通用模块 POST（创建）
        for module_name, config in MODULES.items():
            if path == f'/api/{module_name}':
                items = load_module(module_name)
                data['id'] = gen_id(config['prefix'])
                data['createdAt'] = datetime.datetime.now().isoformat()
                data['updatedAt'] = datetime.datetime.now().isoformat()
                items.insert(0, data)
                save_module(module_name, items)
                self.send_json(data, 201)
                return

        self.send_json({'error': 'Not found'}, 404)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length else '{}'
        try:
            data = json.loads(body)
        except:
            data = {}

        # 通用模块 PUT（更新）
        for module_name in MODULES:
            if path.startswith(f'/api/{module_name}/'):
                item_id = path.split('/')[-1]
                items = load_module(module_name)
                for i, item in enumerate(items):
                    if item.get('id') == item_id:
                        data['updatedAt'] = datetime.datetime.now().isoformat()
                        items[i].update(data)
                        save_module(module_name, items)
                        self.send_json(items[i])
                        return
                self.send_json({'error': 'Not found'}, 404)
                return

        self.send_json({'error': 'Not found'}, 404)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # 通用模块 DELETE
        for module_name in MODULES:
            if path.startswith(f'/api/{module_name}/'):
                item_id = path.split('/')[-1]
                items = load_module(module_name)
                items = [item for item in items if item.get('id') != item_id]
                save_module(module_name, items)
                self.send_json({'status': 'ok'})
                return

        self.send_json({'error': 'Not found'}, 404)


def main():
    start_scheduler()
    server = http.server.HTTPServer(('0.0.0.0', PORT), Handler)
    print("=" * 50)
    print("OneDay / 一日 后端已启动")
    print(f"端口: {PORT}")
    print(f"目录: {BASE_DIR}")
    print(f"访问: http://localhost:{PORT}")
    print("定时任务: 已启动（早间问候/晚间提示/运动提醒）")
    print("=" * 50)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
        server.server_close()

if __name__ == '__main__':
    main()
