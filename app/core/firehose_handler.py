from __future__ import annotations

"""
Logging handler that sends log records to AWS Kinesis Data Firehose.

Configure via env: LOG_DESTINATION=firehose and FIREHOSE_DELIVERY_STREAM_NAME.
Credentials use the default boto3 chain (env vars or IAM role).
"""

import logging
import threading
import time
from typing import Any

from app.core.firehose_client import get_firehose_client


class FirehoseHandler(logging.Handler):
    """
    Buffers log records and sends them to AWS Kinesis Data Firehose in batches.
    Flushes when buffer reaches batch_size or every flush_interval_seconds (so low
    traffic still gets sent). Thread-safe.
    """

    def __init__(
        self,
        delivery_stream_name: str,
        region_name: str | None = None,
        batch_size: int = 10,
        flush_interval_seconds: float = 5.0,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        if not delivery_stream_name or not delivery_stream_name.strip():
            raise ValueError("FirehoseHandler requires a non-empty delivery_stream_name")
        self._delivery_stream_name = delivery_stream_name.strip()
        self._region_name = (region_name or "").strip() or None
        self._batch_size = max(1, min(500, batch_size))  # Firehose limit 500
        self._flush_interval = max(1.0, min(300.0, flush_interval_seconds))
        self._buffer: list[bytes] = []
        self._lock = threading.Lock()
        self._shutdown = threading.Event()
        self._flusher = threading.Thread(target=self._flush_loop, daemon=True)
        self._flusher.start()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
            if not message:
                return
            # Firehose record data is blob; we send UTF-8 JSON line
            data = message.encode("utf-8")
        except Exception:  # noqa: S110
            self.handleError(record)
            return

        with self._lock:
            self._buffer.append(data)
            if len(self._buffer) >= self._batch_size:
                self._flush_locked()

    def _flush_loop(self) -> None:
        """Periodically flush buffer so logs are sent even when traffic is low."""
        while not self._shutdown.wait(timeout=self._flush_interval):
            self.flush()

    def _flush_locked(self) -> None:
        if not self._buffer:
            return
        records = self._buffer
        self._buffer = []
        # Release lock before I/O so other threads can buffer
        # We already moved buffer to local var
        try:
            client = get_firehose_client(region_name=self._region_name)
            # put_record_batch accepts max 500 records, 4MB total
            batch = [{"Data": r} for r in records]
            client.put_record_batch(
                DeliveryStreamName=self._delivery_stream_name,
                Records=batch,
            )
        except Exception:  # noqa: BLE001
            logging.getLogger(__name__).exception("Firehose put_record_batch failed")

    def flush(self) -> None:
        with self._lock:
            self._flush_locked()

    def close(self) -> None:
        self._shutdown.set()
        with self._lock:
            self._flush_locked()
        super().close()
