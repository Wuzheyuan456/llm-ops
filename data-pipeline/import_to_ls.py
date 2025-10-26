# label_studio/import_to_ls.py
import label_studio_sdk
import os
import json

# 连接到 Label Studio
client = label_studio_sdk.Client('http://localhost:8080', r'4a337092f603b7a1de8d7e2c3ca05acf0ccda653')  # 在 LS 设置中生成 API Key
print('API 版本:', client.get_versions())     # 先测通
#print(client.list_projects())
# 选择项目（先手动创建一个）
project = client.get_project(2)               # 再拿项目



def import_to_label_studio(cleaned_file):
    with open(cleaned_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 构造导入数据
    tasks = []
    for item in data:
        tasks.append({
            "data": {
                "title": item["title"],
                "content": item["content"],
                "url": item["url"]
            }
        })

    # 导入
    project.import_tasks(tasks)
    print(f"✅ 已导入 {len(tasks)} 条数据到 Label Studio")


if __name__ == '__main__':
    import_to_label_studio(cleaned_file="./processor/data/cleaned/notices_clean_latest.json")