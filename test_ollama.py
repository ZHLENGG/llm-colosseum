import asyncio
from app.services.ollama_client import ollama_client

async def main():
    print("Отправляем запрос в Ollama...")
    try:
        # Убедись, что модель phi3 скачана (ollama pull phi3)
        result = await ollama_client.generate_response(
            model="phi3", 
            prompt="Привет! Напиши одно короткое предложение о том, кто ты."
        )
        print("\nОтвет от модели:")
        print(result.get("response"))
    except Exception as e:
        print(f"\nОшибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())