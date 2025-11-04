"""Task model - represents scheduled and manual tasks."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, JSON, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class Task(Base):
    """Task model for tracking task execution."""

    __tablename__ = "tasks"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Task information
    task_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Task type (CRAWL, GENERATE_BATCH, GENERATE_SINGLE, CLEANUP, etc.)",
    )
    task_params: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, comment="Task parameters"
    )

    # Execution information
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING",
        index=True,
        comment="Execution status (PENDING, RUNNING, SUCCESS, FAILED)",
    )
    trigger_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Trigger type (SCHEDULED, MANUAL)",
    )

    # Timing information
    start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="Task start time"
    )
    end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="Task end time"
    )

    # Results and error handling
    result_summary: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, comment="Execution result summary"
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Error message if task failed"
    )
    retry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Number of retry attempts"
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
        Index("idx_task_type_status", "task_type", "status"),
        Index("idx_task_created_at", "created_at"),
        Index("idx_task_trigger_type", "trigger_type"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Task(id={self.id}, task_type={self.task_type}, status={self.status}, trigger_type={self.trigger_type})>"
