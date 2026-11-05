"""Keep each task's identifier when one concurrent task fails."""

import asyncio


async def one(item_id):
    await asyncio.sleep(0.01)
    if item_id == 2:
        raise TimeoutError("local simulation timed out")
    return f"item-{item_id}"


async def run():
    results = await asyncio.gather(*(one(i) for i in range(4)), return_exceptions=True)
    successes, failures = [], []
    for item_id, result in enumerate(results):
        if isinstance(result, BaseException):
            failures.append((item_id, type(result).__name__))
        else:
            successes.append(result)
    return successes, failures


if __name__ == "__main__":
    ok, bad = asyncio.run(run())
    assert ok == ["item-0", "item-1", "item-3"]
    assert bad == [(2, "TimeoutError")]
    print("ok=3, failed=1, failed_id=2")
