# src/data.py
import json
import pandas as pd
from transformers import AutoTokenizer
from typing import Dict, Tuple
import torch

# 定义类别到索引的映射（必须固定！）
LABEL2ID: Dict[str, int] = {
    "放假通知": 0,
    "学术活动": 1,
    "行政通知": 2,
    "招聘信息": 3,
    "其他": 4
}

ID2LABEL: Dict[int, str] = {v: k for k, v in LABEL2ID.items()}


def load_data(json_path: str) -> pd.DataFrame:
    """
    加载 Label Studio 导出的 JSON 标注数据
    假设每个 item 包含：title, content, category（标注结果）
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    texts = []
    labels = []

    for item in data:
        # 使用 title 作为输入文本（也可以拼接 content）
        text = item.get("title", "").strip()
        if not text:
            continue  # 跳过空标题

        # 获取标注的 category
        category = item.get("category", "").strip()

        if category not in LABEL2ID:
            print(f"⚠️ Unknown category '{category}', mapped to '其他'")
            category = "其他"  # 默认类别

        texts.append(text)
        labels.append(LABEL2ID[category])

    return pd.DataFrame({
        'text': texts,
        'label': labels
    })


def tokenize_data(df: pd.DataFrame, model_name: str, max_length: int) -> Tuple[Dict, torch.Tensor]:
    """
    对文本进行分词处理
    """
    from transformers import AutoTokenizer
    import torch

    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # 编码文本
    encodings = tokenizer(
        df['text'].tolist(),
        truncation=True,
        padding=True,
        max_length=max_length,
        return_tensors="pt"
    )

    labels = torch.tensor(df['label'].tolist(), dtype=torch.long)

    return encodings, labels


def get_num_labels() -> int:
    """返回类别数量"""
    return len(LABEL2ID)