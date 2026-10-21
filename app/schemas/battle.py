import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# --- Схемы для создания ---
class BattleCreate(BaseModel):
    question: str = Field(min_length=5, max_length=500)
    models: List[str] = Field(min_length=2, max_length=4, default=["phi3", "mistral"])

# --- Базовые схемы ответа ---
class BattleResponse(BaseModel):
    id: uuid.UUID
    question: str
    status: str
    created_at: datetime
    judge_summary: Optional[str] = None
    winner_participant_id: Optional[uuid.UUID] = None

    model_config = {"from_attributes": True}

# --- Детальные схемы (для UI) ---
class ResponseDetail(BaseModel):
    id: uuid.UUID
    participant_id: uuid.UUID
    round: int
    content: str

    model_config = {"from_attributes": True}

class ParticipantDetail(BaseModel):
    id: uuid.UUID
    model_name: str
    display_name: str
    total_score: Optional[float] = None
    responses: List[ResponseDetail] = []

    model_config = {"from_attributes": True}

class CritiqueDetail(BaseModel):
    author_participant_id: uuid.UUID
    target_response_id: uuid.UUID
    content: str
    score: int

    model_config = {"from_attributes": True}

class BattleDetailResponse(BattleResponse):
    participants: List[ParticipantDetail] = []
    critiques: List[CritiqueDetail] = []