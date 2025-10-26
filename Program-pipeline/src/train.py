# src/train.py
import os
import torch
import mlflow
import hashlib
import yaml
from torch.utils.data import DataLoader, TensorDataset
from data import load_data, tokenize_data
from model import SimpleClassifier
from evaluate import evaluate_model
import os
import shutil
import subprocess
def run_dvc_cmd(cmd):
    os.environ['GIT_TRACE'] = '1'  # 看 Git 内部执行流
    os.environ['GIT_TRACE_SETUP'] = '1'  # 看工作区/仓库路径
    print('which git  :', shutil.which('git'))
    print('cwd        :', os.getcwd())
    print('exists Git :', os.path.exists(shutil.which('git')))
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f'>>> {cmd}')
    print(f'  returncode : {result.returncode}')
    print(f'  stdout     : {repr(result.stdout)}')
    print(f'  stderr     : {repr(result.stderr)}')
    if result.returncode != 0:
        raise Exception(f"Command failed: {cmd}\n{result.stderr}")
    print(result.stdout)
# def run_dvc_cmd(cmd):
#     # 用 bash 登录模式，加载 /etc/profile 和 ~/.bashrc
#     result = subprocess.run(
#         ['bash', '-l', '-c', cmd],
#         capture_output=True,
#         text=True,
#         cwd='/media/administrator/Data2/wzy/xx/llm-ops'
#     )
#     print('>>>', cmd)
#     print('returncode:', result.returncode)
#     print('stdout:', repr(result.stdout))
#     print('stderr:', repr(result.stderr))
#     if result.returncode != 0:
#         raise Exception(f"Command failed: {cmd}\n{result.stderr}")
#     print(result.stdout)

def check_data_changed():
    """检查 DVC 数据是否有更新"""
    result = subprocess.run("dvc status", shell=True, capture_output=True, text=True)
    if "new" in result.stdout or "modified" in result.stdout:
        print("✅ Data has changed, proceed with training.")
        return True
    else:
        print("🚫 No data change detected, skip training.")
        return False

def train():
    # --- 1. 检查数据是否更新 ---
    if not check_data_changed():
        return {"status": "skipped", "reason": "no_data_change"}

    # --- 2. 加载参数 ---
    with open("params.yaml") as f:
        params = yaml.safe_load(f)

    model_name = params['model']['name']
    num_labels = params['model']['num_labels']
    epochs = params['training']['epochs']
    batch_size = params['training']['batch_size']
    lr = params['training']['learning_rate']
    max_length = params['data']['max_length']

    # --- 3. 准备数据 ---
    df = load_data(params['data']['path'])
    encodings, labels = tokenize_data(df, model_name, max_length)

    dataset = TensorDataset(
        encodings['input_ids'],
        encodings['attention_mask'],
        labels
    )
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # --- 4. 设置设备 ---
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # --- 5. 加载模型（支持增量训练）---
    model_path = "models/latest_model.pth"
    if os.path.exists(model_path):
        print(f"🔁 Loading existing model from {model_path}")
        model = SimpleClassifier(model_name, num_labels)
        model.load_state_dict(torch.load(model_path))
    else:
        print("🆕 Initializing new model")
        model = SimpleClassifier(model_name, num_labels)
    model.to(device)
    lr = float(lr)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    # --- 6. MLflow 开始记录 ---
    mlflow.set_tracking_uri("file:./mlruns")  # 本地
    mlflow.set_experiment("nlp-text-classification")

    with mlflow.start_run() as run:
        # 记录参数
        mlflow.log_params({
            "model_name": model_name,
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": lr,
            "max_length": max_length
        })

        # 训练循环
        for epoch in range(epochs):

            model.train()
            total_loss = 0
            for batch in dataloader:
                #print(batch)
                input_ids = batch[0].to(device)
                attention_mask = batch[1].to(device)
                labels = batch[2].to(device)

                optimizer.zero_grad()
                outputs = model(input_ids, attention_mask)
                loss = torch.nn.functional.cross_entropy(outputs, labels)
                loss.backward()
                optimizer.step()

                total_loss += loss.item()

            avg_loss = total_loss / len(dataloader)
            mlflow.log_metric("loss", avg_loss, step=epoch)
            print(f"epoch[{epoch}] avg_loss[{avg_loss}]")
        # --- 7. 评估模型 ---
        test_dataloader = DataLoader(dataset, batch_size=batch_size)  # 简化：用全量数据评估
        auc_score = evaluate_model(model, test_dataloader, device)

        # --- 8. 模型门禁：AUC < 0.8 不保存 ---
        if auc_score < 0.8:
            print(f"❌ AUC={auc_score:.3f} < 0.8, skipping model save and DVC commit.")
            return {"status": "rejected", "auc": auc_score}

        # --- 9. 保存模型 + 计算 MD5 ---
        torch.save(model.state_dict(), model_path)
        hash_md5 = hashlib.md5()
        with open(model_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        model_md5 = hash_md5.hexdigest()
        with open("models/latest_model.md5", "w") as f:
            f.write(model_md5)

        mlflow.log_metric("final_auc", auc_score)
        mlflow.log_param("model_md5", model_md5)
        mlflow.pytorch.log_model(model, "model")  # 保存模型到 MLflow

        # --- 10. 注册模型到 MLflow Model Registry ---
        model_uri = f"runs:/{run.info.run_id}/model"
        registered_model_name = "NLPTextClassifier"
        try:
            mlflow.register_model(model_uri, registered_model_name)
        except Exception as e:
            print(f"Model may already exist: {e}")

        print(f"✅ Model trained, AUC={auc_score:.3f}, MD5={model_md5}")

        # --- 11. DVC 提交 ---
        run_dvc_cmd("dvc add models/latest_model.pth")
        run_dvc_cmd("dvc add models/latest_model.md5")
        run_dvc_cmd("dvc add reports/roc_curve.png")
        os.system(f'git commit -m "feat: trained model with AUC={auc_score:.3f}, MD5={model_md5}" --no-verify')  # 跳过钩子
        # run_dvc_cmd("git add models/latest_model.pth.dvc models/latest_model.md5.dvc reports/roc_curve.png.dvc params.yaml")
        # run_dvc_cmd("git add models/latest_model.pth.dvc models/latest_model.md5.dvc reports/roc_curve.png.dvc")
        # run_dvc_cmd(f'git commit -m "feat: trained model with AUC={auc_score:.3f}, MD5={model_md5}"')

        return {"status": "success", "auc": auc_score, "md5": model_md5}

if __name__ == '__main__':
    train()