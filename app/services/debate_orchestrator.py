import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.battle import Battle
from app.db.models.participant import Participant
from app.db.models.response import Response
from app.services.ollama_client import ollama_client

logger = logging.getLogger(__name__)

async def run_battle_round_1(battle_id: str, db: AsyncSession):
    """
    Запускает первый раунд дебатов: все модели отвечают на вопрос параллельно.
    """
    logger.info(f"Starting Round 1 for battle {battle_id}")
    
    # 1. Достаем баттл из БД
    result = await db.execute(select(Battle).where(Battle.id == battle_id))
    battle = result.scalar_one_or_none()
    if not battle:
        logger.error(f"Battle {battle_id} not found")
        return

    battle.status = "running"
    await db.commit()

    # 2. Создаем участников (пока хардкодим модели, потом можно брать из API)
    # В нашем BattleCreate приходят модели, но для простоты создадим тут
    models = ["phi3", "phi3"] # Для теста можно взять две phi3, чтобы не качать другие
    participants = []
    
    for i, model_name in enumerate(models):
        participant = Participant(
            battle_id=battle.id,
            model_name=model_name,
            role="agent",
            display_name=f"Agent {i+1} ({model_name})"
        )
        db.add(participant)
        participants.append(participant)
    
    await db.commit()
    for p in participants:
        await db.refresh(p)

    # 3. Формируем промпт
    prompt = f"Ответь на следующий вопрос кратко и по делу: {battle.question}"

    # 4. Запускаем генерацию ПАРАЛЛЕЛЬНО
    async def get_response(participant: Participant):
        try:
            # Вызываем наш клиент Ollama
            result = await ollama_client.generate_response(model=participant.model_name, prompt=prompt)
            return {
                "participant": participant,
                "content": result.get("response", ""),
                "tokens": result.get("eval_count", 0)
            }
        except Exception as e:
            logger.error(f"Error generating response for {participant.model_name}: {e}")
            return None

    # asyncio.gather — это та самая магия параллельности. 
    # Все запросы к Ollama уходят одновременно.
    responses_data = await asyncio.gather(*(get_response(p) for p in participants))

    # 5. Сохраняем результаты в БД
    for data in responses_data:
        if data is None:
            continue # Пропускаем, если модель упала
        
        response = Response(
            battle_id=battle.id,
            participant_id=data["participant"].id,
            round=1,
            content=data["content"],
            tokens_used=data["tokens"]
        )
        db.add(response)
    
    battle.status = "completed" # Пока ставим completed, позже добавим раунды
    await db.commit()
    logger.info(f"Battle {battle_id} Round 1 completed successfully.")