from apscheduler.schedulers.background import BackgroundScheduler

from exchange.app_logger import logger

scheduler = BackgroundScheduler()


def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started.")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped.")


def add_job(func, trigger, **kwargs):
    try:
        job = scheduler.add_job(func, trigger, **kwargs)
        logger.info(f"Job {job.id} added successfully.")
        return job
    except Exception as e:
        logger.error(f"Failed to add job: {e}")
        return None


def list_jobs():
    return scheduler.get_jobs()


def remove_job(job_id):
    try:
        scheduler.remove_job(job_id)
        logger.info(f"Job {job_id} removed successfully.")
    except Exception as e:
        logger.error(f"Failed to remove job {job_id}: {e}")
