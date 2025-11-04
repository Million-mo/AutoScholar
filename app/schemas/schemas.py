"""Pydantic schemas for data validation and serialization."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Paper Schemas
# ============================================================================


class PaperBase(BaseModel):
    """Base schema for paper data."""

    paper_id: str = Field(..., description="Unique paper identifier")
    title: str = Field(..., description="Paper title")
    authors: List[str] = Field(..., description="List of authors")
    abstract: str = Field(..., description="Paper abstract")
    publication_date: Optional[datetime] = Field(None, description="Publication date")
    source: str = Field(..., description="Source of the paper")
    pdf_url: Optional[str] = Field(None, description="PDF download link")
    categories: Optional[List[str]] = Field(None, description="Paper categories")
    raw_data: Dict[str, Any] = Field(..., description="Raw data from source")


class PaperCreate(PaperBase):
    """Schema for creating a new paper."""

    status: str = Field(default="NEW", description="Processing status")


class PaperUpdate(BaseModel):
    """Schema for updating a paper."""

    status: Optional[str] = Field(None, description="Processing status")
    model_config = ConfigDict(extra="forbid")


class PaperResponse(PaperBase):
    """Schema for paper response."""

    id: int = Field(..., description="Database ID")
    status: str = Field(..., description="Processing status")
    crawl_time: datetime = Field(..., description="Crawl timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Report Schemas
# ============================================================================


class ReportContentSchema(BaseModel):
    """Schema for structured report content."""

    core_summary: str = Field(..., description="Core summary (50-100 words)")
    research_background: str = Field(..., description="Research background (100-200 words)")
    technical_innovation: str = Field(
        ..., description="Technical innovation points (200-300 words)"
    )
    experiments_results: str = Field(
        ..., description="Experiments and results (150-250 words)"
    )
    application_value: str = Field(..., description="Application value (100-150 words)")
    limitations: str = Field(..., description="Limitations analysis (100-150 words)")
    recommended_audience: str = Field(
        ..., description="Recommended reading audience (< 50 words)"
    )


class ReportBase(BaseModel):
    """Base schema for report data."""

    paper_id: int = Field(..., description="Related paper ID")
    llm_provider: str = Field(..., description="LLM provider")
    llm_model: str = Field(..., description="LLM model name")
    report_content: Dict[str, Any] = Field(..., description="Structured report content")
    markdown_path: str = Field(..., description="Markdown file path")


class ReportCreate(ReportBase):
    """Schema for creating a new report."""

    generation_time: Optional[int] = Field(None, description="Generation time in seconds")
    token_usage: Optional[Dict[str, Any]] = Field(None, description="Token usage statistics")
    status: str = Field(default="PENDING", description="Generation status")


class ReportUpdate(BaseModel):
    """Schema for updating a report."""

    status: Optional[str] = Field(None, description="Generation status")
    error_message: Optional[str] = Field(None, description="Error message")
    model_config = ConfigDict(extra="forbid")


class ReportResponse(ReportBase):
    """Schema for report response."""

    id: int = Field(..., description="Database ID")
    generation_time: Optional[int] = Field(None, description="Generation time in seconds")
    token_usage: Optional[Dict[str, Any]] = Field(None, description="Token usage statistics")
    status: str = Field(..., description="Generation status")
    error_message: Optional[str] = Field(None, description="Error message")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Task Schemas
# ============================================================================


class TaskBase(BaseModel):
    """Base schema for task data."""

    task_type: str = Field(..., description="Task type")
    task_params: Optional[Dict[str, Any]] = Field(None, description="Task parameters")
    trigger_type: str = Field(..., description="Trigger type (SCHEDULED/MANUAL)")


class TaskCreate(TaskBase):
    """Schema for creating a new task."""

    status: str = Field(default="PENDING", description="Execution status")


class TaskUpdate(BaseModel):
    """Schema for updating a task."""

    status: Optional[str] = Field(None, description="Execution status")
    start_time: Optional[datetime] = Field(None, description="Task start time")
    end_time: Optional[datetime] = Field(None, description="Task end time")
    result_summary: Optional[Dict[str, Any]] = Field(None, description="Result summary")
    error_message: Optional[str] = Field(None, description="Error message")
    retry_count: Optional[int] = Field(None, description="Retry count")

    model_config = ConfigDict(extra="forbid")


class TaskResponse(TaskBase):
    """Schema for task response."""

    id: int = Field(..., description="Database ID")
    status: str = Field(..., description="Execution status")
    start_time: Optional[datetime] = Field(None, description="Task start time")
    end_time: Optional[datetime] = Field(None, description="Task end time")
    result_summary: Optional[Dict[str, Any]] = Field(None, description="Result summary")
    error_message: Optional[str] = Field(None, description="Error message")
    retry_count: int = Field(..., description="Retry count")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# API Request/Response Schemas
# ============================================================================


class GenerateReportRequest(BaseModel):
    """Request schema for generating a report."""

    paper_id: Optional[str] = Field(None, description="Specific paper ID to process")
    llm_provider: Optional[str] = Field(None, description="Preferred LLM provider")
    force_regenerate: bool = Field(
        default=False, description="Force regenerate even if report exists"
    )


class GenerateReportResponse(BaseModel):
    """Response schema for report generation."""

    task_id: int = Field(..., description="Task ID for tracking")
    message: str = Field(..., description="Response message")
    status: str = Field(..., description="Initial task status")


class CrawlPapersRequest(BaseModel):
    """Request schema for crawling papers."""

    source: str = Field(default="huggingface", description="Paper source to crawl")
    limit: Optional[int] = Field(None, description="Maximum number of papers to crawl")


class CrawlPapersResponse(BaseModel):
    """Response schema for paper crawling."""

    task_id: int = Field(..., description="Task ID for tracking")
    message: str = Field(..., description="Response message")
    status: str = Field(..., description="Initial task status")
