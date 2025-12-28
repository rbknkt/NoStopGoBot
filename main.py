import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import settings

async def main():
    bot = Bot(token=settings.BOT_TOKEN,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    print("Bot is running... Press Ctrl+C to stop")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        print("Bot has been stopped")

if __name__ == "__main__":
    asyncio.run(main())