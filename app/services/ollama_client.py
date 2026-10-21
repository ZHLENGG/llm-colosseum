import httpx
import logging

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        # По умолчанию Ollama крутится на этом порту
        self.base_url = base_url

    async def generate_response(self, model: str, prompt: str) -> dict:
        """
        Отправляет промпт в Ollama и возвращает ответ.
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 300  # <-- Максимум 300 токенов на ответ. Зацикливаться не сможет.
            }
        }

        # Используем асинхронный клиент httpx
        async with httpx.AsyncClient() as client:
            try:
                # timeout=120.0, потому что локальные модели могут думать долго
                response = await client.post(url, json=payload, timeout=300.0)
                response.raise_for_status() # Если ошибка 4xx или 5xx - выбросит исключение
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Ollama API error: {e.response.status_code} - {e.response.text}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Network error connecting to Ollama: {e}")
                raise

# Создаем экземпляр, который будем переиспользовать
ollama_client = OllamaClient()