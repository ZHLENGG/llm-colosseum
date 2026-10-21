from __future__ import annotations
import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Numeric, Text # <-- Добавили Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.battle import Battle
    from app.db.models.response import Response

class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    battle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("battles.id", ondelete="CASCADE"))
    model_name: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[str] = mapped_column(String(10), default="agent") 
    
    # ТЕ САМЫЕ НОВЫЕ ПОЛЯ:
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    total_score: Mapped[Optional[float]] = mapped_column(Numeric(6, 2))
    
    battle: Mapped["Battle"] = relationship(
        back_populates="participants", 
        foreign_keys=[battle_id]
    )
    responses: Mapped[list[Response]] = relationship(back_populates="participant", cascade="all, delete-orphan")