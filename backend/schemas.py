from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


class JobBase(BaseModel):
    title: str = Field(..., description="Job role title")
    company: str = Field(..., description="Hiring company name")
    location: str = Field(default="Remote", description="Job location or Remote status")
    job_url: str = Field(..., description="Direct application or source listing URL")
    description: str = Field(..., description="Raw or parsed job description text")
    skills: List[str] = Field(default_factory=list, description="Extracted tech stack skills")
    experience_level: Optional[str] = Field(
        default="Entry Level", 
        description="e.g. Entry Level, Mid Level, Senior"
    )


class JobCreate(JobBase):
    """Schema used internally when preparing a scraped job for database insertion."""
    content_hash: str = Field(..., description="Deterministic SHA-256 fingerprint for deduplication")


class JobResponse(JobBase):
    """Schema returned by FastAPI endpoints to clients/frontend."""
    id: int
    content_hash: str
    first_seen_at: datetime
    last_seen_at: datetime

    class Config:
        from_attributes = True


class PaginatedJobResponse(BaseModel):
    """Envelope schema for paginated results with metadata."""
    total_count: int
    page: int
    page_size: int
    has_next: bool
    items: List[JobResponse]

class SkillMetric(BaseModel):
    skill: str
    count: int


class TopSkillsResponse(BaseModel):
    total_analyzed_jobs: int
    top_skills: List[SkillMetric]