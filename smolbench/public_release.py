"""Fetch released results from the public S3 bucket."""

from __future__ import annotations

import concurrent.futures
from pathlib import Path
from typing import Any

#: Maximum concurrent S3 object downloads.
FETCH_WORKERS = 32


def client(region: str) -> Any:
    """Create an anonymous S3 client for a public release bucket.

    Parameters
    ----------
    region : str
        Region containing the bucket.

    Returns
    -------
    Any
        An anonymous boto3 S3 client.
    """
    import boto3  # pylint: disable=import-outside-toplevel
    from botocore import UNSIGNED  # pylint: disable=import-outside-toplevel
    from botocore.config import Config  # pylint: disable=import-outside-toplevel

    config = Config(signature_version=UNSIGNED, max_pool_connections=FETCH_WORKERS)
    return boto3.client("s3", region_name=region, config=config)


def fetch(
    out: Path, bucket: str, prefix: str, root: str, client: Any
) -> tuple[int, int]:
    """Copy objects under an S3 key prefix into a local folder.

    Existing files with the same size are skipped. Downloads are written to a
    temporary ``.part`` file before replacing the destination, so interrupted
    fetches can be resumed safely.

    Parameters
    ----------
    out : Path
        Local destination folder.
    bucket : str
        Source bucket name.
    prefix : str
        S3 key prefix to list.
    root : str
        Key prefix removed when mapping object keys to local paths.
    client : Any
        A boto3 S3 client for ``bucket``.

    Returns
    -------
    tuple[int, int]
        Number of downloaded and skipped objects.
    """
    todo: list[tuple[str, Path]] = []
    skipped = 0
    for page in client.get_paginator("list_objects_v2").paginate(
        Bucket=bucket, Prefix=prefix
    ):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            dest = out / key.removeprefix(root)
            if dest.exists() and dest.stat().st_size == obj["Size"]:
                skipped += 1
            else:
                todo.append((key, dest))

    def get(job: tuple[str, Path]) -> None:
        key, dest = job
        dest.parent.mkdir(parents=True, exist_ok=True)
        part = dest.with_name(dest.name + ".part")
        part.write_bytes(client.get_object(Bucket=bucket, Key=key)["Body"].read())
        part.replace(dest)

    with concurrent.futures.ThreadPoolExecutor(max_workers=FETCH_WORKERS) as pool:
        list(pool.map(get, todo))
    return len(todo), skipped
