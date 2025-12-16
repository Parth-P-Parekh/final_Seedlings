# API routes - to be filled from routes_py.txt
import logging
import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

from app.services.github_service import GitHubService
from app.services.llm_service import LLMService
from app.models.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    IssueAnalysis,
    PriorityScore,
    ErrorResponse,
    HealthCheckResponse,
    StatsResponse
)
from app.core.config import settings
from app.utils.cache import CacheManager
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Initialize services
github_service = GitHubService(
    github_token=settings.GITHUB_TOKEN,
    timeout=settings.GITHUB_API_TIMEOUT
)

llm_service = LLMService(
    api_key=settings.GEMINI_API_KEY,
    model=settings.LLM_MODEL,
    temperature=settings.LLM_TEMPERATURE,
    max_tokens=settings.LLM_MAX_TOKENS
)

cache_manager = CacheManager(
    enabled=settings.REDIS_ENABLED,
    redis_host=settings.REDIS_HOST,
    redis_port=settings.REDIS_PORT,
    ttl=settings.CACHE_TTL
)

# Global statistics
stats = {
    "total_analyses": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "errors": 0,
    "response_times": []
}

# Create router
router = APIRouter(prefix="/api/v1", tags=["analysis"])


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_issue(request: AnalysisRequest) -> AnalysisResponse:
    """
    Analyze a GitHub issue and return structured insights.

    Args:
        request: AnalysisRequest with GitHub URL and issue number

    Returns:
        AnalysisResponse with analysis results

    Raises:
        HTTPException: For invalid requests or service errors
    """
    start_time = time.time()

    try:
        # Parse GitHub URL
        try:
            owner, repo = github_service.parse_github_url(request.github_url)
            logger.info(f"Parsed GitHub URL: {owner}/{repo}#{request.issue_number}")
        except ValueError as e:
            stats["errors"] += 1
            raise HTTPException(status_code=400, detail=str(e))

        # Check cache
        cache_key = f"{owner}/{repo}#{request.issue_number}"
        if request.use_cache:
            cached_result = cache_manager.get(cache_key)
            if cached_result:
                stats["cache_hits"] += 1
                logger.info(f"Cache hit for {cache_key}")
                elapsed = time.time() - start_time
                stats["response_times"].append(elapsed)

                return AnalysisResponse(
                    success=True,
                    data=IssueAnalysis(**cached_result),
                    metadata={
                        "analysis_time_ms": int(elapsed * 1000),
                        "cached": True,
                        "issue_url": f"https://github.com/{owner}/{repo}/issues/{request.issue_number}"
                    }
                )

            stats["cache_misses"] += 1

        # Validate repository exists
        is_valid = await github_service.validate_repository(owner, repo)
        if not is_valid:
            stats["errors"] += 1
            raise HTTPException(
                status_code=404,
                detail=f"Repository {owner}/{repo} not found or is private"
            )

        # Fetch issue data
        logger.info(f"Fetching issue #{request.issue_number} from {owner}/{repo}")
        github_issue = await github_service.fetch_issue(owner, repo, request.issue_number)

        # Analyze with LLM
        logger.info("Analyzing issue with Gemini API")
        analysis = await llm_service.analyze_issue(
            issue_title=github_issue.title,
            issue_body=github_issue.body,
            comments=github_issue.comments,
            repo_context=f"{owner}/{repo}"
        )

        # Cache result
        cache_manager.set(cache_key, analysis.dict())
        logger.info(f"Cached analysis result for {cache_key}")

        # Update statistics
        elapsed = time.time() - start_time
        stats["total_analyses"] += 1
        stats["response_times"].append(elapsed)

        logger.info(f"Analysis completed in {elapsed:.2f}s")

        return AnalysisResponse(
            success=True,
            data=analysis,
            metadata={
                "analysis_time_ms": int(elapsed * 1000),
                "cached": False,
                "issue_url": github_issue.url,
                "author": github_issue.author,
                "state": github_issue.state,
                "existing_labels": github_issue.labels
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        stats["errors"] += 1
        logger.error(f"Unexpected error during analysis: {e}", exc_info=True)
        detail = f"Internal server error: {str(e)}" if settings.DEBUG else "Internal server error"
        raise HTTPException(status_code=500, detail=detail)


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    return HealthCheckResponse(
        status="healthy",
        version=settings.API_VERSION,
        timestamp=datetime.utcnow()
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get API statistics and analytics."""
    total = stats["total_analyses"]
    hits = stats["cache_hits"]
    misses = stats["cache_misses"]
    total_requests = hits + misses

    hit_rate = (hits / total_requests * 100) if total_requests > 0 else 0
    avg_time = (sum(stats["response_times"]) / len(stats["response_times"]) * 1000) if stats["response_times"] else 0

    return StatsResponse(
        total_analyses=total,
        cache_hits=hits,
        cache_misses=misses,
        cache_hit_rate=hit_rate,
        avg_response_time_ms=avg_time,
        errors=stats["errors"]
    )


@router.post("/analyze-batch")
async def analyze_batch(urls_and_issues: list[dict]):
    """
    Analyze multiple issues in batch (up to 5).

    Args:
        urls_and_issues: List of {github_url, issue_number} dicts

    Returns:
        List of analysis results
    """
    if len(urls_and_issues) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 issues per batch")

    results = []
    for item in urls_and_issues:
        try:
            request = AnalysisRequest(
                github_url=item["github_url"],
                issue_number=item["issue_number"]
            )
            result = await analyze_issue(request)
            results.append(result)
        except HTTPException as e:
            results.append({
                "success": False,
                "error": e.detail
            })

    return {"analyses": results, "total": len(urls_and_issues)}


@router.delete("/cache/{owner}/{repo}/{issue_number}")
async def clear_cache(owner: str, repo: str, issue_number: int):
    """Clear cache for a specific issue."""
    cache_key = f"{owner}/{repo}#{issue_number}"
    cache_manager.delete(cache_key)
    return {"success": True, "message": f"Cache cleared for {cache_key}"}


@router.post("/cache/clear-all")
async def clear_all_cache():
    """Clear entire cache (admin endpoint)."""
    cache_manager.clear_all()
    return {"success": True, "message": "All cache cleared"}