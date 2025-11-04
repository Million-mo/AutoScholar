"""Report model - represents generated analysis reports."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, JSON, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Report(Base):
    """Report model for storing generated paper analysis reports."""

    __tablename__ = "reports"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to paper
    paper_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Related paper ID",
    )

    # LLM information
    llm_provider: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="LLM provider (openai, qwen, etc.)"
    )
    llm_model: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="LLM model name"
    )

    # Report content
    report_content: Mapped[dict] = mapped_column(
        JSON, nullable=False, comment="Structured report content"
    )
    markdown_path: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="Path to generated Markdown file"
    )

    # Generation metrics
    generation_time: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Generation time in seconds"
    )
    token_usage: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, comment="Token usage statistics"
    )

    # Status and error handling
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
        index=True,
        comment="Generation status (PENDING, SUCCESS, FAILED)",
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Error message if generation failed"
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
        Index("idx_report_paper_id", "paper_id"),
        Index("idx_report_status", "status"),
        Index("idx_report_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Report(id={self.id}, paper_id={self.paper_id}, llm_model={self.llm_model}, status={self.status})>"
