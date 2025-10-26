# processor/clean_dedup.py
import pandas as pd
import re
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions
import os
import json


# 加载模型
model = SentenceTransformer('./all-MiniLM-L6-v2')  # 中文也支持，轻量
ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="./all-MiniLM-L6-v2")

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)  # 多空格变单空格
    return text.strip()

def load_and_clean():
    # 读取最新爬取文件
    files = sorted([f for f in os.listdir('data/raw') if f.startswith('notices_')])
    if not files:
        print("❌ 无原始数据文件")
        return []

    latest_file = f"data/raw/{files[-1]}"
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = pd.json_normalize(json.load(f))

    data['content_clean'] = data['content'].astype(str).apply(clean_text)
    data['title_clean'] = data['title'].astype(str).apply(clean_text)

    # 去重：先按标题 + 日期去重
    data.drop_duplicates(subset=['title_clean', 'publish_date'], inplace=True)

    # 语义去重（可选，耗时）
    # 这里只做向量化入库，去重可在查询时做

    # 保存清洗后数据
    os.makedirs("data/cleaned", exist_ok=True)
    #clean_file = f"data/cleaned/cleaned_{os.path.basename(latest_file)}"
    clean_file = f"data/cleaned/notices_clean_latest.json"
    data.to_json(clean_file, force_ascii=False, orient='records', indent=2)

    print(f"✅ 清洗完成，保存到 {clean_file}")
    return data.to_dict('records'), clean_file


if __name__ == '__main__':
    load_and_clean()