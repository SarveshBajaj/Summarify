from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
from .providers import ProviderType

class SummaryRequest(BaseModel):
    url: str = Field(..., description="URL of the content to summarize")
    max_length: Optional[int] = Field(1000, description="Target maximum length of summary in words")
    provider_type: Optional[ProviderType] = Field(ProviderType.youtube, description="Type of content provider")

    @validator('max_length')
    def validate_max_length(cls, v):
        if v is not None and (v < 100 or v > 2000):
            raise ValueError('max_length must be between 100 and 2000 words')
        return v

class SummaryResponse(BaseModel):
    summary: str = Field(..., description="Generated summary text")
    valid: bool = Field(..., description="Whether the summary passed validation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the summary")

    class Config:
        schema_extra = {
            "example": {
                "summary": "This is a summary of the video content...",
                "valid": True,
                "metadata": {"word_count": 250, "source_type": "youtube"}
            }
        }

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: Optional[str] = None

    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('username must be alphanumeric')
        return v

class User(BaseModel):
    username: str
    email: Optional[str] = None
    disabled: Optional[bool] = None

class Token(BaseModel):
    access_token: str
    token_type: str

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }

class TokenData(BaseModel):
    username: Optional[str] = None

class QueryRecord(BaseModel):
    id: int
    user_id: int
    url: str
    provider_type: str
    summary_length: int
    valid: bool
    processing_time: float
    created_at: str

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "provider_type": "youtube",
                "summary_length": 500,
                "valid": True,
                "processing_time": 5.2,
                "created_at": "2023-05-06 12:34:56"
            }
        }
