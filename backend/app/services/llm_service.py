# LLM service - to be filled from llm_service_py.txt
import json
import logging
import re
from typing import Optional, Dict, Any
import google.generativeai as genai
from google.api_core import retry

from app.core.prompts import create_analysis_prompt
from app.models.schemas import IssueAnalysis, PriorityScore

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM-based issue analysis using Google Gemini."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-pro",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        timeout: int = 30
    ):
        """
        Initialize LLM service.

        Args:
            api_key: Google Gemini API key
            model: Model name (e.g., 'gemini-pro')
            temperature: Temperature for generation (0-1)
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

        # Configure Gemini API
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model)

    async def analyze_issue(
        self,
        issue_title: str,
        issue_body: str,
        comments: list[str],
        repo_context: Optional[str] = None,
        retry_count: int = 0,
        max_retries: int = 3
    ) -> IssueAnalysis:
        """
        Analyze a GitHub issue using LLM.

        Args:
            issue_title: Title of the issue
            issue_body: Body/description of the issue
            comments: List of comments
            repo_context: Optional repository context
            retry_count: Current retry attempt
            max_retries: Maximum retry attempts

        Returns:
            IssueAnalysis object with structured results

        Raises:
            ValueError: If analysis fails after retries
        """
        try:
            # Create prompt with few-shot examples
            prompt = create_analysis_prompt(
                issue_title=issue_title,
                issue_body=issue_body,
                comments=comments,
                repo_context=repo_context
            )

            # Call Gemini API
            response = await self._call_gemini(prompt)
            logger.info("Received response from Gemini API")

            # Parse and validate response
            analysis = self._parse_response(response)

            logger.info(f"Successfully analyzed issue: {analysis.summary}")
            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}. Response: {response}")
            if retry_count < max_retries:
                logger.info(f"Retrying analysis (attempt {retry_count + 1}/{max_retries})")
                # Add clearer instructions to prompt
                enhanced_prompt = prompt + "\n\nIMPORTANT: Respond with ONLY valid JSON, no other text."
                response = await self._call_gemini(enhanced_prompt)
                return await self.analyze_issue(
                    issue_title=issue_title,
                    issue_body=issue_body,
                    comments=comments,
                    repo_context=repo_context,
                    retry_count=retry_count + 1,
                    max_retries=max_retries
                )
            else:
                raise ValueError(f"Failed to parse LLM response after {max_retries} retries")

        except Exception as e:
            logger.error(f"Error analyzing issue: {e}")
            if retry_count < max_retries:
                logger.info(f"Retrying after error (attempt {retry_count + 1}/{max_retries})")
                return await self.analyze_issue(
                    issue_title=issue_title,
                    issue_body=issue_body,
                    comments=comments,
                    repo_context=repo_context,
                    retry_count=retry_count + 1,
                    max_retries=max_retries
                )
            raise

    async def _call_gemini(self, prompt: str) -> str:
        """
        Call Google Gemini API.

        Args:
            prompt: The analysis prompt

        Returns:
            API response text
        """
        try:
            # Use synchronous client since Gemini doesn't have proper async support yet
            response = self.client.generate_content(
                prompt,
                generation_config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_tokens,
                }
            )

            if response.text:
                return response.text
            else:
                raise ValueError("Empty response from Gemini API")

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

    def _parse_response(self, response_text: str) -> IssueAnalysis:
        """
        Parse and validate LLM response.

        Args:
            response_text: Raw response from LLM

        Returns:
            Validated IssueAnalysis object

        Raises:
            ValueError: If response format is invalid
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(
                r'```(?:json)?\s*(.*?)\s*```',
                response_text,
                re.DOTALL
            )

            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response_text

            # Parse JSON
            data = json.loads(json_str)

            # Validate and construct IssueAnalysis
            analysis = IssueAnalysis(
                summary=data.get("summary", ""),
                type=self._validate_type(data.get("type")),
                priority_score=PriorityScore(
                    score=self._validate_priority_score(data.get("priority_score", {}).get("score")),
                    justification=data.get("priority_score", {}).get("justification", "")
                ),
                suggested_labels=self._validate_labels(data.get("suggested_labels", [])),
                potential_impact=data.get("potential_impact", "")
            )

            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            raise ValueError(f"Invalid JSON in response: {e}")
        except KeyError as e:
            logger.error(f"Missing required field: {e}")
            raise ValueError(f"Missing required field in response: {e}")

    @staticmethod
    def _validate_type(issue_type: str) -> str:
        """Validate issue type."""
        valid_types = ["bug", "feature_request", "documentation", "question", "other"]
        if issue_type not in valid_types:
            logger.warning(f"Invalid type '{issue_type}', defaulting to 'other'")
            return "other"
        return issue_type

    @staticmethod
    def _validate_priority_score(score: Any) -> int:
        """Validate and sanitize priority score."""
        try:
            score_int = int(score)
            if 1 <= score_int <= 5:
                return score_int
            else:
                logger.warning(f"Priority score {score} out of range, defaulting to 3")
                return 3
        except (ValueError, TypeError):
            logger.warning(f"Invalid priority score {score}, defaulting to 3")
            return 3

    @staticmethod
    def _validate_labels(labels: Any) -> list[str]:
        """Validate and sanitize labels."""
        if not isinstance(labels, list):
            return []

        # Keep only strings, limit to 5 labels
        valid_labels = [
            str(label).strip()
            for label in labels
            if isinstance(label, (str, int))
        ][:5]

        return valid_labels if valid_labels else ["general"]

    async def analyze_batch(
        self,
        issues: list[Dict[str, Any]]
    ) -> list[IssueAnalysis]:
        """
        Analyze multiple issues in batch.

        Args:
            issues: List of issue dictionaries

        Returns:
            List of IssueAnalysis objects
        """
        results = []
        for issue in issues[:5]:  # Max 5 for batch
            try:
                analysis = await self.analyze_issue(
                    issue_title=issue.get("title", ""),
                    issue_body=issue.get("body", ""),
                    comments=issue.get("comments", []),
                    repo_context=issue.get("repo", None)
                )
                results.append(analysis)
            except Exception as e:
                logger.error(f"Error analyzing issue in batch: {e}")
                continue

        return results