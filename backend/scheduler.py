import logging
from apscheduler.schedulers.background import BackgroundScheduler
from backend.pipeline import run_pipeline

logger = logging.getLogger(__name__)

# Initialize background scheduler instance
scheduler = BackgroundScheduler(daemon=True)


def scheduled_ingestion_job():
    """Wrapper function executed on timer by APScheduler."""
    logger.info("[Scheduler] Starting automatic background ingestion cycle...")
    try:
        metrics = run_pipeline()
        logger.info(f"[Scheduler] Background cycle complete: {metrics}")
    except Exception as e:
        logger.error(f"[Scheduler] Background cycle failed: {e}")


def start_scheduler(interval_hours: int = 1):
    """Starts the background scheduler thread."""
    if not scheduler.running:
        # Schedule periodic execution
        scheduler.add_job(
            scheduled_ingestion_job,
            trigger="interval",
            hours=interval_hours,
            id="job_pipeline_sync",
            replace_existing=True,
        )
        scheduler.start()
        logger.info(f"[Scheduler] Initialized. Running every {interval_hours} hour(s).")


def shutdown_scheduler():
    """Gracefully stops the scheduler thread on app shutdown."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[Scheduler] Shut down successfully.")