from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.exchange.app_logger import logger


class SchedulerManager:

    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started.")

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped.")

    def add_job(self, func, trigger, **kwargs):
        try:
            job = self.scheduler.add_job(func, trigger, **kwargs)
            logger.info(f"Job {job.id} added successfully.")
            return job
        except Exception as e:
            logger.error(f"Failed to add job: {e}")
            return None

    def list_jobs(self):
        return self.scheduler.get_jobs()

    def remove_job(self, job_id):
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Job {job_id} removed successfully.")
        except Exception as e:
            logger.error(f"Failed to remove job {job_id}: {e}")
