
 # 🚀 llm-ops
 搭建大模型DevOps流水线，数据→训练→部署一键完成

[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![K8s](https://img.shields.io/badge/K8s-1.23+-blue.svg)](https://kubernetes.io/)
[![Helm](https://img.shields.io/badge/Helm-3+-blue.svg)](https://helm.sh/)
[![Label-Studio](https://img.shields.io/badge/Label%20Studio-1.11+-blue.svg)](https://labelstud.io/)
[![OpenAI-API](https://img.shields.io/badge/API-OpenAI%20Compatible-green.svg)](https://platform.openai.com/docs/)

---

## 📌 一句话定位
**“把大学官网非结构化通知→清洗→向量化→人工标注→微调→灰度上线→线上日志回流标注”** 全链路自动化，**5 分钟从零到生产**。

---

## 🎯 能力矩阵（一行命令即可拥有）

| 阶段 | 技术 | 开关 | 备注 |
|---|---|---|---|
| 通知爬取 | requests + BeautifulSoup | 定时 CronJob | 可配置多校 |
| 清洗/去重/向量化 | pandas + Sentence-BERT + ChromaDB | 默认启用 | 本地向量库 |
| 人工标注 | Label Studio SDK | 默认启用 | web 点选即可 |
| 增量训练 | PyTorch + MLflow + DVC + Airflow | 数据变更触发 | 模型门禁 acc≥0.85 |
| 权重版本 | Git tag + DVC remote | 自动打 tag | `git checkout & dvc checkout` 回滚 |
| 灰度上线 | Helm + Istio | `helm upgrade --set canary.weight=10` | 90/10、Header AB |
| 可观测 | Prometheus + Grafana | `helm install kube-prometheus-stack` | vLLM-SRE 面板 |
| 数据闭环 | 线上日志 → 采样 → 回流 Label Studio | CronJob 每天 02:00 | 人工打分 → 优劣 CSV |

---

## 🗂️ 项目结构（单仓库三合一）

```
campus-llm-flywheel/
├── data-pipeline/               # ① 通知公告数据管道
│   ├── notice_spider.py
│   ├── clean_dedup.py
│   ├── vector_store.py
│   └── import_to_ls.py
├── process/              # ② MLOps 微调流水线
│   ├── src/train.py            # 增量训练 + MLflow + 门禁
│   ├── airflow/dags/train_nwnu_model.py
│   └── models/best_model.pth.dvc
├── llm-ops/              # ③ vLLM 灰度发布
│   ├── AB+monitor/             # 含 Prometheus 指标埋点
│   ├── vllm-helm-chart/        # 两份 Deployment(v1/v2)
│   └── istio-demo.yaml
├── glue/                       # 胶水脚本
│   ├── ls-export-and-commit.sh # LS→Git→DVC
│   ├── publish-model.sh        # 权重→PV→ConfigMap→灰度
│   └── k8s-*.yaml              # 一次性 PV/VS/DestRule
├── values-global.yaml          # 全局镜像仓库/域名
└── README-INTEGRATION.md       # 你正在看的文档
```

---

## ⚙️ 5 分钟极速体验（本地 minikube）

```bash
# 1. 启动集群
minikube start --cpus=8 --memory=12g --mount --mount-string="$(pwd):/mnt/flywheel"

# 2. 安装 Istio + Prometheus
istioctl install --set profile=demo -y
kubectl label ns default istio-injection=enabled
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prom prometheus-community/kube-prometheus-stack -f glue/prometheus-values.yaml

# 3. 一键部署（含灰度）
helm install vllm ./3-serve-layer/vllm-helm-chart \
  -f values-global.yaml \
  --set global.image=harbor.campus.edu/llm/vllm-service \
  --set model.canary.weight=10

# 4. 获取网关
export GATEWAY_URL=$(minikube ip):$(kubectl -n istio-system get svc istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="http2")].nodePort}')

# 5. 90/10 流量验证
for i in {1..20}; do
  curl -s -H "Host: vllm-service.default.svc.cluster.local" \
       -X POST http://$GATEWAY_URL/v1/completions \
       -d '{"prompt":"你好", "max_tokens":20}' | jq -r .text
done
# Grafana 出现 v1/v2 两条曲线即成功
```

---

## 📊 核心指标（Prometheus 已埋点）

| 指标 | 类型 | 含义 |
|---|---|---|
| vllm_request_latency_seconds | Histogram | 端到端延迟 |
| vllm_token_latency_seconds | Histogram | 单 token 延迟 |
| vllm_gpu_utilization | Histogram | GPU 利用率 0~1 |
| vllm_requests_total | Counter | 状态码维度 QPS |

浏览器打开 `http://<node-ip>:30090 → vLLM-SRE` 面板实时查看。

---

## 🔄 日常运维命令

```bash
# 手动触发训练（测试）
kubectl create job train-now --from=cronjob/train-nwnu-model

# 权重回滚
git tag -l | grep v2.1
git checkout v2.1 && dvc checkout
bash glue/publish-model.sh

# 灰度流量调整
helm upgrade vllm . --set model.canary.weight=50   # 50%
helm upgrade vllm . --set model.canary.weight=100  # 全量
```

---

## 🧱 技术栈速览

| 模块 | 选型 |
|---|---|
| 爬虫 | requests, BeautifulSoup, APScheduler |
| 清洗/向量化 | pandas, Sentence-BERT, ChromaDB |
| 标注 | Label Studio SDK |
| 训练 | PyTorch, Transformers, MLflow, DVC, Airflow |
| 推理 | vLLM, Istio, Prometheus, Grafana |
| 包管理 | Helm, Docker, Git, Make |

---

## 🤝 贡献 & 反馈

1. Fork → Feature 分支 → PR  
2. 提交 Issue 请附 `kubectl version` 与复现脚本  
3. 欢迎认领 Roadmap（见 `docs/roadmap.md`）

**如果本项目帮到你，给个 ⭐ Star 让我知道！**
