import asyncio
from datetime import date
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
from sqlalchemy import select, update
from database import AsyncSessionLocal
from models import User

scheduler = AsyncIOScheduler()

async def send_weekly_message(bot: Bot, user: User):
    today = date.today()
    weeks_lived = (today - user.birth_date).days // 7
    current_week = weeks_lived + 1
    text = (
        f"Здравствуйте, {user.name}!\n"
        f"Вы прожили {weeks_lived} неделю\n"
        f"Пошла {current_week}"
    )
    async with AsyncSessionLocal() as session:
        if user.last_message_id:
            try:
                await bot.delete_message(user.telegram_id, user.last_message_id)
            except Exception:
                pass
        message = await bot.send_message(user.telegram_id, text)
        await session.execute(
            update(User)
            .where(User.telegram_id == user.telegram_id)
            .values(last_message_id=message.message_id)
        )
        await session.commit()

async def weekly_job(bot: Bot, user_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()

    if user:
        await send_weekly_message(bot, user)

def schedule_weekly_message(bot: Bot, user_id: int):
    scheduler.add_job(
        weekly_job,
        CronTrigger(day_of_week="mon", hour=9, minute=00),
        args=[bot, user_id],
        id=f"user_{user_id}_weekly",
        replace_existing=True,
    )

async def load_scheduled_users(bot: Bot):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
    for user in users:
        schedule_weekly_message(bot, user.telegram_id)

def start_scheduler(bot: Bot):
    async def run():
        await load_scheduled_users(bot)
        scheduler.start()

    asyncio.create_task(run())