from __future__ import annotations

"""
Lazy boto3 Firehose client for the FirehoseHandler.
Credentials: FIREHOSE_AWS_ACCESS_KEY_ID + FIREHOSE_AWS_SECRET_ACCESS_KEY, or default boto3 chain (IAM role / AWS_* env).
"""

import os
from functools import lru_cache
from typing import Any


@lru_cache(maxsize=1)
def get_firehose_client(region_name: str | None = None) -> Any:
    import boto3

    kwargs: dict[str, Any] = {}
    if region_name:
        kwargs["region_name"] = region_name

    access_key = (os.getenv("FIREHOSE_AWS_ACCESS_KEY_ID") or "").strip()
    secret_key = (os.getenv("FIREHOSE_AWS_SECRET_ACCESS_KEY") or "").strip()
    if access_key and secret_key:
        kwargs["aws_access_key_id"] = access_key
        kwargs["aws_secret_access_key"] = secret_key

    return boto3.client("firehose", **kwargs)
