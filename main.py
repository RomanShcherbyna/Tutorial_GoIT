
import asyncio
from telethon import TelegramClient
from datetime import datetime, timedelta
import pytz

api_id = 22896263
api_hash = '5492d2de3e4e98f48424278c9c77eea4'

SOURCE_GROUP = 'romaoferty'
tz = pytz.timezone("Europe/Warsaw")

# Ответ на конкретные сообщения в нужных темах
REPLY_TARGETS = [
    (-1002040577469, 144),     # Группа 1 — "Объекты аренда"
    (-1002096342149, 25188)    # Группа 2 — тема 3
]

client = TelegramClient('userbot_session', api_id, api_hash)

async def forward_latest_messages(limit=10):
    try:
        messages = await client.get_messages(SOURCE_GROUP, limit=limit)
        print(f"\n📤 Пересылаю {len(messages)} сообщений — {datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')}")
        for message in reversed(messages):
            if not message.message and not message.media:
                print("⚠️ Пропущено пустое сообщение")
                continue
            for chat_id, reply_id in REPLY_TARGETS:
                try:
                    if message.media:
                        await client.send_file(
                            entity=chat_id,
                            file=message.media,
                            caption=message.text or message.message,
                            reply_to=reply_id
                        )
                    else:
                        await client.send_message(
                            entity=chat_id,
                            message=message.text or message.message,
                            reply_to=reply_id
                        )
                    print(f"✅ Отправлено в {chat_id} (ответ на {reply_id})")
                except Exception as e:
                    print(f"❌ Ошибка отправки в {chat_id}: {e}")
    except Exception as e:
        print(f"❌ Ошибка получения сообщений из {SOURCE_GROUP}: {e}")

async def scheduler():
    while True:
        now = datetime.now(tz)
        times = [now.replace(hour=10, minute=0, second=0, microsecond=0),
                 now.replace(hour=19, minute=0, second=0, microsecond=0)]
        future = min((t for t in times if t > now), default=(now + timedelta(days=1)).replace(hour=10))
        wait_seconds = (future - now).total_seconds()
        print(f"⏳ Жду до {future.strftime('%H:%M')} ({int(wait_seconds)} секунд)")
        await asyncio.sleep(wait_seconds)
        await forward_latest_messages(limit=10)

async def main():
    await client.start()
    print("🚀 Userbot запущен.")
    await asyncio.gather(scheduler(), client.run_until_disconnected())

if __name__ == '__main__':
    asyncio.run(main())
