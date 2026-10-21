from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.participant import Participant
    from app.db.models.critique import Critique

class Battle(Base):
    __tablename__ = "battles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    judge_summary: Mapped[Optional[str]] = mapped_column(Text)
    
    # ID победителя
    winner_participant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("participants.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    participants: Mapped[List["Participant"]] = relationship(
        back_populates="battle", 
        cascade="all, delete-orphan",
        foreign_keys="Participant.battle_id"
    )
    critiques: Mapped[List["Critique"]] = relationship(back_populates="battle", cascade="all, delete-orphan")