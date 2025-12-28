import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import settings
from database import engine, Base, get_db
from handlers import register_all_handlers
from utils.scheduler import start_scheduler

async def main():
    bot = Bot(token=settings.BOT_TOKEN,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    register_all_handlers(dp)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Middleware для сессии
    @dp.update.outer_middleware()
    async def db_session_middleware(handler, event, data):
        async for session in get_db():
            data['session'] = session
            return await handler(event, data)

    start_scheduler(bot)

    print("Bot is running... Press Ctrl+C to stop")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        print("Bot has been stopped")

if __name__ == "__main__":
    asyncio.run(main())