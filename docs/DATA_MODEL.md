# Zames CRM · 数据模型

> 所有数据存储在 localStorage，key 为 `zams-crm-data`。数据结构为 JSON 对象，包含 customers、projects、activities、settings 四个集合。

---

## 1. 客户 Customer

```json
{
  "id": "c_001",
  "name": "张伟",
  "company": "明远科技",
  "title": "采购总监",
  "phone": "138-0000-0001",
  "email": "zhangwei@mingyuan.com",
  "source": "朋友推荐",
  "status": "following",
  "need": "企业级 SaaS 订阅，需支持多部门协作",
  "budget": "500000",
  "address": "",
  "notes": "",
  "createdAt": "2026-08-15T10:00:00+08:00",
  "updatedAt": "2026-08-30T10:15:00+08:00"
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | string | 是 | 唯一标识，格式 `c_xxx` |
| name | string | 是 | 联系人姓名 |
| company | string | 是 | 公司名称 |
| title | string | 否 | 职位 |
| phone | string | 否 | 电话 |
| email | string | 否 | 邮箱 |
| source | string | 否 | 客户来源（朋友推荐/线上咨询/展会/冷呼/其他） |
| status | string | 是 | 状态：`lead`(线索) / `following`(跟进中) / `won`(已成交) / `lost`(已流失) |
| need | string | 否 | 需求描述 |
| budget | string | 否 | 预算（数字字符串，单位元） |
| address | string | 否 | 地址 |
| notes | string | 否 | 备注 |
| createdAt | string | 是 | 创建时间 ISO 8601 |
| updatedAt | string | 是 | 更新时间 ISO 8601 |

---

## 2. 项目 Project

```json
{
  "id": "p_001",
  "name": "明远科技 SaaS 订阅",
  "customerId": "c_001",
  "stage": "proposal",
  "priority": "high",
  "amount": "500000",
  "deadline": "2026-09-05",
  "progress": 65,
  "description": "企业级 SaaS 年度订阅，含 50 个账号",
  "milestones": [
    { "id": "m1", "title": "需求确认", "done": true, "date": "2026-08-20" },
    { "id": "m2", "title": "方案报价", "done": true, "date": "2026-08-28" },
    { "id": "m3", "title": "合同谈判", "done": false, "date": "" },
    { "id": "m4", "title": "签约", "done": false, "date": "" }
  ],
  "nextAction": "致电确认报价细节",
  "createdAt": "2026-08-15T10:00:00+08:00",
  "updatedAt": "2026-08-30T10:15:00+08:00"
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | string | 是 | 唯一标识，格式 `p_xxx` |
| name | string | 是 | 项目名称 |
| customerId | string | 是 | 关联客户 ID |
| stage | string | 是 | 销售阶段：`lead`(线索) / `following`(跟进中) / `proposal`(提案谈判) / `won`(已成交) / `lost`(已流失) |
| priority | string | 是 | 优先级：`high` / `medium` / `low` |
| amount | string | 否 | 金额（数字字符串，单位元） |
| deadline | string | 否 | 截止日期 YYYY-MM-DD |
| progress | number | 是 | 进度百分比 0-100 |
| description | string | 否 | 项目描述 |
| milestones | array | 否 | 里程碑列表 |
| nextAction | string | 否 | 下一步行动 |
| createdAt | string | 是 | 创建时间 |
| updatedAt | string | 是 | 更新时间 |

### 里程碑 Milestone

| 字段 | 类型 | 说明 |
|---|---|---|
| id | string | 唯一标识 |
| title | string | 里程碑标题 |
| done | boolean | 是否完成 |
| date | string | 完成日期，未完成为空字符串 |

---

## 3. 沟通记录 Activity

```json
{
  "id": "a_001",
  "customerId": "c_001",
  "projectId": "p_001",
  "type": "phone",
  "content": "致电张伟，确认方案报价细节，客户对价格基本认可，希望增加 10 个账号",
  "date": "2026-08-30T10:15:00+08:00",
  "createdAt": "2026-08-30T10:16:00+08:00"
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| id | string | 是 | 唯一标识，格式 `a_xxx` |
| customerId | string | 是 | 关联客户 ID |
| projectId | string | 否 | 关联项目 ID（可为空） |
| type | string | 是 | 类型：`phone`(电话) / `email`(邮件) / `meeting`(会议) / `wechat`(微信) / `other`(其他) |
| content | string | 是 | 沟通内容 |
| date | string | 是 | 沟通时间 ISO 8601 |
| createdAt | string | 是 | 记录创建时间 |

---

## 4. 设置 Settings

```json
{
  "stages": [
    { "id": "s1", "label": "线索", "value": "lead", "order": 1 },
    { "id": "s2", "label": "跟进中", "value": "following", "order": 2 },
    { "id": "s3", "label": "提案谈判", "value": "proposal", "order": 3 },
    { "id": "s4", "label": "已成交", "value": "won", "order": 4 },
    { "id": "s5", "label": "已流失", "value": "lost", "order": 5 }
  ],
  "priorities": [
    { "label": "高", "value": "high" },
    { "label": "中", "value": "medium" },
    { "label": "低", "value": "low" }
  ],
  "activityTypes": [
    { "label": "电话", "value": "phone" },
    { "label": "邮件", "value": "email" },
    { "label": "会议", "value": "meeting" },
    { "label": "微信", "value": "wechat" },
    { "label": "其他", "value": "other" }
  ],
  "sources": ["朋友推荐", "线上咨询", "展会", "冷呼", "其他"]
}
```

---

## 5. 完整数据结构

```json
{
  "customers": [ ... ],
  "projects": [ ... ],
  "activities": [ ... ],
  "settings": { ... },
  "meta": {
    "version": "1.0",
    "lastExport": null
  }
}
```

---

## 6. 关联关系

```
Customer (1) ────< Project (N)      一个客户有多个项目
Customer (1) ────< Activity (N)     一个客户有多条沟通记录
Project (1) ────< Activity (N)      一个项目有多条沟通记录（可选）
Project (N) >──── Customer (1)      每个项目属于一个客户
```

---

## 7. ID 生成规则

- 客户：`c_` + 时间戳后 6 位 + 随机 2 位，如 `c_123456ab`
- 项目：`p_` + 同上
- 沟通记录：`a_` + 同上
- 里程碑：`m_` + 同上

---

## 8. 示例数据规模

- 客户：12 个（4 线索 / 5 跟进中 / 2 已成交 / 1 已流失）
- 项目：8 个（分布在各阶段）
- 沟通记录：25 条（覆盖各类型）
