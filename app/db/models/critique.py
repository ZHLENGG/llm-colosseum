from __future__ import annotations
from typing import TYPE_CHECKING
import uuid
from datetime import datetime, timezone
from sqlalchemy import Text, DateTime, ForeignKey, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.response import Response
    from app.db.models.battle import Battle

class Critique(Base):
    __tablename__ = "critiques"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    battle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("battles.id", ondelete="CASCADE"))
    battle: Mapped["Battle"] = relationship(back_populates="critiques")
    
    # Кто написал критику
    author_participant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("participants.id", ondelete="CASCADE"))
    # На какой ответ направлена критика
    target_response_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("responses.id", ondelete="CASCADE"))
    
    content: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[int] = mapped_column(SmallInteger, nullable=False) # Оценка от 1 до 10
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    target_response: Mapped["Response"] = relationship(back_populates="critiques")