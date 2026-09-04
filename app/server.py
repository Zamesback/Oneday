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
    
    todos_today = [t for t in todos if t.get('date', '').startswith(today) or True]
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
   - 待办事项（todos）：用户说要做什么、需要做什么、记得做什么
   - 重要事件/项目（projects）：用户提到的正在跟进的项目、目标、事件
   - 灵感（inspirations）：用户突然想到的想法、创意、点子
   - 朋友/人物（friends）：用户提到的人名、身份、关系
   - 运动（exercise）：用户提到运动、跑步、健身等
   - 情绪状态（mood）：用户当前的心情状态
3. **主动关心**：在合适的时候提醒用户、鼓励用户、给出建议

## 输出格式（严格遵守 JSON 格式）
你必须返回一个 JSON 对象，包含以下字段：
{
  "reply": "你对用户说的话，自然温暖的回应",
  "extracted": {
    "todos": ["待办1", "待办2"],
    "projects": [{"name": "项目名", "stage": "跟进中", "notes": "备注"}],
    "inspirations": ["灵感1", "灵感2"],
    "friends": [{"name": "人名", "identity": "身份", "relationship": "关系"}],
    "exercise": {"status": "done/mentioned/none", "detail": "运动详情"},
    "mood": "happy/neutral/tired/angry/sad"
  },
  "suggestion": "可选的建议或提醒，没有就空字符串"
}

## 重要规则
- 只返回 JSON，不要返回其他任何文字
- reply 要自然，不要说"我帮你记了..."这种机械的话，而是自然地回应
- 提取信息要准确，不要过度提取，不要把闲聊内容当成待办
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

def save_extracted_info(extracted):
    """把 AI 提取的信息保存到对应模块"""
    saved = {'todos': 0, 'projects': 0, 'inspirations': 0, 'friends': 0, 'exercise': 0}
    
    # 保存待办
    if extracted.get('todos'):
        todos = load_module('todos')
        for todo_text in extracted['todos']:
            if todo_text and len(todo_text) > 1:
                todos.insert(0, {
                    'id': gen_id('todo'),
                    'title': todo_text,
                    'priority': 'medium',
                    'status': 'pending',
                    'source': 'ai_extract',
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
    
    # 尝试调用真实 AI
    ai_result = call_real_ai(AI_AGENT_SYSTEM_PROMPT, user_prompt)
    
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

# ===== 晨间/晚间 AI 生成 =====

def generate_morning_greeting_ai():
    """用 AI 生成早间问候（更个性化）"""
    settings = load_settings()
    name = settings.get('userName', '')
    
    # 尝试真实 AI
    if settings.get('apiKey') and settings.get('apiProvider') != 'mock':
        try:
            todos = load_module('todos')
            pending = [t for t in todos if t.get('status') != 'done'][-5:]
            projects = load_module('projects')
            active = [p for p in projects if p.get('status') not in ('done', 'cancelled')][-3:]
            
            context = f"""用户称呼：{name}
今天有 {len(pending)} 个待办，{len(active)} 个进行中的项目。
待办：{', '.join([t.get('title','') for t in pending]) if pending else '无'}
项目：{', '.join([p.get('name','') for p in active]) if active else '无'}"""
            
            prompt = f"""你是 OneDay，用户的 AI 生活伙伴。现在是早上，请给用户生成一段温暖、个性化的早间问候。

{context}

要求：
1. 称呼用户的名字
2. 提到今天的待办或项目（自然地带过，不要罗列）
3. 语气温暖、鼓励、有活力
4. 100字以内
5. 只返回问候文字，不要其他内容"""
            
            result = call_real_ai("你是 OneDay，温暖的 AI 生活伙伴。", prompt)
            if result and isinstance(result, str):
                return result
            elif result and isinstance(result, dict) and result.get('reply'):
                return result['reply']
        except Exception as e:
            print(f"AI 早间问候生成失败: {e}")
    
    # 回退到模拟模式
    return generate_morning_greeting()

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
    """获取每日壁纸（静态渐变，预留 AI 生成接口）"""
    today = datetime.date.today().isoformat()
    # 基于日期选择固定的渐变，保证一天内不变
    day_index = datetime.date.today().toordinal() % len(WALLPAPER_GRADIENTS)
    return {
        'date': today,
        'type': 'gradient',
        'value': WALLPAPER_GRADIENTS[day_index],
        'quote': get_daily_quote(),
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
        if '/api/' in args[0]:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {args[0]}")

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
