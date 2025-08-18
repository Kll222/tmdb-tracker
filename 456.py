import requests
from datetime import datetime, timedelta
import time
import sqlite3
import os

BASE_URL = 'https://api.themoviedb.org/3'
with open('api_key.txt', 'r') as f:
    API_KEY = f.read().strip()

language_map = {"zh", "ja", "ko", "en", "fr"}

country_map = {
    "CN": "中国", "JP": "日本", "KR": "韩国", "HK": "香港",
    "US": "美国", "GB": "英国", "FR": "法国"
}

genre_map = {
    28: "动作", 12: "冒险", 16: "动画", 35: "喜剧", 80: "犯罪", 99: "纪录片",
    18: "剧情", 10751: "家庭", 14: "奇幻", 36: "历史", 27: "恐怖", 10402: "音乐",
    9648: "悬疑", 10749: "爱情", 878: "科幻", 10770: "电视电影", 53: "惊悚",
    10752: "战争", 37: "西部", 10764: "真人秀", 10765: "科幻与奇幻",
    10759: "动作与冒险", 10762: "儿童", 10767: "脱口秀"
}

# --------------------- 数据库初始化 ---------------------
def init_db():
    os.makedirs('database', exist_ok=True)
    conn = sqlite3.connect('database/media_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS media(
            id INTEGER PRIMARY KEY,
            title TEXT,
            release_date TEXT,
            region TEXT,
            genres TEXT,
            overview TEXT,
            poster_url TEXT,
            media_type TEXT
        )
    ''')
    conn.commit()
    return conn

# --------------------- 日期范围 ---------------------
def get_date_range(days=3):
    today = datetime.now().date()
    start_time = today - timedelta(days=days-1)
    return start_time.isoformat(), today.isoformat()

# --------------------- 请求列表数据 ---------------------
def fetch_list(media_type='movie', page=1, language='en-US'):
    if media_type == 'movie':
        url = f'{BASE_URL}/discover/movie'
        date_gte = 'primary_release_date.gte'
        date_lte = 'primary_release_date.lte'
        sort_by = 'primary_release_date.desc'
        params = {
            'api_key': API_KEY,
            'language': language,
            'sort_by': sort_by,
            'include_adult': True,
            'page': page,
            date_gte: get_date_range()[0],
            date_lte: get_date_range()[1],
        }
    else:
        url = f'{BASE_URL}/discover/tv'
        date_gte = 'first_air_date.gte'
        date_lte = 'first_air_date.lte'
        sort_by = 'first_air_date.desc'
        params = {
            'api_key': API_KEY,
            'language': language,
            'sort_by': sort_by,
            'include_adult': True,
            'page': page,
            date_gte: get_date_range()[0],
            date_lte: get_date_range()[1]
        }
    try:
        response = requests.get(url, params=params, timeout=10)
        return response.json().get('results', [])
    except requests.exceptions.RequestException:
        return []

# --------------------- 请求单条中文数据 ---------------------
def fetch_detail_cn(media_type, media_id):
    url = f"{BASE_URL}/{media_type}/{media_id}"
    params = {'api_key': API_KEY, 'language': 'zh-CN'}
    try:
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except requests.exceptions.RequestException:
        return {}

# --------------------- 清洗字段 ---------------------
def clean_region(item):
    countries = item.get('origin_country') or [c.get('iso_3166_1') for c in item.get('production_countries', []) if c.get('iso_3166_1')]
    regions = [country_map.get(c) for c in countries if c in country_map]
    return ", ".join(regions) if regions else None

def clean_language(item):
    lang = item.get('original_language', '').lower()
    return lang if lang in language_map else None

def clean_genres(item):
    genre_ids = item.get('genre_ids', [])
    names = [genre_map.get(g) for g in genre_ids if genre_map.get(g)]
    return ", ".join(names) if names else None

def clean_item(item, media_type):
    return {
        'id': item.get('id'),
        'title': item.get('title') or item.get('name'),
        'release_date': item.get('release_date') or item.get('first_air_date'),
        'region': clean_region(item),
        'genres': clean_genres(item),
        'overview': item.get('overview'),
        'poster_url': f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}" if item.get('poster_path') else None,
        'media_type': media_type
    }

# --------------------- 合并中文 ---------------------
def merge_cn(en_item, cn_item):
    merged = {}
    for key in en_item.keys():
        merged[key] = cn_item.get(key) if cn_item.get(key) else en_item.get(key)
    if all(merged.values()):
        return merged
    return None

# --------------------- 插入数据库 ---------------------
def insert_items(items, conn):
    cursor = conn.cursor()
    for item in items:
        cursor.execute('''
            INSERT OR IGNORE INTO media (id, title, release_date, region, genres, overview, poster_url, media_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item['id'],
            item['title'],
            item['release_date'],
            item['region'],
            item['genres'],
            item['overview'],
            item['poster_url'],
            item['media_type']
        ))
    conn.commit()

# --------------------- 删除3天前的数据 ---------------------
def clean_old_data(conn):
    cursor = conn.cursor()
    start_date, _ = get_date_range(days=3)
    cursor.execute('DELETE FROM media WHERE release_date < ?', (start_date,))
    conn.commit()

# --------------------- 主函数 ---------------------
def main():
    conn = init_db()
    all_data = []

    for media_type in ['movie', 'tv']:
        page = 1
        while True:
            results_en = fetch_list(media_type, page=page, language='en-US')
            if not results_en:
                break
            merged_results = []

            for en_item in results_en:
                cn_item_raw = fetch_detail_cn(media_type, en_item['id'])
                cn_item = clean_item(cn_item_raw, media_type) if cn_item_raw else {}
                en_item_clean = clean_item(en_item, media_type)
                merged = merge_cn(en_item_clean, cn_item)
                if merged and clean_language(en_item):
                    merged_results.append(merged)

                time.sleep(0.2)  # 请求间隔

            all_data.extend(merged_results)

            page += 1
            if page > 1000:  # TMDb最多1000页
                break

    clean_old_data(conn)
    insert_items(all_data, conn)
    conn.close()

if __name__ == '__main__':
    main()
