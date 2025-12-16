# Data schemas - to be filled from schemas_py.txt
from pydantic import BaseModel, Field, HttpUrl, validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class AnalysisRequest(BaseModel):
    """Request model for issue analysis."""
    github_url: str = Field(
        ...,
        description="Public GitHub repository URL (e.g., https://github.com/facebook/react)"
    )
    issue_number: int = Field(
        ...,
        gt=0,
        description="GitHub issue number"
    )
    use_cache: bool = Field(
        default=True,
        description="Use cached results if available"
    )

    @validator("github_url")
    def validate_github_url(cls, v):
        """Validate GitHub URL format."""
        if "github.com" not in v:
            raise ValueError("Must be a valid GitHub URL")
        return v


class PriorityScore(BaseModel):
    """Priority score with justification."""
    score: int = Field(
        ...,
        ge=1,
        le=5,
        description="Priority score from 1 (low) to 5 (critical)"
    )
    justification: str = Field(
        ...,
        description="Brief justification for the score"
    )


class IssueAnalysis(BaseModel):
    """Complete issue analysis result."""
    summary: str = Field(
        ...,
        description="One-sentence summary of the issue"
    )
    type: str = Field(
        ...,
        description="Issue type: bug, feature_request, documentation, question, other"
    )
    priority_score: PriorityScore = Field(
        ...,
        description="Priority score with justification"
    )
    suggested_labels: List[str] = Field(
        default_factory=list,
        description="Suggested GitHub labels (2-3 items)"
    )
    potential_impact: str = Field(
        ...,
        description="Potential impact of the issue"
    )

    @validator("type")
    def validate_type(cls, v):
        """Validate issue type."""
        valid_types = ["bug", "feature_request", "documentation", "question", "other"]
        if v not in valid_types:
            raise ValueError(f"Type must be one of: {', '.join(valid_types)}")
        return v


class AnalysisResponse(BaseModel):
    """Complete API response."""
    success: bool
    data: Optional[IssueAnalysis] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "summary": "Users want faster rendering performance",
                    "type": "bug",
                    "priority_score": {
                        "score": 4,
                        "justification": "Impacts user experience significantly"
                    },
                    "suggested_labels": ["performance", "urgent"],
                    "potential_impact": "Slow rendering affects app usability"
                },
                "metadata": {
                    "analysis_time_ms": 2150,
                    "cached": False,
                    "issue_url": "https://github.com/facebook/react/issues/28029"
                }
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Check timestamp")


class StatsResponse(BaseModel):
    """Analytics statistics."""
    total_analyses: int
    cache_hits: int
    cache_misses: int
    cache_hit_rate: float
    avg_response_time_ms: float
    errors: int


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)