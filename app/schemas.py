from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
from .providers import ProviderType
from .models import ModelType

class SummaryRequest(BaseModel):
    url: str = Field(..., description="URL of the content to summarize")
    max_length: Optional[int] = Field(1000, description="Target maximum length of summary in words")
    provider_type: Optional[ProviderType] = Field(ProviderType.youtube, description="Type of content provider")
    model_type: Optional[ModelType] = Field(ModelType.huggingface, description="Type of summarization model")
    model_name: Optional[str] = Field(None, description="Specific model name (if applicable)")

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
                "metadata": {
                    "word_count": 250,
                    "source_type": "youtube",
                    "model_type": "huggingface",
                    "model_name": "facebook/bart-large-cnn"
                }
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
    model_type: Optional[str] = None
    model_name: Optional[str] = None
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
                "model_type": "huggingface",
                "model_name": "facebook/bart-large-cnn",
                "summary_length": 500,
                "valid": True,
                "processing_time": 5.2,
                "created_at": "2023-05-06 12:34:56"
            }
        }

class APIKeyRequest(BaseModel):
    provider: str = Field(..., description="Provider name (e.g., openai, anthropic)")
    api_key: str = Field(..., description="API key for the provider")

    @validator('provider')
    def validate_provider(cls, v):
        allowed_providers = ['openai', 'anthropic']
        if v not in allowed_providers:
            raise ValueError(f'Provider must be one of: {allowed_providers}')
        return v

class UserAPIKeyResponse(BaseModel):
    provider: str = Field(..., description="Provider name")
    has_key: bool = Field(..., description="Whether the user has an API key for this provider")
    last_updated: Optional[str] = Field(None, description="When the API key was last updated")

class UserAPIKeysResponse(BaseModel):
    keys: List[UserAPIKeyResponse] = Field(..., description="List of user's API keys")
