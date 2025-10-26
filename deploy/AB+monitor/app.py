# app.py
from fastapi import FastAPI, Request
from prometheus_client import (
    start_http_server,
    Histogram,
    Counter,
    generate_latest,
    CONTENT_TYPE_LATEST
)
import time
import threading
import uvicorn

app = FastAPI()

# ======================================
# 1. 定义你要监控的指标
# ======================================

# 请求延迟（histogram）
REQUEST_LATENCY = Histogram(
    'vllm_request_latency_seconds',
    'Time spent processing request'
)

# 请求总数（counter），按状态码分类
REQUESTS_TOTAL = Counter(
    'vllm_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

# Token 延迟（可选）
TOKEN_LATENCY = Histogram(
    'vllm_token_latency_seconds',
    'Latency per token generated'
)

# GPU 利用率（模拟）
GPU_UTIL = Histogram(
    'vllm_gpu_utilization',
    'GPU utilization',
    buckets=[0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
)

# ======================================
# 2. 启动独立的 metrics server（端口 8001）
# ======================================

def run_metrics_server():
    start_http_server(8001)  # ← 自动提供 /metrics 接口

# 在后台启动 metrics server
threading.Thread(target=run_metrics_server, daemon=True).start()

# ======================================
# 3. 业务接口（vLLM 模拟推理）
# ======================================

@app.post("/v1/completions")
async def completions(request: Request):
    # 开始计时
    start_time = time.time()

    try:
        # 模拟 vLLM 推理（真实场景调用 model.generate()）
        prompt_data = await request.json()
        prompt = prompt_data.get("prompt", "hello")

        # 模拟推理耗时（比如 0.3~0.8 秒）
        import random
        delay = random.uniform(0.3, 0.8)
        time.sleep(delay)

        # 模拟生成 token 数
        tokens = len(prompt.split()) * 2
        token_latency = delay / max(tokens, 1)
        
        # 记录指标（这才是关键！）
        REQUEST_LATENCY.observe(time.time() - start_time)
        REQUESTS_TOTAL.labels(method='POST', endpoint='/v1/completions', status='200').inc()
        TOKEN_LATENCY.observe(token_latency)
        GPU_UTIL.observe(random.uniform(0.4, 0.8))  # 模拟 GPU 使用率

        return {
            "text": f"Generated response for: {prompt}",
            "tokens": tokens,
            "latency": delay
        }

    except Exception as e:
        # 记录错误
        REQUESTS_TOTAL.labels(method='POST', endpoint='/v1/completions', status='500').inc()
        return {"error": str(e)}, 500

#也可以不写
@app.get("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}