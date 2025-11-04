"""API routes for paper processing and report generation."""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.config import settings
from app.core.logging import get_logger
from app.models.paper import Paper
from app.models.report import Report
from app.models.task import Task as TaskModel
from app.schemas.schemas import (
    PaperResponse,
    ReportResponse,
    TaskResponse,
    GenerateReportRequest,
    GenerateReportResponse,
    CrawlPapersRequest,
    CrawlPapersResponse,
)
from app.services.orchestrator import PaperOrchestrator

logger = get_logger(__name__)
router = APIRouter()


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> None:
    """Verify API key for protected endpoints.

    Args:
        x_api_key: API key from header

    Raises:
        HTTPException: If API key is invalid
    """
    if not settings.api.api_key:
        # API key not configured, allow access
        return

    if x_api_key != settings.api.api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")


# ============================================================================
# Paper Endpoints
# ============================================================================


@router.get("/papers", response_model=List[PaperResponse])
async def list_papers(
    skip: int = 0,
    limit: int = 20,
    source: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> List[PaperResponse]:
    """List papers with pagination and filters.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        source: Filter by source
        status: Filter by status
        db: Database session

    Returns:
        List of papers
    """
    query = select(Paper).order_by(desc(Paper.created_at))

    if source:
        query = query.where(Paper.source == source)
    if status:
        query = query.where(Paper.status == status)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    papers = result.scalars().all()

    return [PaperResponse.model_validate(paper) for paper in papers]


@router.get("/papers/{paper_id}", response_model=PaperResponse)
async def get_paper(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
) -> PaperResponse:
    """Get a specific paper by ID.

    Args:
        paper_id: Paper identifier
        db: Database session

    Returns:
        Paper details

    Raises:
        HTTPException: If paper not found
    """
    result = await db.execute(
        select(Paper).where(Paper.paper_id == paper_id)
    )
    paper = result.scalar_one_or_none()

    if not paper:
        raise HTTPException(status_code=404, detail=f"Paper not found: {paper_id}")

    return PaperResponse.model_validate(paper)


# ============================================================================
# Report Endpoints
# ============================================================================


@router.get("/reports", response_model=List[ReportResponse])
async def list_reports(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> List[ReportResponse]:
    """List reports with pagination and filters.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Filter by status
        db: Database session

    Returns:
        List of reports
    """
    query = select(Report).order_by(desc(Report.created_at))

    if status:
        query = query.where(Report.status == status)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    reports = result.scalars().all()

    return [ReportResponse.model_validate(report) for report in reports]


@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    """Get a specific report by ID.

    Args:
        report_id: Report database ID
        db: Database session

    Returns:
        Report details

    Raises:
        HTTPException: If report not found
    """
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail=f"Report not found: {report_id}")

    return ReportResponse.model_validate(report)


@router.get("/papers/{paper_id}/reports", response_model=List[ReportResponse])
async def get_paper_reports(
    paper_id: str,
    db: AsyncSession = Depends(get_db),
) -> List[ReportResponse]:
    """Get all reports for a specific paper.

    Args:
        paper_id: Paper identifier
        db: Database session

    Returns:
        List of reports for the paper
    """
    # First get the paper
    result = await db.execute(
        select(Paper).where(Paper.paper_id == paper_id)
    )
    paper = result.scalar_one_or_none()

    if not paper:
        raise HTTPException(status_code=404, detail=f"Paper not found: {paper_id}")

    # Get reports for the paper
    result = await db.execute(
        select(Report).where(Report.paper_id == paper.id).order_by(desc(Report.created_at))
    )
    reports = result.scalars().all()

    return [ReportResponse.model_validate(report) for report in reports]


# ============================================================================
# Task Endpoints (Manual Triggers)
# ============================================================================


@router.post("/tasks/crawl", response_model=CrawlPapersResponse, dependencies=[Depends(verify_api_key)])
async def crawl_papers(
    request: CrawlPapersRequest,
    db: AsyncSession = Depends(get_db),
) -> CrawlPapersResponse:
    """Trigger paper crawling task.

    Args:
        request: Crawl request parameters
        db: Database session

    Returns:
        Task creation response
    """
    logger.info("Manual crawl task triggered", source=request.source, limit=request.limit)

    # Create task record
    task = TaskModel(
        task_type="CRAWL",
        task_params={"source": request.source, "limit": request.limit},
        status="RUNNING",
        trigger_type="MANUAL",
    )
    db.add(task)
    await db.flush()

    try:
        # Execute crawl
        orchestrator = PaperOrchestrator(db)
        result = await orchestrator.crawl_and_save_papers(
            source=request.source,
            limit=request.limit,
        )

        # Update task
        task.status = "SUCCESS"
        task.result_summary = result
        task.end_time = datetime.now()

        await db.commit()

        return CrawlPapersResponse(
            task_id=task.id,
            message=f"Crawled {result['saved']} new papers",
            status="SUCCESS",
        )

    except Exception as e:
        task.status = "FAILED"
        task.error_message = str(e)
        task.end_time = datetime.now()
        await db.commit()

        logger.error("Crawl task failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Crawl failed: {str(e)}")


@router.post("/tasks/generate", response_model=GenerateReportResponse, dependencies=[Depends(verify_api_key)])
async def generate_reports(
    request: GenerateReportRequest,
    db: AsyncSession = Depends(get_db),
) -> GenerateReportResponse:
    """Trigger report generation task.

    Args:
        request: Generation request parameters
        db: Database session

    Returns:
        Task creation response
    """
    logger.info(
        "Manual report generation triggered",
        paper_id=request.paper_id,
        llm_provider=request.llm_provider,
    )

    # Create task record
    task = TaskModel(
        task_type="GENERATE_SINGLE" if request.paper_id else "GENERATE_BATCH",
        task_params={
            "paper_id": request.paper_id,
            "llm_provider": request.llm_provider,
            "force_regenerate": request.force_regenerate,
        },
        status="RUNNING",
        trigger_type="MANUAL",
    )
    db.add(task)
    await db.flush()

    try:
        orchestrator = PaperOrchestrator(db)

        if request.paper_id:
            # Generate for specific paper
            report = await orchestrator.regenerate_report(
                paper_id=request.paper_id,
                llm_provider=request.llm_provider,
            )
            result = {"paper_id": request.paper_id, "report_id": report.id}
            message = f"Generated report for paper {request.paper_id}"
        else:
            # Batch generation
            result = await orchestrator.generate_reports_batch(
                llm_provider=request.llm_provider,
            )
            message = f"Generated {result['success']} reports"

        # Update task
        task.status = "SUCCESS"
        task.result_summary = result
        task.end_time = datetime.now()

        await db.commit()

        return GenerateReportResponse(
            task_id=task.id,
            message=message,
            status="SUCCESS",
        )

    except Exception as e:
        task.status = "FAILED"
        task.error_message = str(e)
        task.end_time = datetime.now()
        await db.commit()

        logger.error("Report generation task failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    skip: int = 0,
    limit: int = 20,
    task_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> List[TaskResponse]:
    """List tasks with pagination and filters.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        task_type: Filter by task type
        status: Filter by status
        db: Database session

    Returns:
        List of tasks
    """
    query = select(TaskModel).order_by(desc(TaskModel.created_at))

    if task_type:
        query = query.where(TaskModel.task_type == task_type)
    if status:
        query = query.where(TaskModel.status == status)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    tasks = result.scalars().all()

    return [TaskResponse.model_validate(task) for task in tasks]


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """Get a specific task by ID.

    Args:
        task_id: Task database ID
        db: Database session

    Returns:
        Task details

    Raises:
        HTTPException: If task not found
    """
    result = await db.execute(
        select(TaskModel).where(TaskModel.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    return TaskResponse.model_validate(task)
