import asyncio
import logging
import re
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.battle import Battle
from app.db.models.participant import Participant
from app.db.models.response import Response
from app.db.models.critique import Critique
from app.services.ollama_client import ollama_client

logger = logging.getLogger(__name__)

async def run_battle_round_1(battle_id: str, db: AsyncSession):
    """
    Раунд 1: Все модели параллельно отвечают на вопрос.
    """
    logger.info(f"Starting Round 1 for battle {battle_id}")
    
    result = await db.execute(select(Battle).where(Battle.id == battle_id))
    battle = result.scalar_one_or_none()
    if not battle:
        logger.error(f"Battle {battle_id} not found")
        return

    # Статус для UI: модели думают над ответами
    battle.status = "round_1_generating" 
    await db.commit()

    # Создаем участников
    models = ["phi3", "mistral"]
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

    prompt = f"Ответь на следующий вопрос кратко и по делу: {battle.question}"

    # Параллельная генерация
    async def get_response(participant: Participant):
        try:
            result = await ollama_client.generate_response(
                model=participant.model_name, 
                prompt=prompt
            )
            return {
                "participant": participant,
                "content": result.get("response", ""),
                "tokens": result.get("eval_count", 0)
            }
        except Exception as e:
            logger.error(f"Error generating response for {participant.model_name}: {e}")
            return None

    responses_data = await asyncio.gather(*(get_response(p) for p in participants))

    # Статус для UI: сохраняем результаты
    battle.status = "round_1_saving"
    await db.commit()

    for data in responses_data:
        if data is None:
            continue
        
        response = Response(
            battle_id=battle.id,
            participant_id=data["participant"].id,
            round=1,
            content=data["content"],
            tokens_used=data["tokens"]
        )
        db.add(response)
    
    battle.status = "round_1_finished"
    await db.commit()
    logger.info(f"Battle {battle_id} Round 1 completed successfully.")


async def run_battle_round_2(battle_id: str, db: AsyncSession):
    """
    Раунд 2: Каждый агент критикует ответ другого агента.
    """
    logger.info(f"Starting Round 2 (Critique) for battle {battle_id}")

    result = await db.execute(select(Battle).where(Battle.id == battle_id))
    battle = result.scalar_one_or_none()

    # Статус для UI: модели пишут критику
    battle.status = "round_2_critiquing"
    await db.commit()
    
    # Достаем ответы первого раунда
    result = await db.execute(
        select(Response)
        .options(selectinload(Response.participant))
        .where(Response.battle_id == battle_id, Response.round == 1)
    )
    responses = result.scalars().all()
    
    if len(responses) < 2:
        logger.error("Not enough responses for cross-critique")
        battle.status = "failed"
        await db.commit()
        return

    async def generate_critique(author_resp: Response, target_resp: Response):
        # ЖЕСТКИЙ ПРОМПТ: требуем краткость и строгий формат оценки в конце
        prompt = (
            f"Вопрос: {battle.question}\n\n"
            f"Ответ другого агента: {target_resp.content}\n\n"
            f"Твоя задача: раскритикуй этот ответ по существу. Будь краток (максимум 3 предложения).\n"
            f"ВАЖНО: В самом конце твоего ответа напиши ТОЛЬКО одну оценку в формате 'Оценка: X', где X - это число от 1 до 10. Не пиши больше ничего после оценки!"
        )
        
        try:
            result = await ollama_client.generate_response(
                model=author_resp.participant.model_name, 
                prompt=prompt
            )
            content = result.get("response", "")
            
            # Ищем ВСЕ совпадения и берем ПОСЛЕДНЕЕ (то, что в самом конце)
            matches = re.findall(r"Оценка:\s*(\d+)", content)
            if matches:
                score = int(matches[-1]) 
            else:
                score = 5
                
            score = max(1, min(10, score)) # Ограничиваем от 1 до 10
            
            return {
                "author": author_resp.participant_id,
                "target_response_id": target_resp.id,
                "content": content,
                "score": score
            }
        except Exception as e:
            logger.error(f"Error during critique: {e}")
            # Если модель упала, ставим дефолтную критику, чтобы не терять баллы
            return {
                "author": author_resp.participant_id,
                "target_response_id": target_resp.id,
                "content": "Модель не смогла сгенерировать критику из-за таймаута.",
                "score": 5 
            }

    # Перекрестная критика (параллельно)
    tasks = [
        generate_critique(responses[0], responses[1]), # Агент 1 критикует Агента 2
        generate_critique(responses[1], responses[0])  # Агент 2 критикует Агента 1
    ]
    
    critique_results = await asyncio.gather(*tasks)

    for data in critique_results:
        critique = Critique(
            battle_id=battle.id,
            author_participant_id=data["author"],
            target_response_id=data["target_response_id"],
            content=data["content"],
            score=data["score"]
        )
        db.add(critique)
        
    battle.status = "round_2_finished"
    await db.commit()
    logger.info(f"Round 2 (Critique) completed for battle {battle_id}")


async def run_battle_judge(battle_id: str, db: AsyncSession):
    """
    Финал: Независимый суд на основе оригинальных ответов.
    """
    logger.info(f"Starting Judge for battle {battle_id}")

    result = await db.execute(select(Battle).where(Battle.id == battle_id))
    battle = result.scalar_one_or_none()

    # Статус для UI: Судья думает
    battle.status = "judge_thinking"
    await db.commit()
    
    # Получаем ответы 1-го раунда
    result = await db.execute(
        select(Response)
        .options(selectinload(Response.participant))
        .where(Response.battle_id == battle_id, Response.round == 1)
    )
    responses = result.scalars().all()
    
    if len(responses) < 2:
        logger.error("Not enough responses for judging")
        battle.status = "failed"
        await db.commit()
        return

    # Готовим промпт для Судьи (Mistral), давая ему прочитать оба ответа
    resp1 = responses[0]
    resp2 = responses[1]
    
    prompt = (
        f"Вопрос пользователя: {battle.question}\n\n"
        f"Ответ участника {resp1.participant.display_name}:\n{resp1.content}\n\n"
        f"Ответ участника {resp2.participant.display_name}:\n{resp2.content}\n\n"
        f"Ты — беспристрастный судья. Какой из этих двух ответов лучше и полезнее для пользователя?\n"
        f"Напиши короткое резюме (2-3 предложения) на РУССКОМ языке, объясняя, почему ты выбрал этого победителя.\n"
        f"В самом конце напиши строго: 'Победитель: [ТОЧНОЕ ИМЯ УЧАСТНИКА]' (выбери одно из двух имен)."
    )
    
    try:
        # Судьей всегда выступает mistral, так как она умнее
        judge_result = await ollama_client.generate_response(model="mistral", prompt=prompt)
        summary = judge_result.get("response", "")
        battle.judge_summary = summary
        
        # Пытаемся понять, кого выбрал судья
        winner = resp1.participant # По умолчанию первый
        if resp2.participant.display_name.lower() in summary.lower() and resp1.participant.display_name.lower() not in summary.lower():
            winner = resp2.participant
        else:
            # Более надежный поиск в конце текста (после слова "Победитель:")
            match = re.search(r"Победитель:\s*(.+)", summary, re.IGNORECASE)
            if match:
                winner_name = match.group(1).strip().lower()
                if resp2.participant.display_name.lower() in winner_name:
                    winner = resp2.participant
                elif resp1.participant.display_name.lower() in winner_name:
                    winner = resp1.participant

        battle.winner_participant_id = winner.id
        
    except Exception as e:
        logger.error(f"Judge LLM error: {e}")
        battle.judge_summary = "Судья не смог вынести вердикт из-за ошибки."
        battle.winner_participant_id = resp1.participant.id # Дефолт

    # Обновляем баллы (чтобы в UI было красиво)
    result = await db.execute(select(Critique).where(Critique.battle_id == battle_id))
    critiques = result.scalars().all()
    scores = {resp1.participant.id: 0, resp2.participant.id: 0}
    resp_to_participant = {r.id: r.participant_id for r in responses}
    
    for c in critiques:
        target_id = resp_to_participant.get(c.target_response_id)
        if target_id in scores:
            scores[target_id] += c.score

    for p in [resp1.participant, resp2.participant]:
        p.total_score = scores.get(p.id, 0)

    battle.status = "completed"
    await db.commit()
    logger.info(f"Battle {battle_id} finished. Winner: {battle.winner_participant_id}")