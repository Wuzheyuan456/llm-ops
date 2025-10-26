import json
import random
from datetime import datetime
import requests

# 日志
LOG_FILE = "/app/logs/requests.log"
OUTPUT_FILE = f"/annotations/samples_{datetime.now().strftime('%Y%m%d')}.jsonl"

def sample_queries():
    with open(LOG_FILE, 'r') as f:
        lines = f.readlines()
    
    # 随机采样 100 条
    samples = random.sample(lines, min(100, len(lines)))
    
    results = []
    for line in samples:
        try:
            req = json.loads(line.strip())
            prompt = req['prompt']
            # 调用模型获取回答（或直接从日志读）
            response = requests.post("http://localhost:8000/v1/completions", json=req).json()
            answer = response.get("text", "")
            
            results.append({
                "prompt": prompt,
                "response": answer,
                "timestamp": datetime.now().isoformat(),
                "model_version": "v1",
                "sample_source": "daily_sample"
            })
        except:
            continue
    
    # 写入标注池（可对接 Label Studio、自研系统等）
    with open(OUTPUT_FILE, 'w') as f:
        for item in results:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    print(f"已采样 {len(results)} 条数据，写入 {OUTPUT_FILE}")

if __name__ == "__main__":
    sample_queries()