"""Share read-only S3 archive access to prevent notebook and test drift."""
from __future__ import annotations
import hashlib
import json
import posixpath
from typing import Any
from smolbench.evals import _aws
from smolbench.evals.results_store import parse_s3_uri

class S3Archive:
    """Stream objects from an ``s3://bucket/prefix`` archive root.

Parameters
----------
uri : str
    S3 archive-root URI.
region : str or None
    AWS region, or ``None`` for normal SDK resolution."""

    def __init__(self, uri: str, region: str | None=None) -> None:
        """Initialize a read-only archive handle.


Parameters
----------
uri : str
    S3 archive-root URI.
region : str or None
    AWS region, or ``None`` for normal SDK resolution."""
        self.bucket, self.prefix = parse_s3_uri(uri)
        self._client = _aws.fresh_client('s3', region)

    def _key(self, rel: str) -> str:
        """Resolve an archive-relative object key.


Parameters
----------
rel : str
    Archive-relative path.

Returns
-------
str
    Full bucket-relative object key."""
        normalized = posixpath.normpath(rel)
        return f'{self.prefix}/{normalized}' if self.prefix else normalized

    def open(self, rel: str) -> Any:
        """Open one object as a streaming response body.


Parameters
----------
rel : str
    Archive-relative path.

Returns
-------
Any
    S3 streaming body.

Raises
------
FileNotFoundError
    If the object key does not exist."""
        try:
            return self._client.get_object(Bucket=self.bucket, Key=self._key(rel))['Body']
        except self._client.exceptions.NoSuchKey as exc:
            raise FileNotFoundError(self._key(rel)) from exc

    def read(self, rel: str) -> bytes:
        """Read one object into memory.


Parameters
----------
rel : str
    Archive-relative path.

Returns
-------
bytes
    Raw object contents."""
        return self.open(rel).read()

    def text(self, rel: str) -> str:
        """Decode one object as UTF-8 text.


Parameters
----------
rel : str
    Archive-relative path.

Returns
-------
str
    Decoded object contents."""
        return self.read(rel).decode('utf-8', errors='replace')

    def json(self, rel: str) -> Any:
        """Decode one object as JSON.


Parameters
----------
rel : str
    Archive-relative path.

Returns
-------
Any
    Parsed JSON value."""
        return json.loads(self.text(rel))

    def size(self, rel: str) -> int:
        """Read an object's content length without downloading it.


Parameters
----------
rel : str
    Archive-relative path.

Returns
-------
int
    Object size in bytes."""
        response = self._client.head_object(Bucket=self.bucket, Key=self._key(rel))
        return int(response['ContentLength'])

    def sha256(self, rel: str) -> str:
        """Hash one object without saving it locally.


Parameters
----------
rel : str
    Archive-relative path.

Returns
-------
str
    Hexadecimal SHA-256 digest."""
        digest = hashlib.sha256()
        for chunk in self.open(rel).iter_chunks(1 << 20):
            digest.update(chunk)
        return digest.hexdigest()
