import yt_dlp
import asyncio
from typing import Optional, Dict

class VideoDownloader:
    def __init__(self):
        self.ydl_opts = {
            'format': 'best[height<=1080]',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'extractor_args': {
                'tiktok': {'format': 'download_addr'}
            }
        }

    async def get_video_info(self, url: str) -> Optional[Dict]:
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
            print(f"Ошибка получения информации: {e}")
            return None

    async def download_video(self, url: str, chat_id: int) -> Optional[str]:
        output_template = f'downloads/%(title).50s_{chat_id}.%(ext)s'
        opts = self.ydl_opts.copy()
        opts['outtmpl'] = output_template
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, lambda: ydl.download([url]))
                return output_template.replace('%(title).50s', 'видео').replace('%(ext)s', 'mp4')
        except Exception as e:
            print(f"Ошибка скачивания: {e}")
            return None
