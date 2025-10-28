
🌐 大学官网数据的语言模型训练系统  
使用 PyTorch + MLflow + DVC + Airflow 构建的工业级 MLOps 流水线  
支持 增量训练、版本回溯、自动化调度、模型门禁，实现从数据到部署的全生命周期管理

---

## 📌 项目目标
构建一个面向高校官网文本理解的自动化语言模型训练系统，具备：
- ✅ 基于西北大学官网 JSON 数据微调语言模型（如 BERT）
- ✅ 使用 DVC 管理数据与模型版本（本地存储）
- ✅ 使用 MLflow 全流程记录实验、参数、指标、模型
- ✅ 使用 Airflow 调度每日/每周训练任务
- ✅ 支持 增量训练触发（数据变更 → 自动训练）
- ✅ 支持 版本回滚（git tag + dvc checkout）
- ✅ 实现 模型门禁（准确率 < 0.85 不允许上线）

---

## 🧩 技术栈
| 工具 | 作用 |
|------|------|
| PyTorch + Transformers | 模型训练（BERT 等） |
| DVC | 数据 & 模型版本控制（本地缓存） |
| MLflow | 实验追踪、模型注册、部署 |
| Airflow | 定时调度训练任务 |
| Git | 代码与 .dvc 指针版本控制 |
| Python | 核心脚本与自动化逻辑 |

---

## 📦 项目结构
```
Program-pipeline/
├── data/
│   └── raw/
│       └── annotations.json   # 官网标注数据
├── models/
│   ├── best_model.pth          # 训练好的模型权重
│   └── best_model.pth.dvc      # DVC 指针文件
├── src/
│   ├── preprocess.py           # 数据预处理
│   ├── train.py                # 训练脚本（集成 MLflow）
│   ├── evaluate.py             # 评估脚本（用于门禁）
│   └── inference.py            # 推理服务
├── airflow/
│   └── train_nwnu_model.py # Airflow DAG 定义
├── mlruns/                     # MLflow 实验记录
├── .dvc/
│   ├── config                  # DVC 配置（需提交）
│   └── cache/                  # 本地缓存（不提交）
├── params.yaml                 # 超参配置（learning_rate, batch_size 等）
├── requirements.txt            # 依赖
├── .gitignore                  # DVC 生成，防止 Git 跟踪大文件
└── README.md                   # 你正在看的文档
```

---

## 🔧 快速开始
1. 安装依赖
```bash
conda create -program-pipline  python=3.10
conda activate program-pipline
pip install -r requirements.txt
```

2. 初始化 DVC（本地模式）
```bash
dvc init
dvc remote add -d local-storage .dvc/cache   # 使用本地缓存作为远程
```
💡 适合单机或小团队使用，无需 S3/OSS。

---

## 🔄 核心工作流
1. 添加新数据（模拟官网更新）
```bash
vim data/raw/annotations.json
dvc add data/raw/annotations.json
```

2. 提交变更
```bash
git add data/raw/annotations.json.dvc
git commit -m "feat: update nwnu website data"
```

3. 手动触发训练（测试用）
```bash
python src/train.py
```
- ✅ 训练过程自动记录到 MLflow
- ✅ 模型保存为 `models/best_model.pth` 并由 DVC 管理

---

## 📊 实验追踪（MLflow）
启动 MLflow UI
```bash
mlflow ui --port 5001 --host 0.0.0.0
```
访问：http://localhost:5001

自动记录内容  
- 参数：learning_rate, batch_size, epochs  
- 指标：accuracy, loss, f1_score  
- 模型：pytorch.log_model()  
- 代码快照：Git commit ID 自动关联  

---

## 🕹️ 增量训练机制
`src/train.py` 内置检测逻辑：
```python
def should_train():
    result = subprocess.run(['dvc', 'status'], capture_output=True, text=True)
    return 'modified' in result.stdout or 'new' in result.stdout

if should_train():
    print("✅ 数据变更，开始训练...")
    # 执行训练
else:
    print("🚫 无数据变更，跳过训练")
```
避免无效训练，节省算力。

---

## 🛑 模型门禁（Model Gate）
在训练后自动评估，低于阈值不提交：
```python
# src/train.py
accuracy = evaluate(model, val_loader)

if accuracy < 0.85:
    raise Exception(f"🚨 模型门禁失败：accuracy={accuracy} < 0.85")
else:
    print("✅ 模型通过门禁，允许提交")
    mlflow.pytorch.log_model(model, "model")
    subprocess.run(['git', 'commit', '-m', f'model v{version}'])
```
防止低质量模型污染主分支。

---

## 🔁 版本回滚与复现
给模型打标签
```bash
git tag -a v1.0 -m "Model v1.0: baseline, accuracy=0.82"
git tag -a v2.0 -m "Model v2.0: fine-tuned, accuracy=0.91"
git push origin --tags
```

回滚到任意版本
```bash
git checkout v1.0
dvc checkout
python src/inference.py --model models/best_model.pth
```
✅ 完整复现历史模型。

---

## 🕰️ Airflow 调度（每日训练）
配置 DAG  
`airflow/dags/train_nwnu_model.py`：
```python
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'mlops',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'train_nwnu_llm',
    default_args=default_args,
    description='每日训练西北大学语言模型',
    schedule_interval='0 2 * * *',  # 每天凌晨2点
    start_date=datetime(2025, 1, 1),
    catchup=False,
)

t1 = BashOperator(
    task_id='run_training',
    bash_command='cd /path/to/nwnu-llm && python src/train.py',
    dag=dag,
)
```
✅ 实现 自动化、无人值守训练。

---

## 🐛 已知问题与解决方案
🔥 问题：subprocess.run 执行 git commit 返回 255  
子进程环境缺失，导致 Git 钩子或 Conda 环境未加载。  
✅ 解决方案（推荐）
```python
subprocess.run(['bash', '-l', '-c', 'git commit -m "msg"'])
```
使用登录 Shell 加载完整环境。

---

## 📚 数据说明
- 数据来源：学校大学官网公开页面 JSON 抽取
- 标注内容：行政通知、新闻公告、招生信息等分类标签
- 用途：训练文本分类模型，支持智能问答、信息抽取
- ⚠️ 数据仅用于学术研究，不包含敏感信息。

---

## 🚀 下一步优化
- [ ] 将 DVC 远程升级为 S3/MinIO，支持团队协作  
- [ ] 使用 MLflow Model Registry 管理 Staging / Production 模型  
- [ ] 集成 Weights & Biases 替代 MLflow UI（可选）  
- [ ] 添加数据漂移检测（Evidently）  
- [ ] 模型 API 化（FastAPI + Docker）  

---

## 🙌 致谢
本项目旨在探索 高校场景下的 MLOps 最佳实践，推动 AI 在教育信息化中的落地。

