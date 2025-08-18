import requests
from datetime import datetime,timedelta
import time
import sqlite3
# 导入需要的模块

BASE_URL = 'https://api.themoviedb.org/3/discover'
with open('api_key.txt', 'r') as f:
    API_KEY = f.read().strip()
# 定义常量和全局配置

def init_db():
    conn = sqlite3.connect('database/media_data.db')
    cursor = conn.cursor()
    # 创建数据库
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS media(
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        title        TEXT,
        release_date TEXT,
        region       TEXT,
        genres       TEXT,
        overview     TEXT,
        poster_url   TEXT
    )
''')
    conn.commit()
    return conn
# 定义数据库的函数

def get_date_range(days=3):
    today = datetime.now().date()
    start_time = today - timedelta(days=days-1)
    return start_time.isoformat(), today.isoformat()
# 定义日期范围函数

def build_params(media_type, start_date, end_date, language='zh-CN', page=1):
    if media_type == 'movie':
        date_gte_key = 'primary_release_date.gte'
        date_lte_key = 'primary_release_date.lte'
        sort_by = 'primary_release_date.desc'
    else:
        date_gte_key = 'first_air_date.gte'
        date_lte_key = 'first_air_date.lte'
        sort_by = 'first_air_date.desc'
    return {
        'api_key': API_KEY,
        'language': language,
        'sort_by': sort_by,
        'page': page,
        'include_adult': True,
        date_gte_key: start_date,
        date_lte_key: end_date,
    }
# 定义构建请求数据字典函数

def fetch_data(media_type='movie', page=1, language='zh-CN'):
    url = f'{BASE_URL}/{media_type}'
    start_date, end_date = get_date_range()
    params = build_params(media_type, start_date, end_date, page=page, language=language)
    try:
        response = requests.get(url, params=params, timeout=10)  # 设置超时时间
        return response.json()
    except requests.exceptions.RequestException:
        return {'results': []}
# 定义请求数据的函数

def fetch_all_data():
    all_results = []
    for media_type in ['movie', 'tv']:
        page = 1
        while True:
            try:
                data = fetch_data(media_type=media_type, page=page)
                results = data.get('results', [])
                if not results:
                    break
                all_results.extend(results)
                if page >= data.get('total_pages', 1):
                    break
                page += 1
                time.sleep(0.25)  # 每页请求间隔 0.25 秒，避免触发 TMDb 限流
            except requests.exceptions.RequestException:
                return {'results': []}
    return all_results
# 定义循环请求所有页数数据并存入列表的函数

def clean_item(item):
    return {
        'movie_id': item.get('id'),
        'title': item.get('title') or item.get('name'),
        'release_date': item.get('release_date') or item.get('first_air_date'),
        'region': clean_region(item),
        'genres': clean_genres(item),
        'overview': clean_overview(item),
        'poster_path': clean_poster_path(item)
    }
# 清洗单个数据项的函数

def clean_all_results(all_results):
    clean_results = []
    for result in all_results:
        cleaned = clean_item(result)
        if cleaned['region'] and cleaned['genres'] and cleaned['poster_path'] and cleaned['overview']:
            clean_results.append(cleaned)
    return clean_results
# 批量清洗数据并存入新列表的函数

country_map = {
    "CN": "中国",
    "JP": "日本",
    "KR": "韩国",
    "HK": "香港",
    "US": "美国",
    "GB": "英国",
    "FR": "法国"
}
def clean_region(item):
    countries = item.get('origin_country')
    if not countries:
        countries =[c.get('iso_3166_1') for c in item.get('production_countries', []) if c.get('iso_3166_1')]
    regions = [country_map[code] for code in countries if code in country_map]
    return ", ".join(regions) if regions else None
# region清洗函数

genre_map = {
    28: "动作",
    12: "冒险",
    16: "动画",
    35: "喜剧",
    80: "犯罪",
    99: "纪录片",
    18: "剧情",
    10751: "家庭",
    14: "奇幻",
    36: "历史",
    27: "恐怖",
    10402: "音乐",
    9648: "悬疑",
    10749: "爱情",
    878: "科幻",
    10770: "电视电影",
    53: "惊悚",
    10752: "战争",
    37: "西部",
    10764: "真人秀",
    10765: "科幻与奇幻",
    10759: "动作与冒险",
    10762: "儿童",
    10767: "脱口秀"
}
def clean_genres(item):
    genre_ids = item.get('genre_ids', [])
    genre_names = [genre_map.get(gid, 'Unknown') for gid in genre_ids]
    return ", ".join(genre_names) if genre_names else None
# genres清洗函数

def clean_overview(item):
    return item.get('overview') or None
# overview清洗函数

def clean_poster_path(item):
    poster_path = item.get('poster_path')
    if poster_path:
        return f"https://image.tmdb.org/t/p/w500{poster_path}"
    else:
        return None
# poster_path清洗函数

def insert_items(clean_results, conn):
    cursor = conn.cursor()
    for item in clean_results:
        cursor.execute('''
        INSERT OR IGNORE INTO media (id, title, release_date, region, genres, overview, poster_url) 
        VALUES (?, ?, ?, ?, ?, ?, ?)''',(
            item['movie_id'],
            item['title'],
            item['release_date'],
            item['region'],
            item['genres'],
            item['overview'],
            item['poster_path']
        ))
        conn.commit()
    return conn
# 定义把数据插入数据表的函数

def main():
    all_results = fetch_all_data()
    clean_results = clean_all_results(all_results)
    conn = init_db()
    insert_items(clean_results, conn)
    conn.close()

if __name__ == '__main__':
    main()
# 主函数与运行入口

