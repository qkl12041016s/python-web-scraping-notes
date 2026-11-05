"""Demonstrate bounded concurrency without contacting a website."""

import asyncio
from time import perf_counter


async def fetch_like_task(item_id: int, limit: asyncio.Semaphore) -> str:
    async with limit:
        await asyncio.sleep(0.1)
        return f"item-{item_id}"


async def main() -> None:
    limit = asyncio.Semaphore(2)
    started = perf_counter()
    tasks = [fetch_like_task(i, limit) for i in range(5)]
    results = await asyncio.gather(*tasks)
    print(results)
    print(f"elapsed: {perf_counter() - started:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
