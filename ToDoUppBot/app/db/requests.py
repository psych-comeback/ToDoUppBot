from app.db.models import async_session
from app.db.models import User, Task
from sqlalchemy import select, delete, update

EXP_POINTS = {
    'daily': 10,
    'easy': 25,
    'weekly': 25,
    'medium': 50,
    'hard': 100,
    'hell': 250
}

def calculate_level(exp):
    level = 1
    while exp >= level * 100:
        exp -= level * 100
        level += 1
    return level, exp  # Возвращаем также оставшийся опыт

async def set_user(tg_id, first_name):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        
        if not user:
            session.add(User(tg_id=tg_id, first_name=first_name))
            await session.commit()

#реклама - https://t.me/+Gf1TENQ5DAIyYmUy (канал создателя бота)
async def update_user_experience(tg_id, lvl):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user:
            # Ограничение опыта в день
            if user.daily_exp + EXP_POINTS[lvl] > 1000:
                return
            user.exp += EXP_POINTS[lvl]
            user.daily_exp += EXP_POINTS[lvl]
            user.level, user.exp = calculate_level(user.exp)
            await session.commit()

async def get_tasks(tg_id, first_name):
    await set_user(tg_id, first_name)  # Передайте правильное имя пользователя
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            await set_user(tg_id, first_name)
            user = await session.scalar(select(User).where(User.tg_id == tg_id))
        tasks = await session.scalars(select(Task).where(Task.user == user.id))
        return tasks.all()
    

async def set_task(tg_id, task, lvl):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        session.add(Task(task=task, lvl=lvl, user=user.id))
        await session.commit()

async def delete_task(task_id):
    async with async_session() as session:
        task = await session.scalar(select(Task).where(Task.id == task_id))
        if task:
            await session.execute(delete(Task).where(Task.id == task_id))
            await session.commit()

async def get_user_profile(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        return user

#реклама - https://t.me/+Gf1TENQ5DAIyYmUy (канал создателя бота)
async def get_users():
    async with async_session() as session:
        users = await session.scalars(select(User))
        return users.all()

async def get_task_by_id(task_id):
    async with async_session() as session:
        task = await session.scalar(select(Task).where(Task.id == task_id))
        return task

async def get_leaderboard():
    async with async_session() as session:
        users = await session.scalars(select(User).order_by(User.level.desc(), User.exp.desc()).limit(20))
        return users.all()
