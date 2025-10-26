# vector_db/vector_store.py
import chromadb
import json
from processor.clean_dedup import model  # 复用模型
from chromadb.utils import embedding_functions

def store_to_vector_db(cleaned_file):
    client = chromadb.PersistentClient(path="./vectordb")
    collection = client.get_or_create_collection(
        name="school_notices",
        embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction("all-MiniLM-L6-v2")
    )

    with open(cleaned_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    texts = [item['content_clean'] for item in data]
    embeddings = model.encode(texts, show_progress_bar=False)

    ids = [f"notice_{item.get('url', '').split('/')[-1].replace('.html','')}" for item in data]
    metadatas = [{
        "title": item['title'],
        "url": item['url'],
        "publish_date": item['publish_date'],
        "crawl_time": item['crawl_time']
    } for item in data]

    collection.add(
        embeddings=embeddings.tolist(),
        documents=texts,
        metadatas=metadatas,
        ids=ids
    )
    print(f"✅ 已向量化并存入 ChromaDB，共 {len(data)} 条")

if __name__ == '__main__':
    store_to_vector_db(cleaned_file='./processor/data/cleaned/notices_clean_latest.json')