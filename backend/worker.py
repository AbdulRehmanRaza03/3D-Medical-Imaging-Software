"""
OrthoVision AI background worker (RQ).

Worker process that consumes reconstruction / segmentation jobs from the Redis
queue. Run separately from the web server:

    # local (threads) backend needs no separate worker.
    # redis backend:
    JOB_BACKEND=redis REDIS_URL=redis://localhost:6379/0 \
        python worker.py

In production, this worker should run on a machine with enough RAM (and
optionally a GPU for AI segmentation).
"""
from __future__ import annotations

import os
import sys

from redis import Redis
from rq import Queue, Worker

from app.core.config import settings


def main() -> int:
    if (settings.job_backend or "local").lower() != "redis":
        print(
            "JOB_BACKEND is not 'redis'; a separate worker is only needed for "
            "the Redis job backend.",
            file=sys.stderr,
        )
        return 1

    redis_conn = Redis.from_url(settings.redis_url, decode_responses=False)
    queue = Queue(settings.redis_queue, connection=redis_conn)

    worker = Worker([queue], connection=redis_conn)
    print(f"Worker started on queue '{settings.redis_queue}' (Redis: {settings.redis_url})")
    worker.work()


if __name__ == "__main__":
    sys.exit(main())
