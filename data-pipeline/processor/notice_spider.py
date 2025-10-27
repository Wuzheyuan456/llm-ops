# crawler/notice_spider.py
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os
from urllib.parse import urljoin

# 大学官网基础地址
BASE_URL = "https://XXX/"
NOTICE_URL = "https://XXX/newtzgg-list.jsp?urltype=tree.TreeTempUrl&wbtreeid=1187"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def parse_chinese_date(chinese_date: str) -> str:
    """
    将“十月22”转换为 “2025-10-22”
    当前年份 + 中文月份映射 + 日期
    """
    year = datetime.now().year
    month_map = {
        '一月': '01', '二月': '02', '三月': '03', '四月': '04',
        '五月': '05', '六月': '06', '七月': '07', '八月': '08',
        '九月': '09', '十月': '10', '十一月': '11', '十二月': '12'
    }
    for k, v in month_map.items():
        if chinese_date.startswith(k):
            day = chinese_date.replace(k, '').strip()
            return f"{year}-{v}-{int(day):02d}"
    return "未知"

def crawl_notices():
    print("🚀 开始爬取大学通知公告...")
    response = requests.get(NOTICE_URL, headers=HEADERS)
    response.raise_for_status()
    response.encoding = 'utf-8'  # 强制 UTF-8 防止乱码
    print(response.status_code, response.url)
    # print(response.text)

    soup = BeautifulSoup(response.text, 'html.parser')
    notice_items = soup.select('div.nwu-not ul li')
    #notice_items = soup.select('div.news-item')  # 所有通知项

    notices = []

    for item in notice_items:
        date_span = item.select_one('span.date')
        title_link = item.select_one('a')
        dept_span = item.select_one('span.department')

        if not title_link:
            continue

        # 提取信息
        raw_date = date_span.get_text(strip=True) if date_span else "未知"
        title = title_link.get_text(strip=True)
        url = urljoin(BASE_URL, title_link['href'])  # 拼接完整 URL
        department = dept_span.get_text(strip=True) if dept_span else "未知"

        # 转换中文日期为标准格式
        publish_date = parse_chinese_date(raw_date)

        # 初始化 content 字段（后续再抓）
        notices.append({
            "title": title,
            "url": url,
            "publish_date": publish_date,
            "raw_date": raw_date,  # 保留原始日期
            "department": department,
            "crawl_time": datetime.now().isoformat(),
            "content": ""
        })

    # 保存原始数据
    os.makedirs("data/raw", exist_ok=True)
    filename = f"data/raw/notices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(notices, f, ensure_ascii=False, indent=2)

    print(f"✅ 爬取完成，共 {len(notices)} 条通知，保存到 {filename}")
    return notices


def crawl_all_notices(max_pages=5):  # 先爬5页做测试
    all_notices = []
    for page in range(1, max_pages + 1):
        print(f"正在爬取第 {page} 页...")
        page_url = f"https://www.nwu.edu.cn/newtzgg-list.jsp?urltype=tree.TreeTempUrl&wbtreeid=1187&PAGENUM={page}"
        response = requests.get(page_url, headers=HEADERS)
        response.raise_for_status()
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')
        notice_items = soup.select('div.nwu-not ul li')

        for item in notice_items:
            month = item.select_one('time .month').get_text(strip=True)
            day = item.select_one('time .day').get_text(strip=True)
            raw_date = f"{month}{day}"

            title_link = item.select_one('a')
            title = title_link.get('title', '').strip()
            href = title_link.get('href', '').strip()
            url = urljoin(BASE_URL, href)

            dept_span = item.select_one('.related-site a')
            department = dept_span.get_text(strip=True) if dept_span else "未知"

            publish_date = parse_chinese_date(raw_date)

            all_notices.append({
                "title": title,
                "url": url,
                "publish_date": publish_date,
                "raw_date": raw_date,
                "department": department,
                "crawl_time": datetime.now().isoformat(),
                "content": ""
            })

    # 保存
    os.makedirs("./data/raw", exist_ok=True)
    filename = f"./data/raw/notices_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_notices, f, ensure_ascii=False, indent=2)

    print(f"所有通知爬取完成，共 {len(all_notices)} 条，保存到 {filename}")
if __name__ == '__main__':
    crawl_all_notices(max_pages=3)  # 先爬3页试试
