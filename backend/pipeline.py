import logging
from backend.database import init_db, upsert_job
from backend.scraper import scrape_remote_jobs
from backend.schemas import JobCreate

# Configure logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def run_pipeline() -> dict:
    """
    Executes the ingestion pipeline:
    1. Ensures DB schema is initialized.
    2. Scrapes job listings.
    3. Validates records via Pydantic.
    4. Upserts records (deduplication check via SHA-256).
    5. Returns execution metrics.
    """
    logger.info("Initializing database...")
    init_db()

    logger.info("Starting scraper engine...")
    scraped_data = scrape_remote_jobs()
    total_fetched = len(scraped_data)
    logger.info(f"Fetched {total_fetched} raw listings.")

    inserted_count = 0
    updated_count = 0
    validation_failures = 0

    for raw_job in scraped_data:
        try:
            # Enforce schema validation
            validated_job = JobCreate(**raw_job)

            # Upsert into database (Standout Deduplication)
            result = upsert_job(validated_job.model_dump())
            if result == "inserted":
                inserted_count += 1
            elif result == "updated":
                updated_count += 1

        except Exception as err:
            logger.warning(f"Validation or write failure for {raw_job.get('title')}: {err}")
            validation_failures += 1

    metrics = {
        "total_fetched": total_fetched,
        "newly_inserted": inserted_count,
        "duplicates_updated": updated_count,
        "validation_failures": validation_failures,
    }

    logger.info(f"Pipeline run finished: {metrics}")
    return metrics


if __name__ == "__main__":
    run_pipeline()