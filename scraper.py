# BidHunter AI - Tender Scraper Module
# 招标信息采集模块

import asyncio
import aiohttp
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from bs4 import BeautifulSoup
import re
import json

@dataclass
class TenderItem:
    """招标信息数据结构"""
    source: str
    source_url: str
    title: str
    publish_date: str
    deadline: Optional[str] = None
    budget: Optional[float] = None
    location: Optional[str] = None
    content: str = ""
    raw_data: Dict = field(default_factory=dict)

class TenderScraper:
    """招标信息采集器基类"""

    def __init__(self, source_name: str, base_url: str):
        self.source_name = source_name
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch(self, url: str) -> Optional[str]:
        """获取页面内容"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                return None
        except Exception as e:
            print(f"请求失败 {url}: {e}")
            return None

    async def get_list(self, page: int = 1) -> List[TenderItem]:
        """获取列表页（子类实现）"""
        raise NotImplementedError

    async def get_detail(self, url: str) -> TenderItem:
        """获取详情页（子类实现）"""
        raise NotImplementedError


class ChinaGovBidScraper(TenderScraper):
    """中国政府采购网采集器"""

    def __init__(self):
        super().__init__("政府采购网", "http://www.ccgp.gov.cn")

    async def get_list(self, page: int = 1) -> List[TenderItem]:
        """获取招标列表"""
        tenders = []
        url = f"http://www.ccgp.gov.cn/gxcg/{'zbgg' if page == 1 else f'zbgg/{page}'}/index.html"

        html = await self.fetch(url)
        if not html:
            return tenders

        soup = BeautifulSoup(html, 'html.parser')

        # 解析列表（示例解析，实际需根据网站结构调整）
        items = soup.select('.c_ul li') or soup.select('.news-list li')

        for item in items:
            try:
                link = item.select_one('a')
                if not link:
                    continue

                title = link.get_text(strip=True)
                href = link.get('href', '')
                if not href.startswith('http'):
                    href = f"http://www.ccgp.gov.cn{href}"

                # 提取日期
                date_text = item.select_one('.date') or item.select_one('span')
                publish_date = self._parse_date(date_text.get_text(strip=True) if date_text else '')

                tenders.append(TenderItem(
                    source=self.source_name,
                    source_url=href,
                    title=title,
                    publish_date=publish_date,
                    content=f"来源: {self.source_name}"
                ))
            except Exception as e:
                print(f"解析列表项失败: {e}")
                continue

        return tenders

    def _parse_date(self, date_str: str) -> str:
        """解析日期"""
        if not date_str:
            return datetime.now().strftime("%Y-%m-%d")

        # 处理中文日期格式
        patterns = [
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y-%m-%d'),
            (r'(\d{4})/(\d{1,2})/(\d{1,2})', '%Y/%m/%d'),
            (r'(\d{4})年(\d{1,2})月(\d{1,2})日', '%Y年%m月%d日'),
        ]

        for pattern, fmt in patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    if '年' in fmt:
                        return f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
                    return f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
                except:
                    pass

        return datetime.now().strftime("%Y-%m-%d")


class QianlimaScraper(TenderScraper):
    """千里马招标网采集器"""

    def __init__(self):
        super().__init__("千里马招标网", "http://www.qianlima.com")

    async def get_list(self, keyword: str = "", page: int = 1) -> List[TenderItem]:
        """获取招标列表"""
        tenders = []

        # 构建搜索URL
        if keyword:
            url = f"http://www.qianlima.com/search/?wd={keyword}&page={page}"
        else:
            url = f"http://www.qianlima.com/zbgg/index_{page}.html"

        html = await self.fetch(url)
        if not html:
            return tenders

        soup = BeautifulSoup(html, 'html.parser')

        # 解析列表
        items = soup.select('.result-list .result-item') or soup.select('.news-list li')

        for item in items:
            try:
                link = item.select_one('a')
                if not link:
                    continue

                title = link.get_text(strip=True)
                href = link.get('href', '')

                tenders.append(TenderItem(
                    source=self.source_name,
                    source_url=href,
                    title=title,
                    publish_date=datetime.now().strftime("%Y-%m-%d"),
                    content=f"来源: {self.source_name}"
                ))
            except Exception as e:
                print(f"解析失败: {e}")
                continue

        return tenders


class ZbcgScraper(TenderScraper):
    """公共资源交易中心采集器"""

    # 各省市公共资源交易中心URL
    REGIONAL_URLS = [
        ("http://ggzy.jiangsu.gov.cn", "江苏"),
        ("http://ggzy.zj.gov.cn", "浙江"),
        ("http://ggzy.sh.gov.cn", "上海"),
        ("http://ggzy.beijing.gov.cn", "北京"),
        ("http://ggzy.gd.gov.cn", "广东"),
    ]

    def __init__(self, region: str = "江苏"):
        self.region = region
        base_url = next((url for url, name in self.REGIONAL_URLS if name == region), self.REGIONAL_URLS[0][0])
        super().__init__(f"公共资源交易中心-{region}", base_url)

    async def get_list(self, category: str = "zfbcggg", page: int = 1) -> List[TenderItem]:
        """获取招标列表"""
        tenders = []

        # 根据不同网站结构调整URL
        url = f"{self.base_url}/jspcenter/jyxx/{category}/list.html"

        html = await self.fetch(url)
        if not html:
            return tenders

        soup = BeautifulSoup(html, 'html.parser')

        # 解析列表
        items = soup.select('.article-list li') or soup.select('.news-list li')

        for item in items:
            try:
                link = item.select_one('a')
                if not link:
                    continue

                title = link.get_text(strip=True)
                href = link.get('href', '')
                if not href.startswith('http'):
                    href = f"{self.base_url}{href}"

                tenders.append(TenderItem(
                    source=self.source_name,
                    source_url=href,
                    title=title,
                    publish_date=datetime.now().strftime("%Y-%m-%d"),
                    content=f"来源: {self.source_name}"
                ))
            except Exception as e:
                print(f"解析失败: {e}")
                continue

        return tenders


class MockScraper(TenderScraper):
    """模拟采集器 - 用于测试"""

    def __init__(self):
        super().__init__("测试数据", "http://test.com")

    async def get_list(self, page: int = 1) -> List[TenderItem]:
        """生成模拟数据"""
        tenders = []

        categories = [
            "信息化建设",
            "系统集成",
            "软件开发",
            "网络工程",
            "安防监控",
            "智慧城市",
            "数据中心",
            "云服务",
        ]

        locations = [
            "北京", "上海", "广东", "江苏", "浙江",
            "四川", "湖北", "湖南", "河南", "山东"
        ]

        # 生成20条模拟数据
        for i in range(20):
            category = categories[i % len(categories)]
            location = locations[i % len(locations)]
            budget = (i + 1) * 500000

            tenders.append(TenderItem(
                source="测试数据",
                source_url=f"http://test.com/tender/{i}",
                title=f"{location}{category}项目招标公告",
                publish_date=(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
                deadline=(datetime.now() + timedelta(days=30 - i)).strftime("%Y-%m-%d"),
                budget=budget,
                location=f"中国·{location}",
                content=f"""
                {location}{category}项目现面向社会公开招标。

                一、项目概况
                本项目旨在建设{category}系统，包括硬件采购、软件开发和系统集成等内容。

                二、投标资格要求
                1. 具有独立法人资格的企业；
                2. 具有相关{category}项目实施经验；
                3. 注册资本不低于500万元；
                4. 具有ISO9001质量管理体系认证。

                三、招标文件的获取
                时间：{datetime.now().strftime("%Y-%m-%d")}至{ (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")}
                地点：XXX

                四、投标截止时间
                {(datetime.now() + timedelta(days=30 - i)).strftime("%Y-%m-%d")} 10:00

                五、联系方式
                联系人：张老师
                电话：010-12345678
                """
            ))

        return tenders


class TenderCrawler:
    """招标信息爬虫管理器"""

    def __init__(self):
        self.scrapers: Dict[str, TenderScraper] = {}

    def register_scraper(self, name: str, scraper: TenderScraper):
        """注册采集器"""
        self.scrapers[name] = scraper

    async def crawl_all(self, sources: List[str] = None) -> List[TenderItem]:
        """采集所有数据源"""
        all_tenders = []

        if not sources:
            sources = list(self.scrapers.keys())

        for source in sources:
            if source in self.scrapers:
                scraper = self.scrapers[source]
                async with scraper:
                    try:
                        tenders = await scraper.get_list()
                        all_tenders.extend(tenders)
                        print(f"从 {source} 采集了 {len(tenders)} 条数据")
                    except Exception as e:
                        print(f"采集 {source} 失败: {e}")

        return all_tenders

    async def crawl_with_keywords(self, keywords: List[str]) -> List[TenderItem]:
        """根据关键词采集"""
        all_tenders = []

        for keyword in keywords:
            if "千里马" in self.scrapers:
                scraper = self.scrapers["千里马"]
                async with scraper:
                    try:
                        tenders = await scraper.get_list(keyword=keyword)
                        all_tenders.extend(tenders)
                    except Exception as e:
                        print(f"关键词 {keyword} 采集失败: {e}")

        return all_tenders


# ============== 数据处理工具函数 ==============

def extract_budget(text: str) -> Optional[float]:
    """从文本中提取预算金额"""
    if not text:
        return None

    # 匹配各种金额格式
    patterns = [
        r'预算[：:]\s*([\d,]+(?:\.\d+)?)\s*(?:万元|万|元)?',
        r'预算金额[：:]\s*([\d,]+(?:\.\d+)?)\s*(?:万元|万|元)?',
        r'采购预算[：:]\s*([\d,]+(?:\.\d+)?)\s*(?:万元|万|元)?',
        r'项目预算[：:]\s*([\d,]+(?:\.\d+)?)\s*(?:万元|万|元)?',
        r'预算控制价[：:]\s*([\d,]+(?:\.\d+)?)\s*(?:万元|万|元)?',
        r'(?:人民币|￥|¥)\s*([\d,]+(?:\.\d+)?)\s*(?:万元|万|元)?',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                amount = float(amount_str)
                # 单位转换
                if '万' in match.group(0):
                    amount *= 10000
                return amount
            except:
                pass

    return None


def extract_deadline(text: str) -> Optional[str]:
    """从文本中提取截止日期"""
    if not text:
        return None

    patterns = [
        r'截止[时分]?[：:]\s*(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})(?:\s*[日号])?(?:\s*(\d{1,2})[:时]?(\d{1,2})?)?',
        r'投标截止[时分]?[：:]\s*(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})',
        r'响应截止[时分]?[：:]\s*(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))
                return f"{year}-{month:02d}-{day:02d}"
            except:
                pass

    return None


def extract_location(text: str) -> Optional[str]:
    """从文本中提取地点"""
    if not text:
        return None

    # 匹配常见地点格式
    patterns = [
        r'地点[：:]\s*(.+?)(?:市|省|区|县)(?:\s*|$)',
        r'项目地点[：:]\s*(.+?)(?:\s*市|\s*省|\s*区|\s*县|$)',
        r'建设地点[：:]\s*(.+?)(?:\s*市|\s*省|\s*区|\s*县|$)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()

    return None


def extract_requirements(text: str) -> List[str]:
    """从文本中提取资质要求"""
    if not text:
        return []

    requirements = []

    # 常见资质关键词
    keywords = [
        "ISO9001", "ISO14001", "ISO27001", "CMMI", "高新技术企业",
        "软件企业", "系统集成资质", "安防资质", "涉密资质",
        "建筑工程资质", "电子与智能化", "消防设施", "建筑装修装饰",
    ]

    for keyword in keywords:
        if keyword in text:
            requirements.append(keyword)

    return requirements


def generate_tender_hash(tender: TenderItem) -> str:
    """生成招标信息唯一标识"""
    content = f"{tender.source}:{tender.title}:{tender.publish_date}"
    return hashlib.md5(content.encode('utf-8')).hexdigest()


# ============== 测试代码 ==============

async def test_crawler():
    """测试采集器"""
    print("=== 测试模拟采集器 ===")
    scraper = MockScraper()
    async with scraper:
        tenders = await scraper.get_list()
        print(f"采集到 {len(tenders)} 条数据")
        for t in tenders[:3]:
            print(f"- {t.title}")
            print(f"  预算: {t.budget}, 地点: {t.location}")
            print()

if __name__ == "__main__":
    asyncio.run(test_crawler())
