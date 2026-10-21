from pydantic import BaseModel, Field
from datetime import datetime
import uuid

# Схема для входящих данных (то, что присылает клиент)
class BattleCreate(BaseModel):
    question: str = Field(
        min_length=5, 
        max_length=500, 
        description="Вопрос, который мы задаем моделям"
    )
    # Пока для простоты будем передавать список строк (имена моделей)
    # Например: ["llama3", "mistral", "phi3"]
    models: list[str] = Field(
        min_length=2, 
        max_length=4, 
        description="Список моделей-участников"
    )

# Схема для ответа (то, что мы отдаем клиенту)
class BattleResponse(BaseModel):
    id: uuid.UUID
    question: str
    status: str
    created_at: datetime

    # Эта настройка говорит Pydantic, что можно создавать эту схему 
    # прямо из объекта SQLAlchemy (ORM), так как у них совпадают поля
    model_config = {"from_attributes": True}