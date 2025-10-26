# scripts/scheduler.py
from apscheduler.schedulers.blocking import BlockingScheduler
from run_pipeline import run_pipeline
from datetime import datetime

sched = BlockingScheduler()

@sched.scheduled_job('cron', hour=6, minute=0)  # 每天早上6点
def timed_job():
    print(f"⏰ 定时任务触发: {datetime.now()}")
    run_pipeline()

print("📌 定时任务已启动，每天 6:00 执行")
sched.start()