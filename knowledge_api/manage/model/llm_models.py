from pydantic import BaseModel, Field

from knowledge_api.manage.model.base import BaseResponse


class RoleInput(BaseResponse):
    """Role Input Model"""

    def __init__(self, data, **kwargs):
        super().__init__(data=data, **kwargs)


class LlmQueryInputEnhance(BaseModel):
    prompt: str = Field(..., description="cue word")
    enhance_context: str = Field(..., description="enhanced content")
    model_id: str = Field(..., description="model selection")