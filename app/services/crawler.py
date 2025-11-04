"""Hugging Face Daily Papers crawler service."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
import re

from app.core.logging import get_logger
from app.core.config import settings
from app.utils.retry import async_retry
from app.schemas.schemas import PaperCreate

logger = get_logger(__name__)


class HuggingFaceCrawler:
    """Crawler for Hugging Face Daily Papers."""

    BASE_URL = "https://huggingface.co/papers"

    def __init__(self) -> None:
        """Initialize the crawler."""
        self.client = httpx.AsyncClient(
            timeout=settings.crawler.timeout,
            headers={"User-Agent": settings.crawler.user_agent},
            follow_redirects=True,
        )

    async def __aenter__(self) -> "HuggingFaceCrawler":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()

    @async_retry(exceptions=(httpx.HTTPError, httpx.TimeoutException))
    async def fetch_daily_papers(self, date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch daily papers from Hugging Face.

        Args:
            date: Date string in format YYYY-MM-DD, defaults to today

        Returns:
            List of paper data dictionaries

        Raises:
            httpx.HTTPError: If HTTP request fails
        """
        url = self.BASE_URL
        if date:
            url = f"{self.BASE_URL}?date={date}"

        logger.info("Fetching Hugging Face daily papers", url=url)

        response = await self.client.get(url)
        response.raise_for_status()

        papers = await self._parse_papers_page(response.text)
        logger.info(
            "Fetched papers from Hugging Face", count=len(papers), url=url
        )

        return papers

    async def _parse_papers_page(self, html: str) -> List[Dict[str, Any]]:
        """Parse papers from HTML page.

        Args:
            html: HTML content of the page

        Returns:
            List of parsed paper data
        """
        soup = BeautifulSoup(html, "lxml")
        papers = []

        # Find all paper articles
        # Note: The actual selectors may need adjustment based on Hugging Face's HTML structure
        paper_articles = soup.find_all("article", class_=re.compile(r"paper"))

        if not paper_articles:
            # Fallback: try finding main content area
            paper_articles = soup.find_all("div", class_=re.compile(r"paper|card"))

        for article in paper_articles:
            try:
                paper_data = await self._parse_paper_article(article)
                if paper_data:
                    papers.append(paper_data)
            except Exception as e:
                logger.warning(
                    "Failed to parse paper article",
                    error=str(e),
                    exc_info=True,
                )
                continue

        return papers

    async def _parse_paper_article(
        self, article: BeautifulSoup
    ) -> Optional[Dict[str, Any]]:
        """Parse individual paper article.

        Args:
            article: BeautifulSoup article element

        Returns:
            Parsed paper data or None if parsing fails
        """
        try:
            # Extract paper ID from arXiv link
            arxiv_link = article.find("a", href=re.compile(r"arxiv\.org"))
            if not arxiv_link:
                return None

            arxiv_url = arxiv_link.get("href", "")
            paper_id_match = re.search(r"(\d{4}\.\d{4,5})", arxiv_url)
            if not paper_id_match:
                return None

            paper_id = paper_id_match.group(1)

            # Extract title
            title_elem = article.find("h3") or article.find("h2")
            title = title_elem.get_text(strip=True) if title_elem else ""

            # Extract authors
            authors_elem = article.find("p", class_=re.compile(r"author"))
            authors_text = authors_elem.get_text(strip=True) if authors_elem else ""
            authors = [a.strip() for a in authors_text.split(",") if a.strip()]

            # Extract abstract
            abstract_elem = article.find("p", class_=re.compile(r"abstract|description"))
            abstract = abstract_elem.get_text(strip=True) if abstract_elem else ""

            # Extract PDF URL
            pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"

            # Extract categories/tags
            categories = []
            tag_elems = article.find_all("span", class_=re.compile(r"tag|badge"))
            for tag_elem in tag_elems:
                tag_text = tag_elem.get_text(strip=True)
                if tag_text:
                    categories.append(tag_text)

            paper_data = {
                "paper_id": f"arxiv-{paper_id}",
                "title": title,
                "authors": authors if authors else ["Unknown"],
                "abstract": abstract or "No abstract available",
                "publication_date": datetime.now(),
                "source": "HUGGINGFACE",
                "pdf_url": pdf_url,
                "categories": categories if categories else None,
                "raw_data": {
                    "arxiv_id": paper_id,
                    "arxiv_url": arxiv_url,
                    "huggingface_url": self.BASE_URL,
                },
            }

            return paper_data

        except Exception as e:
            logger.error(
                "Error parsing paper article",
                error=str(e),
                exc_info=True,
            )
            return None

    def convert_to_paper_schema(self, paper_data: Dict[str, Any]) -> PaperCreate:
        """Convert raw paper data to PaperCreate schema.

        Args:
            paper_data: Raw paper data dictionary

        Returns:
            PaperCreate schema instance
        """
        return PaperCreate(**paper_data)


async def crawl_huggingface_papers(
    date: Optional[str] = None, limit: Optional[int] = None
) -> List[PaperCreate]:
    """Crawl papers from Hugging Face.

    Args:
        date: Optional date string (YYYY-MM-DD)
        limit: Maximum number of papers to return

    Returns:
        List of PaperCreate schemas
    """
    async with HuggingFaceCrawler() as crawler:
        raw_papers = await crawler.fetch_daily_papers(date)

        if limit:
            raw_papers = raw_papers[:limit]

        papers = [crawler.convert_to_paper_schema(p) for p in raw_papers]

        return papers
