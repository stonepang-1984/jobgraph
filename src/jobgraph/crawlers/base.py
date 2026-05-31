"""Base crawler for job data collection."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from loguru import logger


@dataclass
class CrawlResult:
    """Result from crawling."""
    companies: list[dict] = field(default_factory=list)
    jobs: list[dict] = field(default_factory=list)
    reviews: list[dict] = field(default_factory=list)
    pitfalls: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class BaseCrawler(ABC):
    """Base class for data crawlers."""

    def __init__(self, source_name: str):
        self.source_name = source_name

    @abstractmethod
    def crawl_company(self, company_name: str) -> CrawlResult:
        """Crawl data for a single company."""
        pass

    @abstractmethod
    def search_companies(self, query: str, limit: int = 10) -> list[dict]:
        """Search for companies."""
        pass

    @abstractmethod
    def crawl_jobs(self, query: str, location: str = None, limit: int = 50) -> CrawlResult:
        """Crawl job listings."""
        pass

    def crawl_batch(self, company_names: list[str]) -> CrawlResult:
        """Crawl data for multiple companies."""
        all_result = CrawlResult()

        for name in company_names:
            try:
                result = self.crawl_company(name)
                all_result.companies.extend(result.companies)
                all_result.jobs.extend(result.jobs)
                all_result.reviews.extend(result.reviews)
                all_result.pitfalls.extend(result.pitfalls)
                all_result.errors.extend(result.errors)
            except Exception as e:
                logger.error(f"Failed to crawl {name}: {e}")
                all_result.errors.append(str(e))

        return all_result
