from __future__ import annotations
from typing import TYPE_CHECKING
import uuid
from sqlalchemy import String, ForeignKey
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
    role: Mapped[str] = mapped_column(String(10), default="agent") # 'agent' или 'judge'
    
    battle: Mapped["Battle"] = relationship(back_populates="participants")
    responses: Mapped[list["Response"]] = relationship(back_populates="participant", cascade="all, delete-orphan")