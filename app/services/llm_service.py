"""LLM service for generating paper analysis reports."""

from typing import Dict, Any, Optional
from datetime import datetime
import json
import time

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage

from app.core.logging import get_logger
from app.core.config import settings
from app.utils.retry import async_retry
from app.schemas.schemas import ReportContentSchema

logger = get_logger(__name__)


class LLMService:
    """Service for interacting with LLM providers."""

    REPORT_GENERATION_PROMPT = """你是一位资深的学术研究分析专家，擅长解读人工智能和机器学习领域的前沿论文。

请根据以下论文信息，生成一份高质量的中文分析报告。报告应该专业、准确、易读，帮助读者快速理解论文的核心价值。

论文信息：
- 标题：{title}
- 作者：{authors}
- 摘要：{abstract}
- 来源：{source}
- 分类：{categories}

请按以下结构生成报告，并以 JSON 格式返回：

1. core_summary (核心观点总结): 用 1-2 句话概括论文最重要的贡献（50-100字）
2. research_background (研究背景): 论文解决的问题及研究动机（100-200字）
3. technical_innovation (技术创新点): 论文提出的新方法、新技术（200-300字）
4. experiments_results (实验与结果): 主要实验设置和关键结果（150-250字）
5. application_value (应用价值): 研究的实际应用场景和意义（100-150字）
6. limitations (局限性分析): 论文的不足和未来改进方向（100-150字）
7. recommended_audience (推荐阅读人群): 适合哪些领域的研究者或从业者（50字以内）

请确保：
- 内容准确、专业，基于论文摘要进行合理推断
- 语言流畅，避免生硬翻译
- 突出论文的创新点和实用价值
- 客观分析局限性

请以 JSON 格式返回，键名使用英文（如上述结构），值使用中文内容。
"""

    def __init__(self, provider: Optional[str] = None) -> None:
        """Initialize LLM service.

        Args:
            provider: LLM provider name, defaults to config default
        """
        self.provider = provider or settings.llm.default_provider
        self.config = settings.llm.get_provider_config(self.provider)
        self.llm = self._initialize_llm()

    def _initialize_llm(self) -> ChatOpenAI:
        """Initialize LLM client based on provider.

        Returns:
            Initialized LLM client
        """
        # For now, we use OpenAI-compatible API for all providers
        # Different providers can be configured via api_base
        llm = ChatOpenAI(
            model=self.config["model"],
            temperature=self.config["temperature"],
            max_tokens=self.config["max_tokens"],
            openai_api_key=self.config["api_key"],
            openai_api_base=self.config.get("api_base"),
            timeout=60,
        )

        logger.info(
            "Initialized LLM client",
            provider=self.provider,
            model=self.config["model"],
        )

        return llm

    @async_retry(max_attempts=2, exceptions=(Exception,))
    async def generate_report(
        self,
        title: str,
        authors: list[str],
        abstract: str,
        source: str = "",
        categories: Optional[list[str]] = None,
    ) -> Dict[str, Any]:
        """Generate analysis report for a paper.

        Args:
            title: Paper title
            authors: List of authors
            abstract: Paper abstract
            source: Paper source
            categories: Paper categories

        Returns:
            Dictionary containing report content and metadata

        Raises:
            Exception: If report generation fails
        """
        start_time = time.time()

        # Format input data
        authors_str = ", ".join(authors[:5])  # Limit to first 5 authors
        if len(authors) > 5:
            authors_str += " et al."

        categories_str = ", ".join(categories) if categories else "未分类"

        # Build prompt
        prompt = self.REPORT_GENERATION_PROMPT.format(
            title=title,
            authors=authors_str,
            abstract=abstract,
            source=source,
            categories=categories_str,
        )

        logger.info(
            "Generating report with LLM",
            provider=self.provider,
            model=self.config["model"],
            title=title[:100],
        )

        try:
            # Call LLM
            messages = [
                SystemMessage(content="You are an expert academic research analyst."),
                HumanMessage(content=prompt),
            ]

            response = await self.llm.ainvoke(messages)
            content = response.content

            # Parse response
            report_content = self._parse_llm_response(content)

            # Validate structure
            self._validate_report_content(report_content)

            generation_time = int(time.time() - start_time)

            # Extract token usage if available
            token_usage = None
            if hasattr(response, "response_metadata"):
                usage = response.response_metadata.get("token_usage", {})
                if usage:
                    token_usage = {
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                    }

            logger.info(
                "Report generated successfully",
                provider=self.provider,
                generation_time=generation_time,
                token_usage=token_usage,
            )

            return {
                "content": report_content,
                "generation_time": generation_time,
                "token_usage": token_usage,
                "llm_provider": self.provider,
                "llm_model": self.config["model"],
            }

        except Exception as e:
            logger.error(
                "Failed to generate report",
                provider=self.provider,
                error=str(e),
                exc_info=True,
            )
            raise

    def _parse_llm_response(self, response: str) -> Dict[str, str]:
        """Parse LLM response to extract JSON content.

        Args:
            response: Raw LLM response

        Returns:
            Parsed report content dictionary

        Raises:
            ValueError: If parsing fails
        """
        try:
            # Try to find JSON in the response
            # Look for content between ```json and ``` or just parse directly
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response.strip()

            report_content = json.loads(json_str)
            return report_content

        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON from LLM response", error=str(e))
            # Try to extract key-value pairs manually as fallback
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")

    def _validate_report_content(self, content: Dict[str, str]) -> None:
        """Validate report content structure.

        Args:
            content: Report content dictionary

        Raises:
            ValueError: If validation fails
        """
        required_fields = [
            "core_summary",
            "research_background",
            "technical_innovation",
            "experiments_results",
            "application_value",
            "limitations",
            "recommended_audience",
        ]

        missing_fields = [field for field in required_fields if field not in content]

        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        # Validate field lengths (rough check)
        for field, value in content.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Field '{field}' must be a non-empty string")

        logger.debug("Report content validation passed")


async def generate_paper_report(
    paper_data: Dict[str, Any], provider: Optional[str] = None
) -> Dict[str, Any]:
    """Generate report for a paper.

    Args:
        paper_data: Paper data dictionary
        provider: Optional LLM provider override

    Returns:
        Report generation result
    """
    llm_service = LLMService(provider=provider)

    result = await llm_service.generate_report(
        title=paper_data["title"],
        authors=paper_data["authors"],
        abstract=paper_data["abstract"],
        source=paper_data.get("source", ""),
        categories=paper_data.get("categories"),
    )

    return result
