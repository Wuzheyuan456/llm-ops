# src/evaluate.py（部分更新）
from sklearn.metrics import roc_curve, auc
from sklearn.preprocessing import label_binarize
import matplotlib.pyplot as plt
import torch
import numpy as np
from data import ID2LABEL
import mlflow

def evaluate_model(model, dataloader, device, num_labels=5):
    model.eval()
    all_logits = []
    all_labels = []

    with torch.no_grad():
        for batch in dataloader:
            # print(type(batch))  # 看看到底是什么
            # print(batch)  # 打印结构
            input_ids = batch[0].to(device)  # 原来是 batch['input_ids']
            attention_mask = batch[1].to(device)  # 原来是 batch['attention_mask']
            labels = batch[2].to(device)  # 原来是 batch['labels']
            # input_ids = batch['input_ids'].to(device)
            # attention_mask = batch['attention_mask'].to(device)
            # labels = batch['labels'].to(device)

            outputs = model(input_ids, attention_mask)
            all_logits.append(outputs.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    # 合并 logits
    all_logits = np.vstack(all_logits)
    all_probs = torch.softmax(torch.tensor(all_logits), dim=1).numpy()

    # 独热编码标签
    y_test_bin = label_binarize(all_labels, classes=list(range(num_labels)))

    # 计算每个类的 AUC
    fpr = dict()
    tpr = dict()
    roc_auc = dict()
    for i in range(num_labels):
        fpr[i], tpr[i], _ = roc_curve(y_test_bin[:, i], all_probs[:, i])
        roc_auc[i] = auc(fpr[i], tpr[i])

    # 平均 AUC
    auc_macro = np.mean(list(roc_auc.values()))

    # 绘图
    plt.figure(figsize=(8, 6))
    for i, label_name in ID2LABEL.items():
        plt.plot(fpr[i], tpr[i], lw=2, label=f'{label_name} (AUC = {roc_auc[i]:.2f})')

    plt.plot([0, 1], [0, 1], 'k--', lw=1)
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(f'Multi-class ROC Curve (Macro AUC = {auc_macro:.2f})')
    plt.legend(loc='lower right', fontsize='small')
    roc_path = "reports/roc_curve.png"
    plt.savefig(roc_path, dpi=300, bbox_inches='tight')
    plt.close()

    # MLflow 记录
    mlflow.log_metric("test_auc_macro", auc_macro)
    for i in range(num_labels):
        mlflow.log_metric(f"test_auc_{ID2LABEL[i]}", roc_auc[i])
    mlflow.log_artifact(roc_path)

    return auc_macro