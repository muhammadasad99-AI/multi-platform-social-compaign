from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CreateCampaignRequest(BaseModel):
    blog_title: str = Field(..., min_length=1)
    blog_body: str = Field(..., min_length=1)
    blog_url: str = Field(..., min_length=1)
    source_image_path: str = Field(..., description="Path to a local source image to derive variants from")
    scheduled_for: Optional[datetime] = Field(None, description="If omitted, publish is queued immediately")


class CampaignPostStatus(BaseModel):
    platform: str
    status: str
    image_path: Optional[str]
    caption: Optional[str]
    platform_post_id: Optional[str]
    retry_count: int
    last_error: Optional[str]

    class Config:
        from_attributes = True


class CampaignResponse(BaseModel):
    id: str
    blog_title: str
    blog_url: str
    scheduled_for: Optional[datetime]
    posts: list[CampaignPostStatus]