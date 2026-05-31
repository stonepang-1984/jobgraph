"""Base crawler for people data collection."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from loguru import logger


@dataclass
class CrawlResult:
    """Result from crawling."""

    persons: list[dict] = field(default_factory=list)
    companies: list[dict] = field(default_factory=list)
    universities: list[dict] = field(default_factory=list)
    work_experiences: list[dict] = field(default_factory=list)
    educations: list[dict] = field(default_factory=list)
    relations: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class BaseCrawler(ABC):
    """Base class for data crawlers."""

    def __init__(self, source_name: str):
        self.source_name = source_name

    @abstractmethod
    def crawl_person(self, identifier: str) -> CrawlResult:
        """Crawl data for a single person."""
        pass

    @abstractmethod
    def search_person(self, name: str) -> list[dict]:
        """Search for persons by name."""
        pass

    def crawl_batch(self, identifiers: list[str]) -> CrawlResult:
        """Crawl data for multiple persons."""
        all_result = CrawlResult()

        for identifier in identifiers:
            try:
                result = self.crawl_person(identifier)
                all_result.persons.extend(result.persons)
                all_result.companies.extend(result.companies)
                all_result.universities.extend(result.universities)
                all_result.work_experiences.extend(result.work_experiences)
                all_result.educations.extend(result.educations)
                all_result.relations.extend(result.relations)
                all_result.errors.extend(result.errors)
            except Exception as e:
                logger.error(f"Failed to crawl {identifier}: {e}")
                all_result.errors.append(str(e))

        return all_result
