# BidHunter AI - 部署指南

## 概述

本文档提供 BidHunter AI 完整的后端部署指南，包括数据库初始化、后端部署、数据爬虫配置和 AI 服务集成。

## 快速开始

### 步骤 1: 数据库初始化

在 Supabase Dashboard 中执行以下 SQL：

```sql
-- 启用 UUID 扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    company_name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 企业档案表
CREATE TABLE IF NOT EXISTS company_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    industry TEXT,
    location TEXT,
    registered_capital REAL,
    keywords TEXT[] DEFAULT '{}',
    budget_min REAL DEFAULT 0,
    budget_max REAL DEFAULT 100000000,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 招标信息表
CREATE TABLE IF NOT EXISTS tenders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source TEXT NOT NULL,
    source_url TEXT,
    title TEXT NOT NULL,
    content TEXT,
    summary TEXT,
    requirements TEXT,
    risk_analysis TEXT,
    publish_date DATE,
    deadline DATE,
    location TEXT,
    budget REAL,
    category TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 用户跟踪表
CREATE TABLE IF NOT EXISTS user_tender_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    tender_id UUID REFERENCES tenders(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'tracked',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, tender_id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_tenders_publish_date ON tenders(publish_date DESC);
CREATE INDEX IF NOT EXISTS idx_tenders_location ON tenders(location);
CREATE INDEX IF NOT EXISTS idx_tenders_budget ON tenders(budget);
CREATE INDEX IF NOT EXISTS idx_tenders_title ON tenders(title);
CREATE INDEX IF NOT EXISTS idx_company_profiles_user_id ON company_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_tender_tracking_user_id ON user_tender_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_user_tender_tracking_tender_id ON user_tender_tracking(tender_id);

-- 插入示例数据
INSERT INTO tenders (source, source_url, title, content, publish_date, location, budget, category, deadline, status) VALUES
('政府采购网', 'http://www.ccgp.gov.cn', '某市政府信息化系统升级改造项目', '本项目主要内容包括：政务服务平台升级、数据共享交换平台建设、智慧城市运营指挥中心建设等。要求投标人具有相关资质证书。', '2024-01-15', '江苏·南京', 5800000, '信息化', '2024-02-01', 'active'),
('公共资源交易中心', 'http://www.ggzy.gov.cn', '某大学智慧校园建设项目', '建设智慧校园，包括：校园网络全覆盖、智慧教室建设、图书管理系统升级、一卡通系统建设等。', '2024-01-14', '浙江·杭州', 3200000, '教育', '2024-02-05', 'active'),
('招标网', 'http://www.zhaobiao.cn', '某医院HIS系统升级项目', '医院信息管理系统升级，包括：电子病历系统、药品管理系统、挂号收费系统、财务管理系统等。', '2024-01-13', '上海', 4500000, '医疗', '2024-02-10', 'active'),
('政府采购网', 'http://www.ccgp.gov.cn', '某区智慧交通管理系统项目', '建设智慧交通管理系统，包括：交通信号控制、交通诱导发布、停车管理系统、视频监控等。', '2024-01-12', '广东·广州', 2800000, '交通', '2024-02-08', 'active'),
('公共资源交易中心', 'http://www.ggzy.gov.cn', '某企业展厅智能化项目', '企业展厅智能化建设，包括：多媒体展示系统、互动体验系统、智能化控制系统、导览系统等。', '2024-01-11', '北京', 1500000, '企业服务', '2024-02-15', 'active'),
('招标网', 'http://www.zhaobiao.cn', '某园区智慧安防项目', '智慧园区安防系统建设，包括：视频监控系统、门禁系统、报警系统、巡更系统等。', '2024-01-10', '四川·成都', 2200000, '安防', '2024-02-12', 'active'),
('政府采购网', 'http://www.ccgp.gov.cn', '某县乡村振兴数字化项目', '乡村振兴数字化建设，包括：农村电商平台、农产品溯源系统、乡村旅游推广平台等。', '2024-01-09', '山东·济南', 3800000, '农业', '2024-02-20', 'active'),
('中国采购与招标网', 'http://www.chinabidding.com', '某制造企业ERP系统实施项目', 'ERP系统实施，包括：生产管理模块、财务管理模块、供应链管理模块、客户关系管理模块等。', '2024-01-08', '江苏·苏州', 6500000, '企业服务', '2024-02-18', 'active');
```

### 步骤 2: 部署后端

#### 方案 A: Railway 部署（推荐）

1. 注册 [Railway.app](https://railway.app/)
2. 创建新项目，选择 "Deploy from GitHub repo"
3. 连接 GitHub 仓库
4. 添加环境变量：
   - `SUPABASE_URL`: `https://ozheqyidddqhiyojhwxn.supabase.co`
   - `SUPABASE_KEY`: `sb_publishable_cWyTGJaBPQhjh7VvB6uihQ_Y4T_XYqH`
   - `OPENAI_API_KEY`: `sk-cp-xoOohBvMkZhv_u0y57fmJbWB8-rMmqMpz02GM-1La_ogR7rZnG5ZxijVAN8gxiKw0DlX55a7FAbZ_aeCsMOZF1He1PQ_gNtr6sjL0lVV-P_1uLWDxADtAds`
5. 部署会自动开始

#### 方案 B: Render 部署

1. 注册 [Render.com](https://render.com/)
2. 创建 new Web Service
3. 连接 GitHub 仓库
4. 设置：
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. 添加环境变量（同上）

#### 方案 C: 本地运行

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行
uvicorn main:app --reload
```

### 步骤 3: 数据爬虫配置

爬虫模块已包含在后端代码中，可以手动触发数据采集：

```python
# 在 main.py 中调用
from scraper import TenderScraper

# 触发爬虫
scraper = TenderScraper()
# 采集数据并存储到数据库
```

或者通过 API 触发：

```bash
curl -X POST "https://your-api-url/api/webhook/crawl"
```

### 步骤 4: AI 服务

AI 服务已集成到后端，使用您提供的 OpenAI API Key：

- **GPT-3.5 Turbo** 用于招标公告分析
- 自动提取关键信息：摘要、资质要求、风险分析、预算、截止日期
- 智能匹配度计算

## API 端点

部署后，API 端点如下：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | API 状态 |
| `/health` | GET | 健康检查 |
| `/api/tenders` | GET | 搜索招标信息 |
| `/api/tenders/{id}` | GET | 获取招标详情 |
| `/api/tenders/{id}/analyze` | POST | AI 分析招标 |
| `/api/tenders/recommended` | GET | 获取推荐招标 |
| `/api/users` | POST | 创建用户 |
| `/api/tracking` | POST | 跟踪招标 |
| `/api/stats/dashboard` | GET | 统计数据 |

## 测试 API

```bash
# 健康检查
curl https://your-api-url/health

# 获取招标列表
curl https://your-api-url/api/tenders

# AI 分析招标
curl -X POST https://your-api-url/api/tenders/{tender_id}/analyze
```

## 费用说明

- **Supabase**: 免费层足够初期使用
- **OpenAI**: 按调用次数计费，GPT-3.5 Turbo 价格约为 $0.002/1K tokens
- **Railway/Render**: 免费层可用，付费层 $5-20/月

## 获取帮助

如有问题，请联系：support@bidhunter.ai
