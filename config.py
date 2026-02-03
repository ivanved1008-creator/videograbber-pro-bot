import os

# Загружаем токен из переменной окружения BOT_TOKEN, которую вы зададите в панели Bothost
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("Ошибка: Переменная окружения 'BOT_TOKEN' не установлена. Задайте ее в настройках проекта на Bothost.")

# Список поддерживаемых доменов
SUPPORTED_DOMAINS = ['youtube.com', 'youtu.be', 'tiktok.com', 'instagram.com']
