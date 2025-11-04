"""Markdown document generation service."""

from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import re
from jinja2 import Template

from app.core.logging import get_logger
from app.core.config import settings
from app.utils.datetime_utils import format_datetime

logger = get_logger(__name__)


class MarkdownGenerator:
    """Generator for Markdown analysis reports."""

    TEMPLATE = """---
title: "{{ title }}"
date: {{ date }}
paper_id: "{{ paper_id }}"
tags: {{ tags }}
author: "AutoScholar"
llm_model: "{{ llm_model }}"
publish_status: "unpublished"
---

# {{ title }}

## 📋 论文信息

- **标题**: {{ title }}
- **作者**: {{ authors }}
- **发布日期**: {{ publication_date }}
- **来源**: {{ source }}
- **分类**: {{ categories }}
{% if pdf_url %}
- **论文链接**: [PDF]({{ pdf_url }})
{% endif %}

---

## 🎯 核心观点

{{ report_content.core_summary }}

---

## 📖 研究背景

{{ report_content.research_background }}

---

## 💡 技术创新点

{{ report_content.technical_innovation }}

---

## 🔬 实验与结果

{{ report_content.experiments_results }}

---

## 🌟 应用价值

{{ report_content.application_value }}

---

## ⚠️ 局限性分析

{{ report_content.limitations }}

---

## 👥 推荐阅读人群

{{ report_content.recommended_audience }}

---

## 📝 原始摘要

{{ abstract }}

---

*本报告由 AutoScholar 自动生成，使用 {{ llm_model }} 模型*

*生成时间: {{ generation_time }}*
"""

    def __init__(self) -> None:
        """Initialize Markdown generator."""
        self.template = Template(self.TEMPLATE)

    def generate_filename(
        self, paper_id: str, title: str, publication_date: Optional[datetime] = None
    ) -> str:
        """Generate filename for the Markdown document.

        Args:
            paper_id: Paper identifier
            title: Paper title
            publication_date: Paper publication date

        Returns:
            Generated filename
        """
        # Use publication date or current date
        date = publication_date or datetime.now()
        date_str = date.strftime("%Y%m%d")

        # Clean paper ID
        clean_paper_id = re.sub(r"[^\w\-]", "_", paper_id)

        # Extract keywords from title (first 3 words, max 30 chars)
        title_words = re.findall(r"\w+", title.lower())
        keywords = "_".join(title_words[:3])[:30]

        filename = f"{date_str}_{clean_paper_id}_{keywords}.md"

        return filename

    def generate_filepath(
        self, filename: str, publication_date: Optional[datetime] = None
    ) -> Path:
        """Generate full filepath for the Markdown document.

        Args:
            filename: Filename
            publication_date: Publication date for directory structure

        Returns:
            Full file path
        """
        date = publication_date or datetime.now()
        year = str(date.year)
        month = f"{date.month:02d}"

        # Create directory structure: reports/YYYY/MM/
        report_dir = settings.storage.reports_path / year / month
        report_dir.mkdir(parents=True, exist_ok=True)

        return report_dir / filename

    def generate_markdown(
        self,
        paper_data: Dict[str, Any],
        report_content: Dict[str, str],
        llm_model: str,
    ) -> str:
        """Generate Markdown content from paper data and report.

        Args:
            paper_data: Paper metadata
            report_content: Generated report content
            llm_model: LLM model used for generation

        Returns:
            Generated Markdown content
        """
        # Format authors
        authors_str = ", ".join(paper_data.get("authors", []))

        # Format date
        date_str = format_datetime(datetime.now(), "%Y-%m-%d")
        pub_date_str = "未知"
        if paper_data.get("publication_date"):
            pub_date_str = format_datetime(
                paper_data["publication_date"], "%Y-%m-%d"
            )

        # Format categories
        categories = paper_data.get("categories", [])
        categories_str = ", ".join(categories) if categories else "未分类"

        # Format tags for YAML front matter
        tags = categories if categories else ["AI", "Machine Learning"]
        tags_str = str(tags)

        # Render template
        markdown_content = self.template.render(
            title=paper_data.get("title", "未知标题"),
            date=date_str,
            paper_id=paper_data.get("paper_id", "unknown"),
            tags=tags_str,
            llm_model=llm_model,
            authors=authors_str,
            publication_date=pub_date_str,
            source=paper_data.get("source", "未知"),
            categories=categories_str,
            pdf_url=paper_data.get("pdf_url", ""),
            abstract=paper_data.get("abstract", ""),
            report_content=report_content,
            generation_time=date_str,
        )

        return markdown_content

    def save_markdown(
        self, content: str, filepath: Path
    ) -> Path:
        """Save Markdown content to file.

        Args:
            content: Markdown content
            filepath: File path to save to

        Returns:
            Path to saved file
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info("Saved Markdown report", filepath=str(filepath))

        return filepath


async def create_markdown_report(
    paper_data: Dict[str, Any],
    report_content: Dict[str, str],
    llm_model: str,
) -> Dict[str, Any]:
    """Create and save Markdown report.

    Args:
        paper_data: Paper metadata
        report_content: Generated report content
        llm_model: LLM model used

    Returns:
        Dictionary with filepath and other metadata
    """
    generator = MarkdownGenerator()

    # Generate filename and filepath
    filename = generator.generate_filename(
        paper_id=paper_data["paper_id"],
        title=paper_data["title"],
        publication_date=paper_data.get("publication_date"),
    )

    filepath = generator.generate_filepath(
        filename=filename,
        publication_date=paper_data.get("publication_date"),
    )

    # Generate Markdown content
    markdown_content = generator.generate_markdown(
        paper_data=paper_data,
        report_content=report_content,
        llm_model=llm_model,
    )

    # Save to file
    saved_path = generator.save_markdown(markdown_content, filepath)

    logger.info(
        "Created Markdown report",
        paper_id=paper_data["paper_id"],
        filepath=str(saved_path),
    )

    return {
        "filepath": str(saved_path),
        "filename": filename,
        "content_length": len(markdown_content),
    }
