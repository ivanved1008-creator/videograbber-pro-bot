import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

# Импортируем наши модули
import config
from downloader import VideoDownloader

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация
bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
downloader = VideoDownloader()

# Создаем папку для загрузок
os.makedirs('downloads', exist_ok=True)

# ========== КЛАВИАТУРЫ (ваше "оформление") ==========
def main_menu_keyboard():
    """Главное меню после команды /start"""
    keyboard = [
        [InlineKeyboardButton(text="🎬 Скачать видео", callback_data="download")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help"),
         InlineKeyboardButton(text="📊 Статус", callback_data="status")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def quality_keyboard():
    """Клавиатура выбора качества (пример)"""
    keyboard = [
        [InlineKeyboardButton(text="📱 720p (Стандарт)", callback_data="quality_720")],
        [InlineKeyboardButton(text="💻 1080p (HD)", callback_data="quality_1080")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# ========== ОБРАБОТЧИКИ КОМАНД ==========
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start с приветственным сообщением"""
    welcome_text = (
        "🚀 <b>Добро пожаловать в YouTube & TikTok Downloader!</b>\n\n"
        "Я помогу скачать видео с популярных платформ быстро и без водяных знаков.\n\n"
        "✏️ <b>Как пользоваться:</b>\n"
        "1. Просто отправьте мне ссылку на видео\n"
        "2. Я проверю её и предложу варианты\n"
        "3. Выберите качество и получите файл!\n\n"
        "✅ <b>Поддерживаются:</b> YouTube, TikTok, Instagram, VK"
    )
    await message.answer(welcome_text, reply_markup=main_menu_keyboard())

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    help_text = (
        "📖 <b>Справка</b>\n\n"
        "• Отправьте прямую ссылку на видео (например, <code>https://www.youtube.com/watch?v=...</code>)\n"
        "• Бот автоматически определит источник и начнет обработку.\n"
        "• Выберите желаемое качество из предложенных вариантов.\n"
        "• Дождитесь завершения загрузки — файл будет отправлен в этот чат.\n\n"
        "⏱ <i>Скачивание может занять от нескольких секунд до пары минут в зависимости от размера видео и нагрузки на сервер.</i>"
    )
    await message.answer(help_text)

# ========== ОСНОВНОЙ ОБРАБОТЧИК ССЫЛОК ==========
@dp.message(F.text)
async def handle_link(message: types.Message):
    """Обрабатывает текстовые сообщения, проверяя, является ли оно ссылкой"""
    url = message.text.strip()
    
    # Простая проверка на наличие поддерживаемого домена
    if not any(domain in url for domain in config.SUPPORTED_DOMAINS):
        await message.answer("❌ Это не похоже на ссылку с поддерживаемой платформы (YouTube, TikTok и т.д.).")
        return

    # Сообщаем пользователю, что начали работу
    status_msg = await message.answer("🔍 <i>Анализирую ссылку...</i>")

    try:
        # Получаем информацию о видео
        video_info = await downloader.get_video_info(url)
        if not video_info:
            await status_msg.edit_text("⚠️ Не удалось получить информацию о видео. Проверьте ссылку.")
            return

        # Показываем информацию и предлагаем выбрать качество
        info_text = (
            f"🎥 <b>Найдено видео:</b>\n"
            f"• <b>Название:</b> {video_info['title']}\n"
            f"• <b>Автор:</b> {video_info['uploader']}\n"
            f"• <b>Длительность:</b> {video_info['duration']} сек.\n\n"
            f"<i>Выберите качество для скачивания:</i>"
        )
        await status_msg.edit_text(info_text, reply_markup=quality_keyboard())

    except Exception as e:
        logger.error(f"Ошибка обработки ссылки {url}: {e}")
        await status_msg.edit_text("⚠️ При обработке запроса произошла ошибка. Попробуйте позже.")

# ========== ОБРАБОТЧИКИ НАЖАТИЙ НА КНОПКИ (CALLBACK) ==========
@dp.callback_query(F.data == "download")
async def process_download_callback(callback: types.CallbackQuery):
    """Обработчик нажатия кнопки 'Скачать видео'"""
    await callback.message.edit_text("📥 Отправьте мне ссылку на видео...")
    await callback.answer()

@dp.callback_query(F.data.startswith("quality_"))
async def process_quality_callback(callback: types.CallbackQuery):
    """Обработчик выбора качества и запуск скачивания"""
    # Здесь можно передать выбранное качество в downloader (опущено для простоты)
    await callback.message.edit_text("⏳ <i>Начинаю скачивание... Это может занять некоторое время.</i>")
    
    # Извлекаем URL из текста предыдущего сообщения (упрощенный способ)
    # В реальном боте URL нужно передавать между состояниями
    original_text = callback.message.text
    # Поиск URL в тексте (простая реализация)
    import re
    url_match = re.search(r'https?://[^\s]+', original_text)
    
    if url_match:
        url = url_match.group(0)
        # Скачиваем видео
        file_path = await downloader.download_video(url, callback.from_user.id)
        
        if file_path and os.path.exists(file_path):
            # Отправляем видео пользователю
            with open(file_path, 'rb') as video_file:
                await bot.send_video(callback.from_user.id, video_file, caption="✅ Ваше видео готово!")
            # Удаляем временный файл
            os.remove(file_path)
        else:
            await callback.message.answer("❌ Не удалось скачать видео.")
    else:
        await callback.message.answer("⚠️ Не могу найти ссылку для скачивания. Отправьте её снова.")
    
    await callback.answer()

# ========== ЗАПУСК БОТА ==========
async def main():
    """Главная функция для запуска бота"""
    logger.info("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
