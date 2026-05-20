from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def user_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Активные мероприятия")
            ],
            [
                KeyboardButton(text="✅ Записаться на смену")
            ],
            [
                KeyboardButton(text="📌 Мои записи")
            ],
            [
                KeyboardButton(text="❌ Отказ от мероприятия")
            ],
            [
                KeyboardButton(text="✏️ Редактировать данные")
            ],
            [
                KeyboardButton(text="📞 Связь с менеджером")
            ]
        ],
        resize_keyboard=True
    )


def admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📅 Создать мероприятие")
            ],
            [
                KeyboardButton(text="➕ Добавить смену")
            ],
            [
                KeyboardButton(text="📋 Все мероприятия")
            ],
            [
                KeyboardButton(text="👥 Список персонала мероприятия")
            ],
            [
                KeyboardButton(text="✅ Подтвердить список")
            ],
            [
                KeyboardButton(text="❌ Отмена мероприятия")
            ],
            [
                KeyboardButton(text="🗑 Удалить участника")
            ],
            [
                KeyboardButton(text="📢 Массовый комментарий")
            ],
            [
                KeyboardButton(text="👤 Зарегистрированные пользователи")
            ],
            [
                KeyboardButton(text="🚫 Добавить в черный список")
            ],
            [
                KeyboardButton(text="♻️ Удалить из черного списка")
            ],
            [
                KeyboardButton(text="📛 Черный список")
            ]
        ],
        resize_keyboard=True
    )