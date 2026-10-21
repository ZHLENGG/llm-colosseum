from fastapi import APIRouter, Depends, status, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models.battle import Battle
from app.db.models.participant import Participant
# Импортируем все три этапа дебатов
from app.services.debate_orchestrator import run_battle_round_1, run_battle_round_2, run_battle_judge
from app.schemas.battle import BattleCreate, BattleResponse, BattleDetailResponse

router = APIRouter(prefix="/battles", tags=["Battles"])

# Фоновая задача, которая прогоняет все раунды и судью
async def run_full_battle(battle_id: str, db: AsyncSession):
    await run_battle_round_1(battle_id, db)
    await run_battle_round_2(battle_id, db)
    await run_battle_judge(battle_id, db)

@router.post(
    "/", 
    response_model=BattleResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый баттл"
)
async def create_battle(
    payload: BattleCreate, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    new_battle = Battle(
        question=payload.question,
        status="pending"
    )
    db.add(new_battle)
    await db.commit()
    await db.refresh(new_battle)

    # Запускаем полный цикл в фоне
    background_tasks.add_task(run_full_battle, new_battle.id, db)
    
    return new_battle


@router.get(
    "/{battle_id}", 
    response_model=BattleDetailResponse,
    summary="Получить детали баттла для UI"
)
async def get_battle(
    battle_id: str, 
    db: AsyncSession = Depends(get_db)
):
    """
    Отдает полную информацию о баттле: участников, их ответы, критику и вердикт.
    """
    result = await db.execute(
        select(Battle)
        .options(
            # Загружаем участников и их ответы
            selectinload(Battle.participants).selectinload(Participant.responses),
            # Загружаем критику (важно, чтобы связь была описана в модели Battle!)
            selectinload(Battle.critiques)
        )
        .where(Battle.id == battle_id)
    )
    battle = result.scalar_one_or_none()
    
    if not battle:
        raise HTTPException(status_code=404, detail="Battle not found")
    
    return battle