import asyncio
import signal
from telethon import TelegramClient, events

# ============ ВСТАВЬ СВОИ ДАННЫЕ ЗДЕСЬ ============
API_ID = 36849897
API_HASH = '3b1f361c18993639ae7eab250eb51ab8'
BOT_TOKEN = '8550747360:AAF0nhq9CMRhVgplUSeP7JWCbCNqo3NkNXs'
DOWNLOADER_BOT = '@GozillaDownloader'
# =================================================

# Создаем клиентов (но пока НЕ запускаем)
user_client = TelegramClient('user_session', API_ID, API_HASH)
bot_client = TelegramClient('bot_session', API_ID, API_HASH)

# 1. ОПРЕДЕЛЯЕМ ФУНКЦИИ-ОБРАБОТЧИКИ (как обычные функции)
async def handle_start(event):
    """Обрабатывает команду /start"""
    await event.reply('Привет! Я Videograbber Pro Bot. Присылай мне ссылку на видео с YouTube или TikTok.')

async def handle_message(event):
    """Обрабатывает все текстовые сообщения (ссылки)"""
    msg_text = event.message.message
    user = await event.get_sender()

    # Если это не ссылка - игнорируем
    if not ('youtu' in msg_text or 'tiktok' in msg_text):
        return

    await event.reply('🔄 Принял! Передаю запрос загрузчику @GozillaDownloader. Ожидайте...')

    try:
        # 1. Ваш аккаунт отправляет ссылку Gozilla-боту
        async with user_client:
            await user_client.send_message(DOWNLOADER_BOT, msg_text)
            await asyncio.sleep(30)  # Даем время на обработку

        # 2. Ищем в чате с Gozilla результат (видеофайл)
        async with user_client:
            messages = await user_client.get_messages(DOWNLOADER_BOT, limit=5)
            for msg in messages:
                # Если сообщение содержит видео или документ-видео
                if msg.video or (msg.document and 'video' in str(msg.document.mime_type)):
                    # 3. Пересылаем найденное видео пользователю
                    await bot_client.send_message(user.id, '✅ Видео готово! Скачиваю...')
                    await user_client.forward_messages(user.id, msg)
                    return  # Выходим, если нашли и переслали

        # Если после цикла файл не нашелся
        await event.reply('❌ Не удалось получить видео от загрузчика. Попробуйте другую ссылку.')

    except Exception as e:
        await event.reply(f'⚠️ Произошла техническая ошибка: {str(e)}')

async def shutdown(signal, loop):
    """Корректно завершает работу бота"""
    print(f"\n🛑 Получен сигнал {signal.name}, завершаю работу...")
    # Отключаем клиентов
    if user_client.is_connected():
        await user_client.disconnect()
    if bot_client.is_connected():
        await bot_client.disconnect()
    # Останавливаем цикл событий
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()
    print("✅ Бот корректно завершил работу.")

# 2. ГЛАВНАЯ ФУНКЦИЯ, которая всё настраивает и запускает
async def main():
    print("🤖 Запуск бота...")

    # Настраиваем обработку сигналов для graceful shutdown
    loop = asyncio.get_running_loop()
    for sig_name in ('SIGINT', 'SIGTERM'):
        sig = getattr(signal, sig_name, None)
        if sig:
            loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s, loop)))

    # ЗАПУСКАЕМ КЛИЕНТОВ и регистрируем обработчики
    print("🔐 Авторизация аккаунта... (введите номер телефона и код, если потребуется)")
    await user_client.start()
    print("✅ Аккаунт авторизован!")

    # Регистрируем обработчики событий для бота
    bot_client.add_event_handler(handle_start, events.NewMessage(pattern='/start'))
    bot_client.add_event_handler(handle_message, events.NewMessage())

    # Запускаем бота
    await bot_client.start(bot_token=BOT_TOKEN)
    print(f"🎉 Бот @videograbber_pro_bot запущен и работает!")
    print("❓ Отправьте ему /start в Telegram, чтобы начать.")

    # Бот работает, пока не получит сигнал на остановку
    await bot_client.run_until_disconnected()

# 3. ТОЧКА ВХОДА
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nРучная остановка.")
    except Exception as e:
        print(f"💥 Критическая ошибка при запуске: {e}")
    finally:
        print("Работа скрипта завершена.")
