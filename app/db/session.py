from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# Создаем движок. echo=True будет выводить SQL-запросы в консоль (для отладки)
engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True
)

# Фабрика сессий (создает новые сессии для каждого запроса)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Зависимость для FastAPI, которая будет выдавать сессию и закрывать её после запроса
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session