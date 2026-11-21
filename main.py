
import os
import asyncio
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from telethon import TelegramClient
from telethon.sessions import StringSession

MOSCOW = ZoneInfo("Europe/Moscow")

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION = os.environ["TELEGRAM_SESSION"]

SOURCE = os.getenv("SOURCE_CHAT", "BI CDA")
TARGET = os.getenv(
    "TARGET_CHAT",
    "AstraZeneca Public Affairs Department"
)

client = TelegramClient(
    StringSession(SESSION),
    API_ID,
    API_HASH
)


async def forward_document():
    now = datetime.now(MOSCOW)
    start = datetime.combine(
        now.date(), time(6, 0), MOSCOW
    )

    source = await client.get_entity(SOURCE)
    target = await client.get_entity(TARGET)

    selected = None

    async for msg in client.iter_messages(source, limit=100):
        sent_at = msg.date.astimezone(MOSCOW)

        if sent_at < start:
            break

        if sent_at > now:
            continue

        if not msg.file:
            continue

        filename = msg.file.name or ""

        if filename.startswith("Pharmaceutical"):
            selected = msg
            break

    if selected is None:
        print("Подходящий документ не найден")
        return

    # Проверяем, не пересылали ли его раньше.
    async for msg in client.iter_messages(target, limit=200):
        forwarded = msg.fwd_from

        if not forwarded:
            continue

        if (
            forwarded.channel_post == selected.id
            and forwarded.from_id == selected.peer_id
        ):
            print("Документ уже переслан")
            return

    await client.forward_messages(target, selected)
    print("Документ переслан:", selected.file.name)


async def main():
    await client.start()

    last_attempt = None

    while True:
        now = datetime.now(MOSCOW)

        if (
            now.weekday() < 5
            and now.hour == 8
            and now.minute == 0
            and last_attempt != now.date()
        ):
            last_attempt = now.date()

            try:
                await forward_document()
            except Exception as error:
                print("Ошибка:", error)

        await asyncio.sleep(10)


with client:
    client.loop.run_until_complete(main())

