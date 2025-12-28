import re
from datetime import date
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models import User
from utils.scheduler import schedule_weekly_message

router = Router()

class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_birth_date = State()

@router.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await message.delete()
    reply = await message.answer("Как вас зовут?")
    await state.update_data(last_bot_message_id=reply.message_id)
    await state.set_state(RegistrationStates.waiting_for_name)

@router.message(RegistrationStates.waiting_for_name)
async def set_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        reply = await message.answer("Имя не может быть пустым. Введите имя.")
        await state.update_data(last_bot_message_id=reply.message_id)
        return

    data = await state.get_data()
    last_message_id = data.get("last_bot_message_id")
    if last_message_id:
        try:
            await message.bot.delete_message(message.chat.id, last_message_id)
        except Exception:
            pass

    await message.delete()
    await state.update_data(name=name)
    reply = await message.answer("Когда вы родились? Формат ДД.MM.ГГГГ")
    await state.update_data(last_bot_message_id=reply.message_id)
    await state.set_state(RegistrationStates.waiting_for_birth_date)

@router.message(RegistrationStates.waiting_for_birth_date)
async def set_birth_date(message: Message, state: FSMContext, session: AsyncSession):
    text = message.text.strip()
    if not re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", text):
        reply = await message.answer("Неверный формат. Используйте ДД.MM.ГГГГ")
        await state.update_data(last_bot_message_id=reply.message_id)
        return
    try:
        day, month, year = map(int, text.split("."))
        birth_date = date(year, month, day)
        if birth_date > date.today():
            raise ValueError
    except ValueError:
        reply = await message.answer("Некорректная дата. Повторите ввод.")
        await state.update_data(last_bot_message_id=reply.message_id)
        return

    data = await state.get_data()
    last_message_id = data.get("last_bot_message_id")
    if last_message_id:
        try:
            await message.bot.delete_message(message.chat.id, last_message_id)
        except Exception:
            pass

    await message.delete()
    telegram_id = message.from_user.id
    name = data["name"]

    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user:
        await session.execute(
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(name=name, birth_date=birth_date)
        )
    else:
        session.add(User(telegram_id=telegram_id, name=name, birth_date=birth_date))

    await session.commit()
    final_message = await message.answer(
        f"{name}, вы будете получать уведомления каждый понедельник в 9:00."
    )
    await session.execute(
        update(User)
        .where(User.telegram_id == telegram_id)
        .values(last_message_id=final_message.message_id)
    )
    await session.commit()
    schedule_weekly_message(message.bot, telegram_id)
    await state.clear()

def register_handlers(dp):
    dp.include_router(router)