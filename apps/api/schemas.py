from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CaptureRequest(BaseModel):
    url: str
    captured_at: datetime
    html: str
    title: Optional[str] = None


class CaptureResponse(BaseModel):
    status: str
    next_profile: str


class ProfileBase(BaseModel):
    username: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    followers: int = 0
    following: int = 0
    posts_count: int = 0
    website: Optional[str] = None
    is_verified: bool = False
    profile_image: Optional[str] = None
    priority_score: int = 0


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(BaseModel):
    followers: Optional[int] = None
    following: Optional[int] = None
    posts_count: Optional[int] = None
    is_verified: Optional[bool] = None
    profile_image: Optional[str] = None
    priority_score: Optional[int] = None


class ProfileSchema(ProfileBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NextProfileResponse(BaseModel):
    next_profile: str
