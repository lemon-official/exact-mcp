"""Runtime logging configuration and credential-safe value rendering."""

import logging
import json
import re
import shlex
import sys
from collections.abc import Collection, Mapping
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from pydantic import BaseModel, SecretStr

from exact_mcp.config import Settings

REDACTED = "<redacted>"

_SENSITIVE_KEYS = {
    "authorization",
    "clientsecret",
    "accesstoken",
    "refreshtoken",
    "tokenencryptionkey",
    "code",
    "state",
    "password",
}
_BEARER_PATTERN = re.compile(r"(?i)\bbearer\s+[^\s,;]+")
_KEY_VALUE_PATTERN = re.compile(
    r"(?i)([?&;\s](?:code|state|client_secret|access_token|refresh_token)=)[^&;\s]+"
)


def curl_command(
    method: str,
    url: str,
    headers: Mapping[str, str],
    *,
    json_body: Mapping[str, Any] | None = None,
    form_body: Mapping[str, str] | None = None,
) -> str:
    """Render a full shell-safe cURL command for an outbound request."""
    if json_body is not None and form_body is not None:
        raise ValueError("a cURL request cannot have both JSON and form bodies")

    rendered_headers = dict(headers)
    if json_body is not None:
        rendered_headers.setdefault("Content-Type", "application/json")
    if form_body is not None:
        rendered_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")

    arguments = ["curl", "-X", method.upper(), url]
    for name, value in rendered_headers.items():
        arguments.extend(["-H", f"{name}: {value}"])
    if json_body is not None:
        arguments.extend(
            ["--data-raw", json.dumps(json_body, separators=(",", ":"), ensure_ascii=False)]
        )
    if form_body is not None:
        arguments.extend(["--data-raw", urlencode(form_body)])
    return " ".join(shlex.quote(argument) for argument in arguments)


def redact(value: Any, *, sensitive_values: Collection[str] = ()) -> Any:
    """Recursively mask OAuth credentials while preserving useful structure."""
    if isinstance(value, SecretStr):
        return REDACTED
    if isinstance(value, BaseModel):
        return redact(value.model_dump(mode="json"), sensitive_values=sensitive_values)
    if isinstance(value, Mapping):
        return {
            key: REDACTED
            if _sensitive_key(str(key))
            else redact(item, sensitive_values=sensitive_values)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return tuple(redact(item, sensitive_values=sensitive_values) for item in value)
    if isinstance(value, list):
        return [redact(item, sensitive_values=sensitive_values) for item in value]
    if isinstance(value, set):
        return {redact(item, sensitive_values=sensitive_values) for item in value}
    if isinstance(value, str):
        sanitized = _BEARER_PATTERN.sub(f"Bearer {REDACTED}", value)
        sanitized = _KEY_VALUE_PATTERN.sub(lambda match: f"{match.group(1)}{REDACTED}", sanitized)
        for secret in sensitive_values:
            if secret:
                sanitized = sanitized.replace(secret, REDACTED)
        return sanitized
    return value


def configure_logging(settings: Settings) -> None:
    """Configure process-wide stderr logging and an optional rotating file."""
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(formatter)
    handlers: list[logging.Handler] = [stderr_handler]
    file_error: OSError | None = None

    if settings.log_file is not None:
        try:
            log_file = Path(settings.log_file).expanduser()
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=settings.log_max_bytes,
                backupCount=settings.log_backup_count,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)
        except OSError as exc:
            file_error = exc

    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        handlers=handlers,
        force=True,
    )
    if file_error is not None:
        logging.getLogger(__name__).warning(
            "log_file_unavailable path=%s error=%s",
            settings.log_file,
            file_error,
        )


def _sensitive_key(key: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]", "", key.lower())
    return normalized in _SENSITIVE_KEYS or "password" in normalized or "secret" in normalized
