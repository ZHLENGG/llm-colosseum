from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models.battle import Battle
from app.schemas.battle import BattleCreate, BattleResponse
from app.services.debate_orchestrator import run_battle_round_1

# Создаем роутер с префиксом /battles и тегом для Swagger
router = APIRouter(prefix="/battles", tags=["Battles"])

@router.post(
    "/", 
    response_model=BattleResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый баттл"
)
async def create_battle(
    payload: BattleCreate, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db) # Внедряем сессию БД через Depends
):
    """
    Принимает вопрос и список моделей. Создает запись в БД со статусом 'pending'.
    """
    # 1. Создаем объект модели (SQLAlchemy)
    new_battle = Battle(
        question=payload.question,
        status="pending"
    )
    
    # 2. Добавляем его в сессию и коммитим (сохраняем в БД)
    db.add(new_battle)
    await db.commit()
    
    # 3. Обновляем объект из БД, чтобы получить сгенерированные поля (например, id и created_at)
    await db.refresh(new_battle)

    # ЗАПУСКАЕМ ДЕБАТЫ В ФОНЕ!
    # Клиент сразу получит ответ 201, а дебаты продолжат крутиться в сервере.
    background_tasks.add_task(run_battle_round_1, new_battle.id, db)
    
    # FastAPI автоматически возьмет объект new_battle, 
    # прогонит его через BattleResponse (Pydantic) и вернет клиенту JSON.
    return new_battle