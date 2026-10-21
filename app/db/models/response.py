from __future__ import annotations
from typing import TYPE_CHECKING
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Text, Integer, DateTime, ForeignKey, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.participant import Participant
    from app.db.models.critique import Critique

class Response(Base):
    __tablename__ = "responses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    battle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("battles.id", ondelete="CASCADE"))
    participant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("participants.id", ondelete="CASCADE"))
    
    round: Mapped[int] = mapped_column(SmallInteger, nullable=False) # 1 или 3
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    participant: Mapped["Participant"] = relationship(back_populates="responses")
    # Эта связь понадобится нам, когда мы будем считать оценки
    critiques: Mapped[list["Critique"]] = relationship(back_populates="target_response", cascade="all, delete-orphan")