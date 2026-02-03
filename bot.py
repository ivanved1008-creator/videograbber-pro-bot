import os
import re
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode
import yt_dlp

# ==================== НАСТРОЙКИ ====================
# ЗАМЕНИТЕ ЭТИ ЗНАЧЕНИЯ НА СВОИ:
BOT_TOKEN = '8550747360:AAF0nhq9CMRhVgplUSeP7JWCbCNqo3NkNXs'  # Ваш токен от @BotFather
API_ID = 36849897  # Ваш api_id с my.telegram.org
API_HASH = '3b1f361c18993639ae7eab250eb51ab8'  # Ваш api_hash
YOUR_HOSTING_USERNAME = 'user123'  # Замените на ваш логин на Bothost или любое слово

# Список поддерживаемых платформ
SUPPORTED_DOMAINS = ['youtube.com', 'youtu.be', 'tiktok.com']

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== КЛАСС ДЛЯ СКАЧИВАНИЯ ВИДЕО ====================
class VideoDownloader:
    def __init__(self):
        self.ydl_opts = {
            'format': 'best[height<=1080]',
            'outtmpl': 'downloads/%(title).100s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'socket_timeout': 30,
            'retries': 3,
            'continuedl': True,
            'noprogress': True,
            'max_filesize': 10_000_000_000,
            'merge_output_format': 'mp4',
            'extractor_args': {
                'tiktok': {'format': 'download_addr'}
            }
        }
        os.makedirs('downloads', exist_ok=True)

    async def get_video_info(self, url: str):
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                loop = asyncio.get_event_loop()
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
                return {
                    'title': info.get('title', 'Без названия'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Неизвестно'),
                    'webpage_url': info.get('webpage_url', url)
                }
        except Exception as e:
            logger.error(f"Ошибка получения информации: {e}")
            return None

    async def download_video(self, url: str, chat_id: int):
        output_template = f'downloads/%(title).50s_{chat_id}.%(ext)s'
        opts = self.ydl_opts.copy()
        opts['outtmpl'] = output_template
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, lambda: ydl.download([url]))
                return output_template.replace('%(title).50s', 'video').replace('%(ext)s', 'mp4')
        except Exception as e:
            logger.error(f"Ошибка скачивания: {e}")
            return None

# ==================== ИНИЦИАЛИЗАЦИЯ БОТА ====================
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
downloader = VideoDownloader()

# ==================== КОМАНДЫ БОТА ====================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🚀 <b>Добро пожаловать в YouTube & TikTok Downloader!</b>\n\n"
        "Просто отправь мне ссылку на видео, и я скачаю его в качестве до 1080p.\n\n"
        "✅ <b>Поддерживаются:</b>\n"
        "• YouTube\n"
        "• TikTok (без водяного знака)\n\n"
        "⚡ <b>Бот оптимизирован для скорости!</b>",
        parse_mode='markdown'
    )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "📖 <b>Справка</b>\n\n"
        "• Отправьте прямую ссылку на видео\n"
        "• Бот автоматически определит источник и начнет обработку\n"
        "• Выберите качество (если доступно)\n"
        "• Получите готовое видео\n\n"
        "<i>Скачивание может занять от нескольких секунд до пары минут.</i>"
    )

# ==================== ОБРАБОТКА ССЫЛОК ====================
@dp.message(F.text)
async def handle_link(message: types.Message):
    # Ищем ссылку в тексте сообщения
    msg_text = message.text
    urls_found = []
    
    # Используем регулярное выражение для поиска ссылок
    url_pattern = re.compile(r'https?://\S+')
    urls_found = url_pattern.findall(msg_text)
    
    if not urls_found:
        await message.answer("❌ Не могу найти ссылку в вашем сообщении. Отправьте прямую ссылку.")
        return
    
    url = urls_found[0].strip().rstrip('.,;!?')
    
    # Проверяем, что это ссылка на поддерживаемую платформу
    if not any(domain in url for domain in SUPPORTED_DOMAINS):
        await message.answer("⚠️ Это не ссылка на поддерживаемую платформу (YouTube, TikTok).")
        return
    
    # Отправляем сообщение о начале обработки
    status_msg = await message.answer("🔍 <i>Анализирую ссылку...</i>")
    
    try:
        # Получаем информацию о видео
        video_info = await downloader.get_video_info(url)
        if not video_info:
            await status_msg.edit_text("❌ Не удалось получить информацию о видео. Проверьте ссылку.")
            return
        
        # Обновляем статус
        await status_msg.edit_text(
            f"🎬 <b>{video_info['title'][:50]}...</b>\n"
            f"👤 Автор: {video_info['uploader']}\n"
            f"⏱ Длительность: {video_info['duration']} сек.\n\n"
            f"<i>Начинаю загрузку...</i>"
        )
        
        # Скачиваем видео
        file_path = await downloader.download_video(url, message.chat.id)
        
        if file_path and os.path.exists(file_path):
            # Отправляем видео
            with open(file_path, 'rb') as video_file:
                await message.answer("✅ <b>Видео готово!</b>")
                await bot.send_video(
                    message.chat.id,
                    video_file,
                    caption=f"🎥 {video_info['title'][:50]}... (via @videograbber_pro_bot)"
                )
            # Удаляем временный файл
            os.remove(file_path)
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Не удалось скачать видео. Попробуйте другую ссылку.")
            
    except Exception as e:
        logger.error(f"Ошибка при скачивании {url}: {e}")
        await status_msg.edit_text(f"⚠️ Произошла ошибка при обработке: {str(e)[:200]}...")

# ==================== ЗАПУСК БОТА ====================
async def main():
    logger.info("Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
