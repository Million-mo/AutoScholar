"""Orchestration service for coordinating paper processing workflows."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.logging import get_logger
from app.models.paper import Paper
from app.models.report import Report
from app.models.task import Task
from app.schemas.schemas import PaperCreate, ReportCreate
from app.services.crawler import crawl_huggingface_papers
from app.services.llm_service import generate_paper_report
from app.services.document_generator import create_markdown_report

logger = get_logger(__name__)


class PaperOrchestrator:
    """Orchestrates paper crawling, analysis, and report generation."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize orchestrator.

        Args:
            db: Database session
        """
        self.db = db

    async def crawl_and_save_papers(
        self,
        source: str = "huggingface",
        date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Crawl papers and save to database.

        Args:
            source: Paper source to crawl
            date: Optional date for crawling
            limit: Maximum number of papers

        Returns:
            Dictionary with crawl results
        """
        logger.info("Starting paper crawl", source=source, date=date, limit=limit)

        # Crawl papers
        if source == "huggingface":
            papers = await crawl_huggingface_papers(date=date, limit=limit)
        else:
            raise ValueError(f"Unsupported source: {source}")

        # Save to database with deduplication
        saved_count = 0
        duplicate_count = 0
        failed_count = 0

        for paper_data in papers:
            try:
                # Check if paper already exists
                result = await self.db.execute(
                    select(Paper).where(Paper.paper_id == paper_data.paper_id)
                )
                existing_paper = result.scalar_one_or_none()

                if existing_paper:
                    duplicate_count += 1
                    logger.debug(
                        "Paper already exists",
                        paper_id=paper_data.paper_id,
                    )
                    continue

                # Create new paper
                paper = Paper(
                    paper_id=paper_data.paper_id,
                    title=paper_data.title,
                    authors=paper_data.authors,
                    abstract=paper_data.abstract,
                    publication_date=paper_data.publication_date,
                    source=paper_data.source,
                    pdf_url=paper_data.pdf_url,
                    categories=paper_data.categories,
                    raw_data=paper_data.raw_data,
                    status="NEW",
                )

                self.db.add(paper)
                await self.db.flush()
                saved_count += 1

                logger.info(
                    "Saved new paper",
                    paper_id=paper_data.paper_id,
                    title=paper_data.title[:50],
                )

            except Exception as e:
                failed_count += 1
                logger.error(
                    "Failed to save paper",
                    paper_id=paper_data.paper_id,
                    error=str(e),
                    exc_info=True,
                )

        await self.db.commit()

        result = {
            "total_crawled": len(papers),
            "saved": saved_count,
            "duplicates": duplicate_count,
            "failed": failed_count,
        }

        logger.info("Paper crawl completed", **result)
        return result

    async def generate_reports_batch(
        self,
        llm_provider: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate reports for unprocessed papers.

        Args:
            llm_provider: Optional LLM provider to use
            limit: Maximum number of papers to process

        Returns:
            Dictionary with generation results
        """
        logger.info("Starting batch report generation", llm_provider=llm_provider, limit=limit)

        # Query unprocessed papers
        query = select(Paper).where(Paper.status == "NEW")
        if limit:
            query = query.limit(limit)

        result = await self.db.execute(query)
        papers = result.scalars().all()

        if not papers:
            logger.info("No unprocessed papers found")
            return {"total_processed": 0, "success": 0, "failed": 0}

        success_count = 0
        failed_count = 0

        for paper in papers:
            try:
                await self._generate_single_report(paper, llm_provider)
                success_count += 1
            except Exception as e:
                failed_count += 1
                logger.error(
                    "Failed to generate report for paper",
                    paper_id=paper.paper_id,
                    error=str(e),
                    exc_info=True,
                )
                # Update paper status to FAILED
                paper.status = "FAILED"

        await self.db.commit()

        result = {
            "total_processed": len(papers),
            "success": success_count,
            "failed": failed_count,
        }

        logger.info("Batch report generation completed", **result)
        return result

    async def _generate_single_report(
        self,
        paper: Paper,
        llm_provider: Optional[str] = None,
    ) -> Report:
        """Generate report for a single paper.

        Args:
            paper: Paper model instance
            llm_provider: Optional LLM provider

        Returns:
            Created Report instance
        """
        logger.info(
            "Generating report for paper",
            paper_id=paper.paper_id,
            title=paper.title[:50],
        )

        # Update paper status
        paper.status = "PROCESSING"
        await self.db.flush()

        try:
            # Prepare paper data
            paper_data = {
                "paper_id": paper.paper_id,
                "title": paper.title,
                "authors": paper.authors,
                "abstract": paper.abstract,
                "publication_date": paper.publication_date,
                "source": paper.source,
                "pdf_url": paper.pdf_url,
                "categories": paper.categories,
            }

            # Generate report with LLM
            llm_result = await generate_paper_report(
                paper_data=paper_data,
                provider=llm_provider,
            )

            # Create Markdown document
            doc_result = await create_markdown_report(
                paper_data=paper_data,
                report_content=llm_result["content"],
                llm_model=llm_result["llm_model"],
            )

            # Save report to database
            report = Report(
                paper_id=paper.id,
                llm_provider=llm_result["llm_provider"],
                llm_model=llm_result["llm_model"],
                report_content=llm_result["content"],
                markdown_path=doc_result["filepath"],
                generation_time=llm_result.get("generation_time"),
                token_usage=llm_result.get("token_usage"),
                status="SUCCESS",
            )

            self.db.add(report)

            # Update paper status
            paper.status = "COMPLETED"

            await self.db.flush()

            logger.info(
                "Report generated successfully",
                paper_id=paper.paper_id,
                report_id=report.id,
                filepath=doc_result["filepath"],
            )

            return report

        except Exception as e:
            # Update paper status to FAILED
            paper.status = "FAILED"
            await self.db.flush()

            logger.error(
                "Failed to generate report",
                paper_id=paper.paper_id,
                error=str(e),
                exc_info=True,
            )
            raise

    async def regenerate_report(
        self,
        paper_id: str,
        llm_provider: Optional[str] = None,
    ) -> Report:
        """Regenerate report for a specific paper.

        Args:
            paper_id: Paper identifier
            llm_provider: Optional LLM provider

        Returns:
            Created Report instance

        Raises:
            ValueError: If paper not found
        """
        # Find paper
        result = await self.db.execute(
            select(Paper).where(Paper.paper_id == paper_id)
        )
        paper = result.scalar_one_or_none()

        if not paper:
            raise ValueError(f"Paper not found: {paper_id}")

        # Generate new report
        report = await self._generate_single_report(paper, llm_provider)
        await self.db.commit()

        return report
