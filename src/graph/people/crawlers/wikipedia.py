"""Wikipedia data crawler for people information."""

import hashlib
import re

import requests
from loguru import logger

from src.graph.people.crawlers.base import BaseCrawler, CrawlResult


class WikipediaCrawler(BaseCrawler):
    """Crawl people data from Wikipedia."""

    API_URL = "https://zh.wikipedia.org/w/api.php"
    EN_API_URL = "https://en.wikipedia.org/w/api.php"

    def __init__(self, language: str = "zh"):
        super().__init__("wikipedia")
        self.language = language
        self.api_url = self.API_URL if language == "zh" else self.EN_API_URL

    def search_person(self, name: str, limit: int = 10) -> list[dict]:
        """Search for persons on Wikipedia."""
        params = {
            "action": "query",
            "list": "search",
            "srsearch": f"{name} 人物",
            "srlimit": limit,
            "format": "json",
        }

        try:
            response = requests.get(self.api_url, params=params, timeout=10)
            data = response.json()

            results = []
            for item in data.get("query", {}).get("search", []):
                results.append(
                    {
                        "title": item["title"],
                        "snippet": item.get("snippet", ""),
                        "pageid": item["pageid"],
                    }
                )

            return results

        except Exception as e:
            logger.error(f"Wikipedia search failed: {e}")
            return []

    def crawl_person(self, identifier: str) -> CrawlResult:
        """Crawl person data from Wikipedia page."""
        result = CrawlResult()

        try:
            # Get page content
            page_data = self._get_page(identifier)
            if not page_data:
                result.errors.append(f"Page not found: {identifier}")
                return result

            # Extract infobox data
            infobox = self._extract_infobox(page_data.get("wikitext", ""))

            # Build person data
            person = self._build_person(identifier, page_data, infobox)
            if person:
                result.persons.append(person)

            # Extract companies/organizations
            companies = self._extract_companies(infobox)
            result.companies.extend(companies)

            # Extract universities
            universities = self._extract_universities(infobox)
            result.universities.extend(universities)

            # Extract work experiences
            work_exps = self._extract_work_experience(person, infobox, companies)
            result.work_experiences.extend(work_exps)

            # Extract education
            educations = self._extract_education(person, infobox, universities)
            result.educations.extend(educations)

        except Exception as e:
            logger.error(f"Failed to crawl person {identifier}: {e}")
            result.errors.append(str(e))

        return result

    def _get_page(self, title: str) -> dict | None:
        """Get Wikipedia page content."""
        params = {
            "action": "query",
            "titles": title,
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main",
            "format": "json",
        }

        try:
            response = requests.get(self.api_url, params=params, timeout=10)
            data = response.json()

            pages = data.get("query", {}).get("pages", {})
            for page_id, page in pages.items():
                if page_id != "-1":
                    revisions = page.get("revisions", [])
                    if revisions:
                        wikitext = revisions[0].get("slots", {}).get("main", {}).get("*", "")
                        return {
                            "title": page.get("title", ""),
                            "pageid": page_id,
                            "wikitext": wikitext,
                        }

            return None

        except Exception as e:
            logger.error(f"Failed to get page {title}: {e}")
            return None

    def _extract_infobox(self, wikitext: str) -> dict:
        """Extract infobox data from wikitext."""
        infobox = {}

        # Find infobox
        match = re.search(r"\{\{Infobox\s+person(.*?)\}\}", wikitext, re.DOTALL | re.IGNORECASE)
        if not match:
            match = re.search(r"\{\{infobox(.*?)\}\}", wikitext, re.DOTALL | re.IGNORECASE)

        if match:
            content = match.group(1)

            # Extract fields
            patterns = {
                "name": r"\|\s*名字\s*=\s*(.+?)(?:\n|\|)",
                "name_en": r"\|\s*英文名\s*=\s*(.+?)(?:\n|\|)",
                "birth_date": r"\|\s*出生日期\s*=\s*(.+?)(?:\n|\|)",
                "birth_place": r"\|\s*出生地點\s*=\s*(.+?)(?:\n|\|)",
                "nationality": r"\|\s*國籍\s*=\s*(.+?)(?:\n|\|)",
                "education": r"\|\s*教育程度\s*=\s*(.+?)(?:\n|\|)",
                "alma_mater": r"\|\s*母校\s*=\s*(.+?)(?:\n|\|)",
                "occupation": r"\|.*?職業\s*=\s*(.+?)(?:\n|\|)",
                "employer": r"\|\s*雇主\s*=\s*(.+?)(?:\n|\|)",
                "organization": r"\|\s*機構\s*=\s*(.+?)(?:\n|\|)",
                "title": r"\|\s*職位\s*=\s*(.+?)(?:\n|\|)",
            }

            for key, pattern in patterns.items():
                match = re.search(pattern, content)
                if match:
                    value = match.group(1).strip()
                    # Clean wikitext markup
                    value = re.sub(r"\[\[(.+?\|)?(.+?)\]\]", r"\2", value)
                    value = re.sub(r"\{\{.+?\}\}", "", value)
                    value = value.strip()
                    infobox[key] = value

        return infobox

    def _build_person(self, identifier: str, page_data: dict, infobox: dict) -> dict | None:
        """Build person dict from crawled data."""
        name = infobox.get("name") or page_data.get("title", "")
        if not name:
            return None

        person_id = hashlib.md5(name.encode()).hexdigest()[:16]

        return {
            "id": person_id,
            "name": name,
            "name_en": infobox.get("name_en"),
            "birth_date": infobox.get("birth_date"),
            "birth_place": infobox.get("birth_place"),
            "nationality": infobox.get("nationality"),
            "bio": page_data.get("wikitext", "")[:500],
            "source": "wikipedia",
            "source_url": f"https://{self.language}.wikipedia.org/wiki/{identifier}",
            "tags": self._extract_tags(infobox),
        }

    def _extract_tags(self, infobox: dict) -> list[str]:
        """Extract tags from infobox."""
        tags = []

        occupation = infobox.get("occupation", "")
        if occupation:
            tags.extend([t.strip() for t in re.split(r"[,、/]", occupation) if t.strip()])

        return tags[:5]

    def _extract_companies(self, infobox: dict) -> list[dict]:
        """Extract companies from infobox."""
        companies = []

        employer = infobox.get("employer", "")
        if employer:
            company_id = hashlib.md5(employer.encode()).hexdigest()[:16]
            companies.append(
                {
                    "id": company_id,
                    "name": employer,
                    "source": "wikipedia",
                }
            )

        organization = infobox.get("organization", "")
        if organization and organization != employer:
            org_id = hashlib.md5(organization.encode()).hexdigest()[:16]
            companies.append(
                {
                    "id": org_id,
                    "name": organization,
                    "source": "wikipedia",
                }
            )

        return companies

    def _extract_universities(self, infobox: dict) -> list[dict]:
        """Extract universities from infobox."""
        universities = []

        alma_mater = infobox.get("alma_mater", "")
        if alma_mater:
            # Split multiple universities
            for uni in re.split(r"[,、/]", alma_mater):
                uni = uni.strip()
                if uni:
                    uni_id = hashlib.md5(uni.encode()).hexdigest()[:16]
                    universities.append(
                        {
                            "id": uni_id,
                            "name": uni,
                            "source": "wikipedia",
                        }
                    )

        return universities

    def _extract_work_experience(self, person: dict, infobox: dict, companies: list[dict]) -> list[dict]:
        """Extract work experience relationships."""
        if not person or not companies:
            return []

        exps = []
        title = infobox.get("title", "")

        for company in companies:
            exps.append(
                {
                    "person_id": person["id"],
                    "company_id": company["id"],
                    "position": title or "成员",
                    "is_current": True,
                    "source": "wikipedia",
                }
            )

        return exps

    def _extract_education(self, person: dict, infobox: dict, universities: list[dict]) -> list[dict]:
        """Extract education relationships."""
        if not person or not universities:
            return []

        edus = []
        degree = infobox.get("education", "")

        for uni in universities:
            edus.append(
                {
                    "person_id": person["id"],
                    "university_id": uni["id"],
                    "degree": degree or None,
                    "source": "wikipedia",
                }
            )

        return edus


# Singleton instance
wikipedia_crawler = WikipediaCrawler()
