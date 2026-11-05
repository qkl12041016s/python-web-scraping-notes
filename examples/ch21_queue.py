"""Simulate duplicate task delivery with two local workers."""

from queue import Empty, Queue
from threading import Lock, Thread


tasks = Queue()
for item_id in (1, 2, 1, 3, 2):
    tasks.put(item_id)

seen = set()
lock = Lock()


def worker() -> None:
    while True:
        try:
            item_id = tasks.get_nowait()
        except Empty:
            return
        try:
            with lock:
                seen.add(item_id)
        finally:
            tasks.task_done()


workers = [Thread(target=worker) for _ in range(2)]
for thread in workers:
    thread.start()
tasks.join()
for thread in workers:
    thread.join()
print("unique items:", sorted(seen))
