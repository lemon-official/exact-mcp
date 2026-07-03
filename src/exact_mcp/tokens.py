"""OAuth token models and encrypted persistence."""

import os
import tempfile
from pathlib import Path
from typing import Protocol

import anyio
from cryptography.fernet import Fernet, InvalidToken
from pydantic import BaseModel, ConfigDict, Field


class OAuthTokens(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    access_token: str = Field(min_length=1)
    refresh_token: str = Field(min_length=1)
    expires_at: float
    obtained_at: float
    refresh_token_obtained_at: float | None = None
    token_type: str = "Bearer"


class TokenStore(Protocol):
    async def load(self) -> OAuthTokens | None: ...

    async def save(self, tokens: OAuthTokens) -> None: ...

    async def clear(self) -> None: ...


class MemoryTokenStore:
    def __init__(self, tokens: OAuthTokens | None = None) -> None:
        self._tokens = tokens

    async def load(self) -> OAuthTokens | None:
        return self._tokens

    async def save(self, tokens: OAuthTokens) -> None:
        self._tokens = tokens

    async def clear(self) -> None:
        self._tokens = None


class EncryptedFileTokenStore:
    """Atomically persist tokens encrypted with a deployment-owned Fernet key."""

    def __init__(self, path: Path, key: bytes) -> None:
        self._path = path
        self._fernet = Fernet(key)

    async def load(self) -> OAuthTokens | None:
        return await anyio.to_thread.run_sync(self._load_sync)

    def _load_sync(self) -> OAuthTokens | None:
        if not self._path.exists():
            return None
        try:
            plaintext = self._fernet.decrypt(self._path.read_bytes())
        except InvalidToken as exc:
            raise ValueError("unable to decrypt OAuth token file") from exc
        return OAuthTokens.model_validate_json(plaintext)

    async def save(self, tokens: OAuthTokens) -> None:
        await anyio.to_thread.run_sync(self._save_sync, tokens)

    def _save_sync(self, tokens: OAuthTokens) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        ciphertext = self._fernet.encrypt(tokens.model_dump_json().encode())
        descriptor, temporary_name = tempfile.mkstemp(
            dir=self._path.parent,
            prefix=f".{self._path.name}.",
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(ciphertext)
                handle.flush()
                os.fsync(handle.fileno())
            temporary.chmod(0o600)
            os.replace(temporary, self._path)
        finally:
            temporary.unlink(missing_ok=True)

    async def clear(self) -> None:
        await anyio.to_thread.run_sync(self._path.unlink, True)
