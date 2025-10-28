🚀  vLLM-Istio-Canary  
「开箱即用」的 **大模型推理服务灰度发布+可观测+数据闭环** 生产级方案。

---

📁 仓库结构
```
deploy/
├── AB+monitor/                    # vLLM 镜像源码（含 Prometheus 指标）
│   ├── app.py                     #加入Prometheus埋点
│   ├──  cronjob.yaml
│   ├──  sample_queries.py       # 每日自动采样
│   ├──  service.yaml            
│   └──virtualservice-ab.yaml
├── vllm-helm-chart/                 # 一键部署 Chart
│   ├── templates/
│       ├── vllm-deployment-v1.yaml
│       ├── vllm-deployment-v2.yaml
│       ├── service.yaml
│       ├── hpa.yaml
│       ├── gateway.yaml
│       ├── destination-rule.yaml
│       └── virtual-service-canary.yaml
├── app.py                            # vllm模拟接口
├── docerfile                 
├── requirements.txt                  
└── istio-demo.yaml                   # istio安装文件
```

---

🎯 能力矩阵（一行命令即可拥有）
| 能力 | 实现方式 | 开关 |
|---|---|---|
| 🚢 **Docker 化 vLLM** | 官方镜像 + Flask 接口 + Prometheus 指标 | `docker build -t vllm-service:v1 .` |
| 🔧 **Helm 部署** | 两份 Deployment(v1/v2) + Service + HPA | `helm install vllm ./helm-chart` |
| 📈 **自动扩缩容** | CPU/内存 双指标 HPA | 默认启用 |
| 🌈 **Istio 90/10 金丝雀** | DestinationRule + VirtualService 权重 | `virtualservice.yaml` |
| 🧪 **Header 级 A/B 测试** | 仅带 `x-ab-test: v2` 走新版本 | `virtualservice-ab.yaml` |
| 📊 **Prometheus+Grafana** | 自定义延迟/token/GPU 指标 | `helm install prometheus …` |
| 🔄 **数据闭环** | CronJob 每日采样 100 条 → 标注池 | `cronjob.yaml` |

---

🚀 5 分钟快速开始
1. 启动本地 K8s  
```bash
minikube start --driver=docker --cpus=4 --memory=8g
```

2. 安装 Istio  
```bash
istioctl install --set profile=demo -y
kubectl label ns default istio-injection=enabled
```

3. 安装 Prometheus + Grafana  
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prom prometheus-community/kube-prometheus-stack -f k8s/prometheus-values.yaml
```

4. 构建并推送 vLLM 镜像（可改用 ghcr.io 官方镜像）  
```bash
cd service
docker build -t your-registry/vllm-service:v1 .
docker push your-registry/vllm-service:v1
```

5. 一键部署 vLLM 金丝雀  
```bash
cd helm-chart
helm install vllm . --set image.repository=your-registry/vllm-service
```

6. 获取网关地址  
```bash
export GATEWAY_URL=$(minikube ip):$(kubectl -n istio-system get svc istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="http2")].nodePort}')
```

7. 90/10 流量验证  
```bash
for i in {1..20}; do
  curl -s -H "Host: vllm-service.default.svc.cluster.local" \
       -X POST http://$GATEWAY_URL/v1/completions \
       -d '{"prompt":"hello", "max_tokens":5}' | jq -r .text
done
```
观察 Grafana：`vLLM-SRE` 面板实时出现 v1/v2 两条曲线即成功。

---

📊 Prometheus 暴露的核心指标
| 名称 | 类型 | 含义 |
|---|---|---|
| `vllm_request_latency_seconds` | Histogram | 端到端延迟 |
| `vllm_token_latency_seconds` | Histogram | 单 token 延迟 |
| `vllm_gpu_utilization` | Histogram | GPU 利用率（0~1） |
| `vllm_requests_total` | Counter | 状态码维度 QPS |

---

🔄 数据闭环流程（自动）
1. CronJob 每天 02:00 从日志采样 100 条真实 prompt；
2. 调用当前模型生成答案，写入 `/annotations/samples_YYYYMMDD.jsonl`；
3. 人工导入 Label Studio 打分（1-5 分）；
4. 评分脚本自动计算 v1/v2 优劣 → 输出 CSV → 决策是否全量。

---

🧪 A/B 测试（Header 路由）
```bash
# 走 v2 实验组
curl -H "x-ab-test: v2" -H "Host: vllm-service.default.svc.cluster.local" \
     http://$GATEWAY_URL/v1/completions -d '{"prompt":"hello"}'
```
Grafana 对比两组：延迟、错误率、人工评分 → 科学全量。

---

🔍 常见排障
| 现象 | 解决 |
|---|---|
| `no healthy upstream` | 检查 DestinationRule 子集 label 是否同 deployment 一致 |
| 指标缺失 | 确认 service 有 `prometheus.io/scrape: "true"` 注解 |
| 短域名 404 | Istio 必须使用 FQDN，如 `vllm-service.default.svc.cluster.local` |

---

🏗️ 架构图
```
┌-------------┐     ┌-------------┐
│  Prometheus │←----┤   vLLM Pod  │ 8001/metrics
└------┬------┘     └------┬------┘
       │ Grafana           │ 采样脚本
       ▼                   ▼
┌-------------┐     ┌-------------┐
│  Grafana    │     │ 标注池      │
│  Dashboard  │     │ (JSONL)     │
└------┬------┘     └------┬------┘
       │                   │
       └--------决策--------┘
              人 + 指标
```

---

🎯 未来展望
- [ ] Argo Rollouts 自动金丝雀分析  
- [ ] Kiali 流量拓扑可视化  
- [ ] vLLM 多 LoRA 热加载  
- [ ] 接入 W&B / MLflow 统一实验管理

---

🤝 贡献
1. Fork → Feature 分支 → PR  
2. 提交 Issue 请附 `kubectl version` & 复现脚本  
3. 欢迎认领 Roadmap！


如果本项目帮到你，给个 ⭐ Star 让我知道！
