import asyncio
import logging
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from config import TOKEN
from app.handlers import router
from app.db.models import async_main, async_session, User
from app.db.requests import get_tasks, get_users

bot = Bot(token=TOKEN)
dp = Dispatcher()


async def send_reminders():
    users = await get_users()
    for user in users:
        tasks = await get_tasks(user.tg_id, user.first_name)  # Передайте имя пользователя
        daily_tasks = [task for task in tasks if task.lvl == 'daily']
        weekly_tasks = [task for task in tasks if task.lvl == 'weekly']
        if daily_tasks:
            await bot.send_message(user.tg_id, "У вас есть невыполненные ежедневные задачи!")
        if weekly_tasks:
            await bot.send_message(user.tg_id, "У вас есть невыполненные еженедельные задачи!")


async def reset_daily_exp():
    async with async_session() as session:
        users = await session.scalars(select(User))
        for user in users:
            user.daily_exp = 0
        await session.commit()

#реклама - https://t.me/+Gf1TENQ5DAIyYmUy (канал создателя бота)
async def main():
    logging.basicConfig(level=logging.INFO)
    await async_main()  # Создание и обновление таблиц
    dp.include_router(router)
    
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_reminders, 'interval', hours=6)
    scheduler.add_job(reset_daily_exp, 'cron', hour=0)  # Сброс ежедневного опыта в полночь
    scheduler.start()
    
    await dp.start_polling(bot)  


if __name__ == '__main__': 
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("exit")
    except Exception as e:
        logging.error(f"An error occurred: {e}")