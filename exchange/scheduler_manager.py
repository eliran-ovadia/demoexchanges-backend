from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()


def start_scheduler():
    if not scheduler.running:
        scheduler.start()


def stop_scheduler():
    scheduler.shutdown()


def add_job(func, trigger, **kwargs):
    scheduler.add_job(func, trigger, **kwargs)
