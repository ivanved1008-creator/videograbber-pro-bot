import os, asyncio, signal
from telethon import TelegramClient, events

# ============ ВСТАВЬ СВОИ ДАННЫЕ ЗДЕСЬ ============
API_ID = 36849897
API_HASH = '3b1f361c18993639ae7eab250eb51ab8'
BOT_TOKEN = '8550747360:AAF0nhq9CMRhVgplUSeP7JWCbCNqo3NkNXs'
DOWNLOADER_BOT = '@GozillaDownloader'
# =================================================

# Глобальные переменные для клиентов
user_client = None
bot_client = None

async def shutdown():
    """Корректно завершает работу бота, отключая клиентов."""
    print("🛑 Получен сигнал на завершение работы...")
    if user_client and user_client.is_connected():
        await user_client.disconnect()
        print("✅ User client отключен.")
    if bot_client and bot_client.is_connected():
        await bot_client.disconnect()
        print("✅ Bot client отключен.")
    # Даем время на завершение всех задач
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [t.cancel() for t in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    print("✅ Все задачи завершены.")

@bot_client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    await event.reply('Привет! Я Videograbber Pro Bot. Присылай мне ссылку на видео с YouTube или TikTok.')

@bot_client.on(events.NewMessage())
async def link_handler(event):
    msg_text = event.message.message
    user = await event.get_sender()
    if not ('youtu' in msg_text or 'tiktok' in msg_text):
        return
    await event.reply('🔄 Принял! Передаю запрос загрузчику @GozillaDownloader. Ожидайте...')
    try:
        async with user_client:
            await user_client.send_message(DOWNLOADER_BOT, msg_text)
            await asyncio.sleep(25)
            messages = await user_client.get_messages(DOWNLOADER_BOT, limit=5)
            for msg in messages:
                if msg.video or (msg.document and 'video' in str(msg.document.mime_type)):
                    await bot_client.send_message(user.id, '✅ Видео готово! Скачиваю...')
                    await user_client.forward_messages(user.id, msg)
                    return
        await event.reply('❌ Не удалось получить видео от загрузчика. Попробуйте другую ссылку.')
    except Exception as e:
        await event.reply(f'⚠️ Ошибка: {str(e)}')

async def main():
    global user_client, bot_client
    print("🤖 Запуск бота...")
    
    # Создаем клиентов с путями к сессиям в рабочей директории
    user_client = TelegramClient('user_session', API_ID, API_HASH)
    bot_client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

    # Регистрируем обработчик сигналов для graceful shutdown
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))

    print("🔐 Начало авторизации...")
    await user_client.start()
    print("✅ Аккаунт авторизован!")
    await bot_client.start()
    print(f"🎉 Бот запущен и работает!")
    
    # Запускаем бота на постоянную работу
    await bot_client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Ручная остановка.")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
    finally:
        print("Бот завершил работу.")
