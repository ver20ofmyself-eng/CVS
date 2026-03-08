from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class PromptBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    system_prompt: str = Field(..., min_length=10)
    user_prompt_template: str = Field(..., min_length=10)
    response_format: Dict[str, Any] = Field(default={})
    parameters: Dict[str, Any] = Field(default={})
    is_active: bool = True
    is_default: bool = False

class PromptCreate(PromptBase):
    pass

class PromptUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    system_prompt: Optional[str] = Field(None, min_length=10)
    user_prompt_template: Optional[str] = Field(None, min_length=10)
    response_format: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None

class PromptResponse(PromptBase):
    id: int
    version: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PromptHistoryResponse(BaseModel):
    id: int
    prompt_id: int
    name: str
    system_prompt: str
    user_prompt_template: str
    parameters: Dict[str, Any]
    version: int
    changed_by: Optional[int] = None
    changed_at: datetime
    change_comment: Optional[str] = None
    
    class Config:
        from_attributes = True
        