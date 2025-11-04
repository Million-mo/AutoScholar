"""Paper model - represents academic papers."""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, DateTime, JSON, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class Paper(Base):
    """Paper model for storing academic paper metadata."""

    __tablename__ = "papers"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Paper identification
    paper_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True, comment="Unique paper identifier (e.g., arXiv ID)"
    )

    # Paper metadata
    title: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="Paper title"
    )
    authors: Mapped[List[str]] = mapped_column(
        JSON, nullable=False, comment="List of authors"
    )
    abstract: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Paper abstract"
    )
    publication_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="Publication date"
    )

    # Source information
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="Source (HUGGINGFACE, ARXIV, etc.)"
    )
    pdf_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="PDF download link"
    )
    categories: Mapped[Optional[List[str]]] = mapped_column(
        JSON, nullable=True, comment="Paper categories/tags"
    )

    # Raw data and metadata
    raw_data: Mapped[dict] = mapped_column(
        JSON, nullable=False, comment="Raw data backup from source"
    )
    crawl_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), comment="Crawl timestamp"
    )

    # Processing status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="NEW",
        index=True,
        comment="Processing status (NEW, PROCESSING, COMPLETED, FAILED)",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), comment="Creation timestamp"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Update timestamp",
    )

    # Indexes
    __table_args__ = (
        Index("idx_paper_source_status", "source", "status"),
        Index("idx_paper_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Paper(id={self.id}, paper_id={self.paper_id}, title={self.title[:50]}...)>"
