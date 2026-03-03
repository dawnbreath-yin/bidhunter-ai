-- BidHunter AI Database Schema
-- Run this SQL in Supabase SQL Editor to set up the database

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    company_name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Company profiles table
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

-- Tenders table
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

-- User tender tracking table
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

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_tenders_publish_date ON tenders(publish_date DESC);
CREATE INDEX IF NOT EXISTS idx_tenders_location ON tenders(location);
CREATE INDEX IF NOT EXISTS idx_tenders_budget ON tenders(budget);
CREATE INDEX IF NOT EXISTS idx_tenders_title ON tenders(title);
CREATE INDEX IF NOT EXISTS idx_company_profiles_user_id ON company_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_tender_tracking_user_id ON user_tender_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_user_tender_tracking_tender_id ON user_tender_tracking(tender_id);

-- Enable Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE company_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenders ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_tender_tracking ENABLE ROW LEVEL SECURITY;

-- RLS Policies
-- Users can read their own data
CREATE POLICY "Users can read own data" ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can insert own data" ON users FOR INSERT WITH CHECK (auth.uid() = id);
CREATE POLICY "Users can update own data" ON users FOR UPDATE USING (auth.uid() = id);

-- Company profiles - users can manage their own
CREATE POLICY "Users can manage own profile" ON company_profiles FOR ALL USING (auth.uid() = user_id);

-- Tenders - public read, admin write
CREATE POLICY "Tenders are viewable by everyone" ON tenders FOR SELECT USING (true);
CREATE POLICY "Service role can manage tenders" ON tenders FOR ALL USING (auth.role() = 'service_role');

-- Tracking - users can manage their own
CREATE POLICY "Users can manage own tracking" ON user_tender_tracking FOR ALL USING (auth.uid() = user_id);

-- Insert sample tender data for testing
INSERT INTO tenders (source, source_url, title, content, publish_date, location, budget, category) VALUES
('政府采购网', 'http://www.ccgp.gov.cn', '某市政府信息化系统升级改造项目', '本项目主要内容包括：政务服务平台升级、数据共享交换平台建设、智慧城市运营指挥中心建设等。要求投标人具有相关资质证书。', '2024-01-15', '江苏·南京', 5800000, '信息化'),
('公共资源交易中心', 'http://www.ggzy.gov.cn', '某大学智慧校园建设项目', '建设智慧校园，包括：校园网络全覆盖、智慧教室建设、图书管理系统升级、一卡通系统建设等。', '2024-01-14', '浙江·杭州', 3200000, '教育'),
('招标网', 'http://www.zhaobiao.cn', '某医院HIS系统升级项目', '医院信息管理系统升级，包括：电子病历系统、药品管理系统、挂号收费系统、财务管理系统等。', '2024-01-13', '上海', 4500000, '医疗'),
('政府采购网', 'http://www.ccgp.gov.cn', '某区智慧交通管理系统项目', '建设智慧交通管理系统，包括：交通信号控制、交通诱导发布、停车管理系统、视频监控等。', '2024-01-12', '广东·广州', 2800000, '交通'),
('公共资源交易中心', 'http://www.ggzy.gov.cn', '某企业展厅智能化项目', '企业展厅智能化建设，包括：多媒体展示系统、互动体验系统、智能化控制系统、导览系统等。', '2024-01-11', '北京', 1500000, '企业服务'),
('招标网', 'http://www.zhaobiao.cn', '某园区智慧安防项目', '智慧园区安防系统建设，包括：视频监控系统、门禁系统、报警系统、巡更系统等。', '2024-01-10', '四川·成都', 2200000, '安防'),
('政府采购网', 'http://www.ccgp.gov.cn', '某县乡村振兴数字化项目', '乡村振兴数字化建设，包括：农村电商平台、农产品溯源系统、乡村旅游推广平台等。', '2024-01-09', '山东·济南', 3800000, '农业'),
('中国采购与招标网', 'http://www.chinabidding.com', '某制造企业ERP系统实施项目', 'ERP系统实施，包括：生产管理模块、财务管理模块、供应链管理模块、客户关系管理模块等。', '2024-01-08', '江苏·苏州', 6500000, '企业服务');
