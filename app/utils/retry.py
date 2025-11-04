"""Retry utility with exponential backoff."""

from typing import TypeVar, Callable, Any, Optional
from functools import wraps
import asyncio
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryCallState,
)

from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)

T = TypeVar("T")


def async_retry(
    max_attempts: Optional[int] = None,
    retry_delay: Optional[int] = None,
    exceptions: tuple = (Exception,),
) -> Callable:
    """Decorator for async functions with exponential backoff retry.

    Args:
        max_attempts: Maximum number of retry attempts
        retry_delay: Base delay between retries in seconds
        exceptions: Tuple of exceptions to retry on

    Returns:
        Decorated function with retry logic
    """
    if max_attempts is None:
        max_attempts = settings.crawler.max_retries
    if retry_delay is None:
        retry_delay = settings.crawler.retry_delay

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=retry_delay, min=retry_delay, max=60),
            retry=retry_if_exception_type(exceptions),
            before_sleep=before_sleep_log(logger, logging_level="WARNING"),
            reraise=True,
        )
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def sync_retry(
    max_attempts: Optional[int] = None,
    retry_delay: Optional[int] = None,
    exceptions: tuple = (Exception,),
) -> Callable:
    """Decorator for sync functions with exponential backoff retry.

    Args:
        max_attempts: Maximum number of retry attempts
        retry_delay: Base delay between retries in seconds
        exceptions: Tuple of exceptions to retry on

    Returns:
        Decorated function with retry logic
    """
    if max_attempts is None:
        max_attempts = settings.crawler.max_retries
    if retry_delay is None:
        retry_delay = settings.crawler.retry_delay

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=retry_delay, min=retry_delay, max=60),
            retry=retry_if_exception_type(exceptions),
            before_sleep=before_sleep_log(logger, logging_level="WARNING"),
            reraise=True,
        )
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return wrapper

    return decorator
