# scripts/run_pipeline.py
from processor.notice_spider import crawl_notices
from processor.clean_dedup import load_and_clean
from vector_store import store_to_vector_db
from import_to_ls import import_to_label_studio
import time

def run_pipeline():
    print("🚀 开始执行通知公告爬取流程...")
    try:
        # 1. 爬取
        crawl_notices()

        # 2. 清洗
        cleaned_data, cleaned_file = load_and_clean()

        # 3. 向量化入库
        store_to_vector_db(cleaned_file)

        # 4. 导入标注系统
        import_to_label_studio(cleaned_file)

        print("🎉 全流程执行完毕！")
    except Exception as e:
        print(f"❌ 流程出错: {e}")

if __name__ == '__main__':
    run_pipeline()