#!/usr/bin/env python3
"""
BidHunter AI - Database Initialization Script
Run this script to initialize the Supabase database schema
"""

import os
import sys

# Install dependencies
os.system("pip install supabase psycopg2-binary -q")

from supabase import create_client
import json

# Configuration
SUPABASE_URL = "https://ozheqyidddqhiyojhwxn.supabase.co"
# Use service role key for admin operations (get from Supabase dashboard -> Settings -> API)
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

def init_database():
    if not SUPABASE_SERVICE_KEY:
        print("Error: Please set SUPABASE_SERVICE_KEY environment variable")
        print("Get it from: Supabase Dashboard -> Settings -> API -> service_role")
        sys.exit(1)

    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    # Sample tender data
    tenders_data = [
        {
            "source": "政府采购网",
            "source_url": "http://www.ccgp.gov.cn",
            "title": "某市政府信息化系统升级改造项目",
            "content": "本项目主要内容包括：政务服务平台升级、数据共享交换平台建设、智慧城市运营指挥中心建设等。要求投标人具有相关资质证书。",
            "publish_date": "2024-01-15",
            "location": "江苏·南京",
            "budget": 5800000,
            "category": "信息化",
            "deadline": "2024-02-01",
            "status": "active"
        },
        {
            "source": "公共资源交易中心",
            "source_url": "http://www.ggzy.gov.cn",
            "title": "某大学智慧校园建设项目",
            "content": "建设智慧校园，包括：校园网络全覆盖、智慧教室建设、图书管理系统升级、一卡通系统建设等。",
            "publish_date": "2024-01-14",
            "location": "浙江·杭州",
            "budget": 3200000,
            "category": "教育",
            "deadline": "2024-02-05",
            "status": "active"
        },
        {
            "source": "招标网",
            "source_url": "http://www.zhaobiao.cn",
            "title": "某医院HIS系统升级项目",
            "content": "医院信息管理系统升级，包括：电子病历系统、药品管理系统、挂号收费系统、财务管理系统等。",
            "publish_date": "2024-01-13",
            "location": "上海",
            "budget": 4500000,
            "category": "医疗",
            "deadline": "2024-02-10",
            "status": "active"
        },
        {
            "source": "政府采购网",
            "source_url": "http://www.ccgp.gov.cn",
            "title": "某区智慧交通管理系统项目",
            "content": "建设智慧交通管理系统，包括：交通信号控制、交通诱导发布、停车管理系统、视频监控等。",
            "publish_date": "2024-01-12",
            "location": "广东·广州",
            "budget": 2800000,
            "category": "交通",
            "deadline": "2024-02-08",
            "status": "active"
        },
        {
            "source": "公共资源交易中心",
            "source_url": "http://www.ggzy.gov.cn",
            "title": "某企业展厅智能化项目",
            "content": "企业展厅智能化建设，包括：多媒体展示系统、互动体验系统、智能化控制系统、导览系统等。",
            "publish_date": "2024-01-11",
            "location": "北京",
            "budget": 1500000,
            "category": "企业服务",
            "deadline": "2024-02-15",
            "status": "active"
        },
        {
            "source": "招标网",
            "source_url": "http://www.zhaobiao.cn",
            "title": "某园区智慧安防项目",
            "content": "智慧园区安防系统建设，包括：视频监控系统、门禁系统、报警系统、巡更系统等。",
            "publish_date": "2024-01-10",
            "location": "四川·成都",
            "budget": 2200000,
            "category": "安防",
            "deadline": "2024-02-12",
            "status": "active"
        },
        {
            "source": "政府采购网",
            "source_url": "http://www.ccgp.gov.cn",
            "title": "某县乡村振兴数字化项目",
            "content": "乡村振兴数字化建设，包括：农村电商平台、农产品溯源系统、乡村旅游推广平台等。",
            "publish_date": "2024-01-09",
            "location": "山东·济南",
            "budget": 3800000,
            "category": "农业",
            "deadline": "2024-02-20",
            "status": "active"
        },
        {
            "source": "中国采购与招标网",
            "source_url": "http://www.chinabidding.com",
            "title": "某制造企业ERP系统实施项目",
            "content": "ERP系统实施，包括：生产管理模块、财务管理模块、供应链管理模块、客户关系管理模块等。",
            "publish_date": "2024-01-08",
            "location": "江苏·苏州",
            "budget": 6500000,
            "category": "企业服务",
            "deadline": "2024-02-18",
            "status": "active"
        },
    ]

    print("Inserting sample tender data...")

    for tender in tenders_data:
        try:
            result = supabase.table("tenders").insert(tender).execute()
            print(f"  ✓ Inserted: {tender['title'][:30]}...")
        except Exception as e:
            print(f"  ✗ Error inserting {tender['title'][:30]}: {str(e)[:50]}")

    print("\n✅ Database initialized successfully!")
    print(f"   Total tenders: {len(tenders_data)}")

if __name__ == "__main__":
    print("=" * 50)
    print("BidHunter AI - Database Initialization")
    print("=" * 50)
    init_database()
