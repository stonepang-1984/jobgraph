"""Import generated job data into the knowledge graph."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.jobgraph.graph_manager import job_manager
from src.jobgraph.crawlers.data_generator import generate_all_data


def import_generated_data(
    company_count: int = 50,
    jobs_per_company: int = 5,
    reviews_per_company: int = 5
):
    """Import generated data into Neo4j."""
    logger.info("=" * 60)
    logger.info("Importing Generated Job Data")
    logger.info("=" * 60)

    # Generate data
    companies, jobs, reviews, pitfalls = generate_all_data(
        company_count=company_count,
        jobs_per_company=jobs_per_company,
        reviews_per_company=reviews_per_company
    )

    # Import companies
    logger.info(f"Importing {len(companies)} companies...")
    for company in companies:
        try:
            job_manager.create_company(company)
        except Exception as e:
            logger.error(f"Failed to import company {company.name}: {e}")

    # Import jobs
    logger.info(f"Importing {len(jobs)} jobs...")
    for job in jobs:
        try:
            job_manager.create_job(job)
        except Exception as e:
            logger.error(f"Failed to import job {job.title}: {e}")

    # Import reviews
    logger.info(f"Importing {len(reviews)} reviews...")
    for review in reviews:
        try:
            job_manager.create_review(review)
        except Exception as e:
            logger.error(f"Failed to import review: {e}")

    # Import pitfalls
    logger.info(f"Importing {len(pitfalls)} pitfalls...")
    for pitfall in pitfalls:
        try:
            job_manager.create_pitfall(pitfall)
        except Exception as e:
            logger.error(f"Failed to import pitfall: {e}")

    # Print statistics
    stats = job_manager.get_stats()
    logger.info("\n" + "=" * 60)
    logger.info("Import Complete!")
    logger.info("=" * 60)
    logger.info(f"Companies: {stats.get('companies', 0)}")
    logger.info(f"Jobs: {stats.get('jobs', 0)}")
    logger.info(f"Reviews: {stats.get('reviews', 0)}")
    logger.info(f"Pitfalls: {stats.get('pitfalls', 0)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Import generated job data")
    parser.add_argument("--companies", type=int, default=50, help="Number of companies")
    parser.add_argument("--jobs", type=int, default=5, help="Jobs per company")
    parser.add_argument("--reviews", type=int, default=5, help="Reviews per company")
    args = parser.parse_args()

    import_generated_data(
        company_count=args.companies,
        jobs_per_company=args.jobs,
        reviews_per_company=args.reviews
    )
