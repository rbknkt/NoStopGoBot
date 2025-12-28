import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings
from database import engine, Base

async def main():
    bot = Bot(token=settings.BOT_TOKEN,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Bot is running... Press Ctrl+C to stop")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        print("Bot has been stopped")

if __name__ == "__main__":
    asyncio.run(main())