from aiogram import Router, types, Bot
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

from app.db.requests import set_task, update_user_experience, delete_task, get_tasks, get_user_profile, get_task_by_id, get_leaderboard, EXP_POINTS
from datetime import datetime, timedelta

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(f'Добро пожаловать в ToDoUppBot, {message.from_user.first_name}. \nСтановитесь лучше и стремитесь к успеху :) \nМы поможем вам в этом, взяв на себя планирование. \nДля ознакомления введите /help')


@router.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer(f'''Все команды:
/task_list - список заданий, но отдельно:
/daily - ежедневные задания
/weekly - еженедельные задания
=============================
Сложность заданий и награда за них (опыт):
- daily (ежедневные): 10
- weekly (еженедельные): 25,
- easy (легкие): 25,
- medium (средние): 50,
- hard (сложные): 100,
- hell (безумные/адские): 250
=============================
/create_task - создать задание, /create_task <сложность> <задание>
/done - выполнить задание
/delete_task - удалить задание, /delete_task <id задания>
=============================
/profile - ваш профиль
/leader - топ 20 пользователей''')

#реклама - https://t.me/+Gf1TENQ5DAIyYmUy (канал создателя бота)
@router.message(Command("create_task"))
async def create_task(message: types.Message):
    try:
        _, lvl, *task_text = message.text.split()
        task_text = " ".join(task_text)
        if len(task_text) > 100:
            await message.reply("Текст задачи не должен превышать 100 символов.")
            return
        
        tasks = await get_tasks(message.from_user.id, message.from_user.first_name)
        daily_tasks = [task for task in tasks if task.lvl == 'daily']
        weekly_tasks = [task for task in tasks if task.lvl == 'weekly']
        
        if lvl == 'daily' and len(daily_tasks) >= 10:
            await message.reply("Вы достигли лимита в 10 ежедневных задач.")
            return
        if lvl == 'weekly' and len(weekly_tasks) >= 25:
            await message.reply("Вы достигли лимита в 25 еженедельных задач.")
            return
        
        await set_task(message.from_user.id, task_text, lvl)
        await update_user_experience(message.from_user.id, lvl)
        await message.reply(f"Задача '{task_text}' уровня '{lvl}' создана.")
    except ValueError:
        await message.reply("Использование: /create_task <уровень> <текст задачи>")


@router.message(Command('done'))
async def cmd_done_task(message: Message):
    try:
        _, task_id = message.text.split()
        task_id = int(task_id)
        task = await get_task_by_id(task_id)
        if task and task.user == (await get_user_profile(message.from_user.id)).id:
            if task.lvl == 'daily':
                now = datetime.utcnow()
                next_due = datetime(now.year, now.month, now.day) + timedelta(days=1)
                task.next_due = next_due
                await message.reply(f"Ежедневная задача с ID {task_id} выполнена и будет доступна завтра в 00:00 UTC.")
            elif task.lvl == 'weekly':
                now = datetime.utcnow()
                next_due = datetime(now.year, now.month, now.day) + timedelta(days=(7 - now.weekday()))
                task.next_due = next_due
                await message.reply(f"Еженедельная задача с ID {task_id} выполнена и будет доступна в следующий понедельник в 00:00 UTC.")
            else:
                await delete_task(task_id)
                await message.reply(f"Задача с ID {task_id} выполнена и удалена.")
        elif task:
            await message.reply(f"Вы не можете выполнить задачу с ID {task_id}, так как она не принадлежит вам.")
        else:
            await message.reply(f"Задача с ID {task_id} не найдена.")
    except ValueError:
        await message.reply("Использование: /done <ID задачи>")

#реклама - https://t.me/+Gf1TENQ5DAIyYmUy (канал создателя бота)
@router.message(Command('task_list'))
async def cmd_task_list(message: Message):
    tasks = await get_tasks(message.from_user.id, message.from_user.first_name)
    non_recurring_tasks = [task for task in tasks if task.lvl not in ['daily', 'weekly']]
    if non_recurring_tasks:
        response = "Ваши задачи:\n"
        for task in sorted(non_recurring_tasks, key=lambda x: EXP_POINTS[x.lvl]):
            response += f"ID: {task.id}, Уровень: {task.lvl}, Задача: {task.task}\n"
        await message.reply(response)
    else:
        await message.reply("У вас нет задач.")


@router.message(Command('profile'))
async def cmd_profile(message: Message):
    user_profile = await get_user_profile(message.from_user.id)
    if user_profile:
        leaderboard = await get_leaderboard()
        rank = next((idx + 1 for idx, user in enumerate(leaderboard) if user.tg_id == message.from_user.id), None)
        exp_for_next_level = user_profile.level * 100
        response = (f"Профиль пользователя:\n"
                    f"Уровень: {user_profile.level} ({user_profile.exp}/{exp_for_next_level})\n"
                    f"Место в топе: {rank}")
        await message.reply(response)
    else:
        await message.reply("Профиль не найден.")


@router.message(Command('leader'))
async def cmd_leader(message: Message):
    leaderboard = await get_leaderboard()
    response = "Топ 20 пользователей:\n"
    for idx, user in enumerate(leaderboard, start=1):
        user_profile = await get_user_profile(user.tg_id)
        exp_for_next_level = user_profile.level * 100
        response += f"{idx}. {user_profile.first_name} - Уровень: {user.level} ({user_profile.exp}/{exp_for_next_level})\n"
    await message.reply(response)


@router.message(Command('daily'))
async def cmd_daily_tasks(message: Message):
    tasks = await get_tasks(message.from_user.id, message.from_user.first_name)
    daily_tasks = sorted([task for task in tasks if task.lvl == 'daily'], key=lambda x: EXP_POINTS[x.lvl])
    if daily_tasks:
        response = "Ваши ежедневные задачи:\n"
        for task in daily_tasks:
            response += f"ID: {task.id}, Уровень: {task.lvl}, Задача: {task.task}\n"
        await message.reply(response)
    else:
        await message.reply("У вас нет ежедневных задач.")


@router.message(Command('weekly'))
async def cmd_weekly_tasks(message: Message):
    tasks = await get_tasks(message.from_user.id, message.from_user.first_name)
    weekly_tasks = sorted([task for task in tasks if task.lvl == 'weekly'], key=lambda x: EXP_POINTS[x.lvl])
    if weekly_tasks:
        response = "Ваши еженедельные задачи:\n"
        for task in weekly_tasks:
            response += f"ID: {task.id}, Уровень: {task.lvl}, Задача: {task.task}\n"
        await message.reply(response)
    else:
        await message.reply("У вас нет еженедельных задач.")

#реклама - https://t.me/+Gf1TENQ5DAIyYmUy (канал создателя бота)
@router.message(Command('delete_task'))
async def cmd_delete_task(message: Message):
    try:
        _, task_id = message.text.split()
        task_id = int(task_id)
        task = await get_task_by_id(task_id)
        if task and task.user == (await get_user_profile(message.from_user.id)).id:
            await delete_task(task_id)
            await message.reply(f"Задача с ID {task_id} удалена.")
        elif task:
            await message.reply(f"Вы не можете удалить задачу с ID {task_id}, так как она не принадлежит вам.")
        else:
            await message.reply(f"Задача с ID {task_id} не найдена.")
    except ValueError:
        await message.reply("Использование: /delete_task <ID задачи>")


async def notify_user(bot: Bot, user_id: int, message: str):
    await bot.send_message(user_id, message)

