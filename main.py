# BidHunter AI - Backend API
# FastAPI Application for Tender Intelligence System

import os
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from openai import OpenAI
import json
import hashlib

# ============== Configuration ==============
app = FastAPI(title="BidHunter AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://ozheqyidddqhiyojhwxn.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable_cWyTGJaBPQhjh7VvB6uihQ_Y4T_XYqH")
# OpenAI API Key - User provided
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-cp-xoOohBvMkZhv_u0y57fmJbWB8-rMmqMpz02GM-1La_ogR7rZnG5ZxijVAN8gxiKw0DlX55a7FAbZ_aeCsMOZF1He1PQ_gNtr6sjL0lVV-P_1uLWDxADtAds")

# Initialize clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ============== Data Models ==============
class TenderCreate(BaseModel):
    source: str
    source_url: str
    title: str
    content: str
    publish_date: Optional[str] = None
    location: Optional[str] = None
    budget: Optional[float] = None

class TenderAnalyzeRequest(BaseModel):
    tender_id: str

class TenderSearchRequest(BaseModel):
    keyword: Optional[str] = None
    location: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    page: int = 1
    limit: int = 20

class UserProfileCreate(BaseModel):
    email: str
    company_name: str
    industry: Optional[str] = None
    location: Optional[str] = None
    registered_capital: Optional[float] = None
    keywords: Optional[List[str]] = None

# ============== AI Analysis Functions ==============
async def analyze_tender_with_ai(title: str, content: str) -> Dict[str, Any]:
    """
    使用GPT分析招标公告，提取关键信息
    """
    if not OPENAI_API_KEY:
        return {
            "summary": f"这是一个关于{title}的项目招标。",
            "requirements": ["相关资质要求", "注册资本要求", "业绩要求"],
            "risk_analysis": "暂无风险分析",
            "budget": None,
            "deadline": None,
        }

    prompt = f"""
    请分析以下招标公告，提取关键信息：

    标题：{title}

    内容：{content[:2000]}

    请以JSON格式返回以下字段：
    1. summary: 2-3句话的项目摘要
    2. requirements: 资质要求列表（数组）
    3. risk_analysis: 风险分析（1句话）
    4. budget: 预算金额（如果未提及请返回null）
    5. deadline: 截止日期（如果未提及请返回null）
    """

    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个专业的招标分析助手，擅长提取关键信息。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )

        result_text = response.choices[0].message.content
        # 尝试解析JSON
        try:
            result = json.loads(result_text)
            return result
        except:
            return {
                "summary": result_text[:200],
                "requirements": [],
                "risk_analysis": "解析失败",
                "budget": None,
                "deadline": None,
            }
    except Exception as e:
        print(f"AI分析错误: {e}")
        return {
            "summary": "AI分析暂时不可用",
            "requirements": [],
            "risk_analysis": "分析失败",
            "budget": None,
            "deadline": None,
        }

def calculate_match_score(tender: Dict, user_profile: Dict) -> int:
    """
    计算招标与用户档案的匹配度
    """
    score = 0
    factors = 0

    # 关键词匹配
    if user_profile.get("keywords"):
        keywords = user_profile["keywords"]
        title = tender.get("title", "")
        summary = tender.get("summary", "")
        text = f"{title} {summary}"

        keyword_matches = sum(1 for kw in keywords if kw in text)
        if keywords:
            score += (keyword_matches / len(keywords)) * 40
            factors += 40

    # 预算范围匹配
    budget = tender.get("budget")
    if budget:
        budget_min = user_profile.get("budget_min", 0)
        budget_max = user_profile.get("budget_max", float("inf"))
        if budget_min <= budget <= budget_max:
            score += 30
        factors += 30

    # 地区匹配
    tender_location = tender.get("location", "")
    user_location = user_profile.get("location", "")
    if user_location and tender_location:
        if user_location in tender_location or tender_location in user_location:
            score += 30
        factors += 30

    return min(int(score), 100) if factors > 0 else 50

# ============== API Routes ==============

@app.get("/")
async def root():
    return {"message": "BidHunter AI API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ============== Tender APIs ==============

@app.post("/api/tenders")
async def create_tender(tender: TenderCreate, background_tasks: BackgroundTasks):
    """创建新的招标记录"""
    data = {
        "source": tender.source,
        "source_url": tender.source_url,
        "title": tender.title,
        "content": tender.content,
        "publish_date": tender.publish_date or datetime.now().strftime("%Y-%m-%d"),
        "location": tender.location,
        "budget": tender.budget,
    }

    result = supabase.table("tenders").insert(data).execute()

    if result.error:
        raise HTTPException(status_code=500, detail=result.error.message)

    return {"success": True, "data": result.data}

@app.get("/api/tenders")
async def search_tenders(
    keyword: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    budget_min: Optional[float] = Query(None),
    budget_max: Optional[float] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """搜索招标信息"""
    offset = (page - 1) * limit

    query = supabase.table("tenders").select("*", count="exact")

    if keyword:
        query = query.ilike("title", f"%{keyword}%")

    if location:
        query = query.eq("location", location)

    if budget_min:
        query = query.gte("budget", budget_min)

    if budget_max:
        query = query.lte("budget", budget_max)

    result = query.order("publish_date", desc=True).range(offset, offset + limit - 1).execute()

    return {
        "success": True,
        "data": result.data,
        "total": result.count,
        "page": page,
        "limit": limit
    }

@app.get("/api/tenders/{tender_id}")
async def get_tender(tender_id: str):
    """获取招标详情"""
    result = supabase.table("tenders").select("*").eq("id", tender_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="招标信息不存在")

    return {"success": True, "data": result.data[0]}

@app.post("/api/tenders/{tender_id}/analyze")
async def analyze_tender(tender_id: str, background_tasks: BackgroundTasks):
    """使用AI分析招标公告"""
    # 获取招标信息
    result = supabase.table("tenders").select("*").eq("id", tender_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="招标信息不存在")

    tender = result.data[0]

    # 使用AI分析
    analysis = await analyze_tender_with_ai(tender["title"], tender["content"])

    # 更新招标记录
    update_data = {
        "summary": analysis.get("summary"),
        "requirements": json.dumps(analysis.get("requirements", [])),
        "risk_analysis": analysis.get("risk_analysis"),
    }

    if analysis.get("budget"):
        update_data["budget"] = analysis["budget"]

    supabase.table("tenders").update(update_data).eq("id", tender_id).execute()

    return {"success": True, "analysis": analysis}

@app.get("/api/tenders/recommended")
async def get_recommended_tenders(
    user_id: str = Query(...),
    limit: int = Query(10, ge=1, le=50)
):
    """获取推荐招标（基于用户档案）"""
    # 获取用户档案
    profile_result = supabase.table("company_profiles").select("*").eq("user_id", user_id).execute()

    if not profile_result.data:
        # 如果没有档案，返回最新招标
        result = supabase.table("tenders").select("*").order("publish_date", desc=True).limit(limit).execute()
        return {"success": True, "data": result.data, "reason": "no_profile"}

    profile = profile_result.data[0]

    # 获取所有招标并计算匹配度
    tenders_result = supabase.table("tenders").select("*").order("publish_date", desc=True).limit(200).execute()

    # 计算匹配度并排序
    scored_tenders = []
    for tender in tenders_result.data:
        score = calculate_match_score(tender, profile)
        tender["match_score"] = score
        scored_tenders.append(tender)

    # 按匹配度排序
    scored_tenders.sort(key=lambda x: x.get("match_score", 0), reverse=True)

    return {
        "success": True,
        "data": scored_tenders[:limit],
        "profile": profile
    }

# ============== User APIs ==============

@app.post("/api/users")
async def create_user(profile: UserProfileCreate):
    """创建用户"""
    # 检查邮箱是否已存在
    existing = supabase.table("users").select("id").eq("email", profile.email).execute()

    if existing.data:
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    # 创建用户
    user_data = {
        "email": profile.email,
        "company_name": profile.company_name,
    }

    result = supabase.table("users").insert(user_data).execute()

    if result.error:
        raise HTTPException(status_code=500, detail=result.error.message)

    user_id = result.data[0]["id"]

    # 创建用户档案
    profile_data = {
        "user_id": user_id,
        "industry": profile.industry,
        "location": profile.location,
        "registered_capital": profile.registered_capital,
        "keywords": profile.keywords or [],
    }

    supabase.table("company_profiles").insert(profile_data).execute()

    return {"success": True, "user_id": user_id}

@app.get("/api/users/{user_id}/profile")
async def get_user_profile(user_id: str):
    """获取用户档案"""
    result = supabase.table("company_profiles").select("*").eq("user_id", user_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="用户档案不存在")

    return {"success": True, "data": result.data[0]}

@app.put("/api/users/{user_id}/profile")
async def update_user_profile(user_id: str, profile: Dict):
    """更新用户档案"""
    profile["updated_at"] = datetime.now().isoformat()

    result = supabase.table("company_profiles").update(profile).eq("user_id", user_id).execute()

    if result.error:
        raise HTTPException(status_code=500, detail=result.error.message)

    return {"success": True, "data": result.data}

# ============== Tracking APIs ==============

@app.post("/api/tracking")
async def track_tender(user_id: str, tender_id: str):
    """跟踪招标项目"""
    data = {
        "user_id": user_id,
        "tender_id": tender_id,
        "status": "tracked",
        "created_at": datetime.now().isoformat()
    }

    result = supabase.table("user_tender_tracking").upsert(data).execute()

    if result.error:
        raise HTTPException(status_code=500, detail=result.error.message)

    return {"success": True}

@app.get("/api/tracking/{user_id}")
async def get_tracked_tenders(user_id: str):
    """获取用户跟踪的招标"""
    result = supabase.table("user_tender_tracking").select(
        "*, tenders(*)"
    ).eq("user_id", user_id).execute()

    return {"success": True, "data": result.data}

@app.delete("/api/tracking/{tracking_id}")
async def untrack_tender(tracking_id: str):
    """取消跟踪"""
    result = supabase.table("user_tender_tracking").delete().eq("id", tracking_id).execute()

    if result.error:
        raise HTTPException(status_code=500, detail=result.error.message)

    return {"success": True}

# ============== Statistics APIs ==============

@app.get("/api/stats/dashboard")
async def get_dashboard_stats(user_id: str = Query(...)):
    """获取仪表盘统计数据"""

    # 今日新机会
    today = datetime.now().strftime("%Y-%m-%d")
    today_result = supabase.table("tenders").select("id", count="exact").eq("publish_date", today).execute()
    today_count = today_result.count or 0

    # 即将截止（7天内）
    week_later = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    closing_result = supabase.table("tenders").select("id", count="exact").lte("deadline", week_later).execute()
    closing_count = closing_result.count or 0

    # 高匹配机会
    profile_result = supabase.table("company_profiles").select("*").eq("user_id", user_id).execute()
    high_match_count = 0

    if profile_result.data:
        profile = profile_result.data[0]
        tenders_result = supabase.table("tenders").select("*").order("publish_date", desc=True).limit(100).execute()

        for tender in tenders_result.data:
            score = calculate_match_score(tender, profile)
            if score >= 80:
                high_match_count += 1

    # 我的跟踪
    tracked_result = supabase.table("user_tender_tracking").select("id", count="exact").eq("user_id", user_id).execute()
    tracked_count = tracked_result.count or 0

    return {
        "success": True,
        "data": {
            "today_new": today_count,
            "closing_soon": closing_count,
            "high_match": high_match_count,
            "tracked": tracked_count
        }
    }

# ============== Data Source APIs ==============

@app.get("/api/sources")
async def get_data_sources():
    """获取数据源列表"""
    sources = [
        {"id": "gov", "name": "政府采购网", "url": "http://www.ccgp.gov.cn", "type": "government"},
        {"id": "ggzy", "name": "公共资源交易中心", "url": "http://www.ggzy.gov.cn", "type": "government"},
        {"id": "bidcenter", "name": "千里马招标网", "url": "http://www.qianlima.com", "type": "commercial"},
        {"id": "chinabidding", "name": "中国采购与招标网", "url": "http://www.chinabidding.com", "type": "commercial"},
    ]
    return {"success": True, "data": sources}

# ============== Webhook for external triggers ==============

@app.post("/api/webhook/crawl")
async def trigger_crawl(background_tasks: BackgroundTasks):
    """触发数据采集任务"""
    return {"success": True, "message": "采集任务已触发"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
