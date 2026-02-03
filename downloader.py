import yt_dlp
import asyncio
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class VideoDownloader:
    def __init__(self):
        self.ydl_opts = {
            # Основные настройки
            'format': 'best[height<=1080]+bestaudio/best[height<=1080]',  # Качество до 1080p
            'outtmpl': 'downloads/%(title).100s.%(ext)s',  # Шаблон имени файла
            'quiet': False,  # Чтобы видеть прогресс в логах
            'no_warnings': False,
            'extract_flat': False,
            
            # Настройки для обхода блокировки 403 (YouTube)
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'player_skip': ['configs', 'webpage'],
                },
                'tiktok': {
                    'format': 'download_addr'  # Приоритет на версию без watermark
                }
            },
            
            # Ключевое: использование Deno для JavaScript (решает 403 ошибку)
            'postprocessor_args': {
                'sponsorblock': {'path': 'deno'},
            },
            
            # Настройки для имитации браузера
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            
            # Сетевые настройки
            'socket_timeout': 30,
            'retries': 10,
            'fragment_retries': 10,
            'skip_unavailable_fragments': True,
            'http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                'Referer': 'https://www.youtube.com/',
            },
            
            # Настройки для больших файлов
            'continuedl': True,
            'noprogress': False,
            'merge_output_format': 'mp4',
        }

    async def get_video_info(self, url: str) -> Optional[Dict]:
        """Получает информацию о видео без скачивания"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                loop = asyncio.get_event_loop()
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
                
                return {
                    'title': info.get('title', 'Без названия'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Неизвестно'),
                    'webpage_url': info.get('webpage_url', url),
                    'thumbnail': info.get('thumbnail'),
                    'view_count': info.get('view_count'),
                    'description': info.get('description', '')[:200] + '...' if info.get('description') else ''
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения информации: {e}")
            return None

    async def download_video(self, url: str, chat_id: int) -> Optional[str]:
        """Скачивает видео и возвращает путь к файлу"""
        try:
            # Уникальное имя файла для каждого пользователя
            output_template = f'downloads/%(title).50s_{chat_id}.%(ext)s'
            opts = self.ydl_opts.copy()
            opts['outtmpl'] = output_template
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, lambda: ydl.download([url]))
                
                # Получаем фактическое имя файла
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
                if info:
                    actual_filename = ydl.prepare_filename(info)
                    return actual_filename
                    
            return None
            
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"Ошибка скачивания yt-dlp: {e}")
            return None
        except Exception as e:
            logger.error(f"Общая ошибка скачивания: {e}")
            return None
