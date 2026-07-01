from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from exact_mcp.tokens import EncryptedFileTokenStore, MemoryTokenStore, OAuthTokens


@pytest.mark.asyncio
async def test_memory_store_round_trips_tokens() -> None:
    tokens = OAuthTokens(
        access_token="access-secret",
        refresh_token="refresh-secret",
        expires_at=1000,
        obtained_at=400,
    )
    store = MemoryTokenStore()

    await store.save(tokens)

    assert await store.load() == tokens
    await store.clear()
    assert await store.load() is None


@pytest.mark.asyncio
async def test_encrypted_file_store_never_writes_plaintext(tmp_path: Path) -> None:
    path = tmp_path / "tokens.enc"
    store = EncryptedFileTokenStore(path, Fernet.generate_key())
    tokens = OAuthTokens(
        access_token="access-secret",
        refresh_token="refresh-secret",
        expires_at=1000,
        obtained_at=400,
    )

    await store.save(tokens)

    contents = path.read_bytes()
    assert b"access-secret" not in contents
    assert b"refresh-secret" not in contents
    assert await store.load() == tokens
    assert path.stat().st_mode & 0o077 == 0


@pytest.mark.asyncio
async def test_encrypted_file_store_rejects_wrong_key(tmp_path: Path) -> None:
    path = tmp_path / "tokens.enc"
    await EncryptedFileTokenStore(path, Fernet.generate_key()).save(
        OAuthTokens(
            access_token="access",
            refresh_token="refresh",
            expires_at=1000,
            obtained_at=400,
        )
    )

    with pytest.raises(ValueError, match="decrypt"):
        await EncryptedFileTokenStore(path, Fernet.generate_key()).load()
