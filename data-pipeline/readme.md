
📊 大学通知公告自动化数据管道

一个完整的 Python 数据 pipeline，用于每日自动爬取大学官网通知公告，经过清洗、去重、向量化后存入本地向量数据库，并支持人工标注，构建可检索的“高校政策知识库”。  
🔁 从非结构化网页到结构化知识的转化实践  
🎯 适用于：数据工程、AI 应用、爬虫项目、RAG 基础系统

---

## 🚀 项目目标
- ✅ 每日定时爬取 [大学通知公告](https://XXX/newtzgg-list.jsp?urltype=tree.TreeTempUrl&wbtreeid=1187)
- ✅ 提取标题、发布时间、来源部门、正文内容
- ✅ 清洗去重，标准化中文日期（如“十月22” → 2025-10-22）
- ✅ 使用 Sentence-BERT 向量化，存入 ChromaDB 实现语义检索
- ✅ 集成 Label Studio，支持人工分类标注（如：放假 / 科研 / 教学）
- ✅ APScheduler 定时运行，形成可持续更新的知识闭环

---

## 🧱 技术栈

| 模块 | 技术 |
|------|------|
| 爬虫 | requests + BeautifulSoup4 |
| 数据处理 | pandas |
| 向量化 | sentence-transformers (all-MiniLM-L6-v2) |
| 向量数据库 | ChromaDB |
| 标注平台 | Label Studio SDK |
| 定时任务 | APScheduler |
| 开发环境 | Python 3.8+ |

---

## 📦 项目结构

```
school-notice-pipeline/
├── processor/
│   ├──data/
│   │   ├──raw/                  # 原始爬取 JSON 文件
│   │   └──cleaned/              # 清洗后结构化数据
│   ├── clean_dedup.py        # 清洗、去重、日期标准化
│   └── notice_spider.py      # 精准爬取通知列表与正文
├── vector_store.py       # 向量化并存入 ChromaDB
├── import_to_ls.py       # 导入数据至 Label Studio
├── run_pipeline.py       # 主流程入口
├── scheduler.py          # 每日定时执行
├── vectordb/                 # ChromaDB 向量数据库存储目录
├── config.py                 # 配置文件（URL、路径等）
└── requirements.txt          # 依赖包
```

---

## 🛠️ 快速开始

1. 安装依赖  
```bash
conda create -n data-pipeline python=3.10
conda activate data-pipeline
pip install -r requirements.txt
```

2. （可选）启动 Label Studio  
```bash
label-studio start
```
访问 http://localhost:8080 创建项目，获取 API Key 并配置。

3. 运行主流程  
```bash
python scripts/run_pipeline.py
```

4. 设置每日定时任务  
```bash
python scripts/scheduler.py
```
默认每天 6:00 自动执行。

---

## 🌟 核心能力亮点

| 阶段 | 技能点 |
|------|--------|
| 采集 | requests + BeautifulSoup、反爬策略、静态页面精准解析 |
| 清洗 | pandas 数据清洗、正则处理、中文日期标准化（“十月22” → 2025-10-22）、去重 |
| 存储 | 向量数据库（ChromaDB）、元数据持久化、本地文件管理 |
| 语义理解 | Sentence-BERT 向量化、语义相似度计算、嵌入模型应用 |
| 标注平台 | Label Studio 集成、API 调用、人机协同闭环 |
| 自动化 | APScheduler 定时任务、脚本化执行、可重复运行 |

---

## 🔄 数据流程

```
[定时触发]
↓
[爬虫模块] → 精准提取：标题、链接、日期、部门
↓
[正文抓取] → 进入详情页获取完整内容
↓
[清洗去重] → 去噪、标准化、去重
↓
[向量化] → Sentence-BERT 生成 384 维向量
↓
[ChromaDB] → 支持语义检索
↓
[Label Studio] → 人工标注分类，为 AI 训练打基础
```

---

## 📊 应用场景
- 构建“通知助手”，支持自然语言查询
- 分析科研申报、放假通知发布趋势
- 作为 RAG（检索增强生成）系统的知识源
- 可迁移至其他高校或政府网站，做竞品监控

---

## 🚀 未来计划
- [ ] 接入大模型自动生成摘要
- [ ] 使用 Streamlit 搭建前端展示页
- [ ] 微信推送重要通知
- [ ] 支持多所学校配置化爬取

---

## 🙌 鸣谢
- [Label Studio](https://labelstud.io/) - 强大的开源标注平台
- [Sentence Transformers](https://www.sbert.net/) - 优秀的文本向量化工具
- [ChromaDB](https://www.trychroma.com/) - 轻量高效的向量数据库
```
