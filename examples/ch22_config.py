"""Read validated runtime settings without printing secrets."""

import os
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    concurrency: int
    timeout_seconds: float
    has_token: bool


def load_settings() -> Settings:
    concurrency = int(os.getenv("CRAWL_CONCURRENCY", "2"))
    timeout = float(os.getenv("CRAWL_TIMEOUT", "10"))
    if not 1 <= concurrency <= 8:
        raise ValueError("concurrency must be between 1 and 8")
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be finite and positive")
    return Settings(concurrency, timeout, bool(os.getenv("CRAWL_TOKEN")))


if __name__ == "__main__":
    print(load_settings())
