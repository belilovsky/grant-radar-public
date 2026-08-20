"""Content-addressed assets for the server-rendered public shell.

The product deliberately keeps its templates as Python SSR modules.  This
adapter externalises only large executable inline blocks after rendering, so
the public markup stays backwards-compatible while CSS and JavaScript become
immutable browser-cacheable resources.
"""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
from pathlib import Path

from fastapi import Request
from starlette.responses import Response

GENERATED_ASSET_DIR = Path(
    os.environ.get("QAZ_FUND_GENERATED_ASSET_DIR", "/tmp/qazfund-generated-assets")
)
_MIN_EXTERNAL_ASSET_BYTES = 8_192
_ASSET_NAME = re.compile(r"^[0-9a-f]{64}\.(?:css|js)$")
_STYLE_BLOCK = re.compile(
    r"<style(?P<attrs>[^>]*)>(?P<body>.*?)</style>",
    flags=re.IGNORECASE | re.DOTALL,
)
_SCRIPT_BLOCK = re.compile(
    r"<script(?P<attrs>[^>]*)>(?P<body>.*?)</script>",
    flags=re.IGNORECASE | re.DOTALL,
)


def generated_asset_path(asset_name: str) -> Path | None:
    """Resolve a validated generated asset without permitting path traversal."""

    if _ASSET_NAME.fullmatch(asset_name) is None:
        return None
    path = GENERATED_ASSET_DIR / asset_name
    return path if path.is_file() else None


def _store_asset(body: str, extension: str) -> str:
    encoded = body.encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    asset_name = f"{digest}.{extension}"
    destination = GENERATED_ASSET_DIR / asset_name
    if destination.is_file():
        return asset_name

    GENERATED_ASSET_DIR.mkdir(mode=0o755, parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{digest}.", suffix=".partial", dir=GENERATED_ASSET_DIR
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_name, 0o644)
        os.replace(temporary_name, destination)
    finally:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
    return asset_name


def externalize_large_inline_assets(html: str, *, root_path: str = "") -> str:
    """Replace large inline CSS/JS with immutable, content-hashed URLs."""

    asset_root = f"{root_path.rstrip('/')}/assets/generated"

    def replace_style(match: re.Match[str]) -> str:
        body = match.group("body")
        if len(body.encode("utf-8")) < _MIN_EXTERNAL_ASSET_BYTES:
            return match.group(0)
        asset_name = _store_asset(body, "css")
        attrs = match.group("attrs")
        media_match = re.search(r"\bmedia=(['\"])(.*?)\1", attrs, re.IGNORECASE)
        media = f' media="{media_match.group(2)}"' if media_match is not None else ""
        return f'<link rel="stylesheet" href="{asset_root}/{asset_name}"{media}>'

    def replace_script(match: re.Match[str]) -> str:
        attrs = match.group("attrs")
        body = match.group("body")
        lowered_attrs = attrs.lower()
        if " src=" in f" {lowered_attrs}" or len(body.encode("utf-8")) < (
            _MIN_EXTERNAL_ASSET_BYTES
        ):
            return match.group(0)
        type_match = re.search(r"\btype=(['\"])(.*?)\1", attrs, re.IGNORECASE)
        script_type = type_match.group(2).strip().lower() if type_match else ""
        if script_type and script_type not in {
            "application/javascript",
            "text/javascript",
            "module",
        }:
            return match.group(0)
        asset_name = _store_asset(body, "js")
        safe_attrs = attrs.strip()
        suffix = f" {safe_attrs}" if safe_attrs else ""
        return f'<script src="{asset_root}/{asset_name}"{suffix}></script>'

    html = _STYLE_BLOCK.sub(replace_style, html)
    return _SCRIPT_BLOCK.sub(replace_script, html)


async def externalize_html_response(request: Request, response: Response) -> Response:
    """Externalise cacheable assets in an HTML response produced by FastAPI."""

    content_type = response.headers.get("content-type", "").lower()
    if (
        request.method == "HEAD"
        or request.url.path != "/"
        or "text/html" not in content_type
        or not hasattr(response, "body_iterator")
    ):
        return response

    chunks = [chunk async for chunk in response.body_iterator]  # type: ignore[attr-defined]
    body = b"".join(
        chunk.encode("utf-8") if isinstance(chunk, str) else bytes(chunk)
        for chunk in chunks
    )
    try:
        html = body.decode("utf-8")
    except UnicodeDecodeError:
        return Response(
            body,
            status_code=response.status_code,
            headers=dict(response.headers),
            background=response.background,
        )
    transformed = externalize_large_inline_assets(
        html, root_path=str(request.scope.get("root_path") or "")
    )
    headers = {
        key: value
        for key, value in response.headers.items()
        if key.lower() not in {"content-length", "content-encoding"}
    }
    return Response(
        transformed.encode("utf-8"),
        status_code=response.status_code,
        headers=headers,
        background=response.background,
    )
