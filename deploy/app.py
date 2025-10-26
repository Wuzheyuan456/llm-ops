# app.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
import random
import time

app = FastAPI(title="Mock vLLM API (OpenAI Compatible)", version="0.1.0")

# 模拟一些“生成”的文本
RESPONSE_SAMPLES = [
    "The capital of France is Paris.",
    "To be or not to be, that is the question.",
    "The model is running in mock mode. No real inference here.",
    "42 is the answer to life, the universe, and everything."
]

class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 16
    temperature: Optional[float] = 0.7
    n: Optional[int] = 1

class Choice(BaseModel):
    text: str
    index: int

class CompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[Choice]

@app.post("/v1/completions", response_model=CompletionResponse)
async def create_completion(request: CompletionRequest):
    # 模拟延迟（0.1~1秒），相当于推理耗时
    delay = random.uniform(0.1, 1.0)
    time.sleep(delay)

    # 随机选择响应（可扩展为基于 prompt 的规则）
    texts = [
        random.choice(RESPONSE_SAMPLES)[:request.max_tokens]
        for _ in range(request.n)
    ]

    return CompletionResponse(
        id=f"cmpl-{int(time.time())}",
        object="text_completion",
        created=int(time.time()),
        model="mock-llama-3-8b",
        choices=[
            Choice(text=text, index=i) for i, text in enumerate(texts)
        ]
    )

@app.get("/health")
async def health():
    return {"status": "healthy"}

"""
构建镜像
cd mock-vllm
docker build -t mock-vllm:latest .

运行容器
docker run -p 8000:8000 --rm mock-vllm:latest
--rm 容器一退出，就自动删除它，不留痕迹
测试 API
curl http://localhost:8000/health
# 返回: {"status":"healthy"}

curl -X POST http://localhost:8000/v1/completions \
     -H "Content-Type: application/json" \
     -d '{
           "prompt": "Hello, how are you?",
           "max_tokens": 50,
           "temperature": 0.7
         }'

给镜像打版本标签
docker tag mock-vllm:latest your-registry/mock-vllm:v0.1-mock
docker push your-registry/mock-vllm:v0.1-mock

Helm 的 values.yaml
image:
  repository: your-registry/mock-vllm
  tag: v0.1-mock
  
  
  
启动之后kubectl port-forward svc/vllm-service 8000:80
这条命令监听本地 8000 端口，并把所有请求转发到 K8s 集群内的 vllm-service 服务的 80 端口
"""