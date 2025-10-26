# airflow_dags/train_nlp_model.py
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from src.train import train

default_args = {
    'owner': 'ml-team',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'nlp_model_training',
    default_args=default_args,
    description='每周训练NLP模型，支持回滚',
    schedule_interval='0 0 * * 1',  # 每周一 00:00
    start_date=datetime(2025, 1, 1),
    catchup=False,
)

task = PythonOperator(
    task_id='train_model',
    python_callable=train,
    dag=dag,
)