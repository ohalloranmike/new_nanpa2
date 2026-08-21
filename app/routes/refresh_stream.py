import asyncio
import json

from fastapi import Request

from app.ingest import database_timestamp, refresh_database


async def refresh_event_stream(request: Request, config):
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def progress(stage: str, message: str, percent: int) -> None:
        loop.call_soon_threadsafe(
            queue.put_nowait,
            {"stage": stage, "message": message, "percent": percent},
        )

    refresh_task = asyncio.create_task(asyncio.to_thread(refresh_database, config, True, progress))
    terminal_stages = {"complete", "error", "uptodate"}

    try:
        while True:
            try:
                item = await asyncio.wait_for(queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                if refresh_task.done() and queue.empty():
                    break
                continue

            yield f"data: {json.dumps(item)}\n\n"
            if item.get("stage") in terminal_stages:
                break

        await refresh_task
        request.app.state.db_last_updated = database_timestamp(config)
    except Exception as exc:
        payload = {"stage": "error", "message": f"Update failed: {exc}", "percent": 0}
        yield f"data: {json.dumps(payload)}\n\n"
