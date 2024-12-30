from sqlalchemy import ForeignKey, String, BigInteger, Enum
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

from config import DB_URL

engine = create_async_engine(url=DB_URL,
                             echo=True)
    
async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)
    first_name: Mapped[str] = mapped_column(String(100))
    exp: Mapped[int] = mapped_column(default=0)
    level: Mapped[int] = mapped_column(default=1)
    daily_exp: Mapped[int] = mapped_column(default=0)  # Добавьте поле для ежедневного опыта

#реклама - https://t.me/+Gf1TENQ5DAIyYmUy (канал создателя бота)
class Task(Base):
    __tablename__ = 'tasks'

    id: Mapped[int] = mapped_column(primary_key=True)
    task: Mapped[str] = mapped_column(String(100))
    lvl: Mapped[str] = mapped_column(Enum('easy', 'medium', 'hard', 'hell', 'daily', 'weekly', name='lvl_enum'), nullable=False)
    user: Mapped[int] = mapped_column(ForeignKey('users.id'))


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Добавьте следующую строку для обновления существующих таблиц
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)