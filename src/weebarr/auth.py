"""Authentication helpers for local and Plex-backed login flows."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import asdict, dataclass
from typing import Any, cast
from urllib.parse import urlencode

import httpx

from src.weebarr.settings import Settings

PLEX_PIN_CREATE_URL = "https://plex.tv/api/v2/pins"
PLEX_PIN_CHECK_URL = "https://plex.tv/api/v2/pins/{pin_id}"
PLEX_USER_URL = "https://plex.tv/api/v2/user"
DEFAULT_REDIRECT_PATH = "/seasonal"
PBKDF2_ITERATIONS = 390000
API_KEY_PREFIX = "weebarr_"


@dataclass(frozen=True)
class AuthUser:
    """Authenticated user info stored in the signed session."""

    mode: str
    username: str
    display_name: str
    avatar_url: str | None = None
    email: str | None = None

    @classmethod
    def from_session(cls, value: dict[str, Any] | None) -> "AuthUser | None":
        if not isinstance(value, dict):
            return None
        mode = str(value.get("mode") or "").strip().lower()
        username = str(value.get("username") or "").strip()
        display_name = str(value.get("display_name") or "").strip()
        if not mode or not username or not display_name:
            return None
        return cls(
            mode=mode,
            username=username,
            display_name=display_name,
            avatar_url=(
                str(value.get("avatar_url")).strip()
                if value.get("avatar_url")
                else None
            ),
            email=str(value.get("email")).strip() if value.get("email") else None,
        )


def build_session_user_payload(user: AuthUser) -> dict[str, Any]:
    """Serialize an auth user for the session cookie."""

    return asdict(user)


def verify_local_credentials(
    settings: Settings,
    *,
    username: str,
    password: str,
) -> bool:
    """Check local credentials using constant-time comparison."""

    expected_username = settings.auth_username.strip().casefold()
    provided_username = username.strip().casefold()
    password_valid = False
    if settings.auth_password_hash:
        password_valid = verify_secret(password, settings.auth_password_hash)
    elif settings.auth_password:
        password_valid = hmac.compare_digest(password, settings.auth_password)
    return bool(
        expected_username
        and password_valid
        and hmac.compare_digest(provided_username, expected_username)
    )


def hash_secret(secret: str) -> str:
    """Hash a secret value for config persistence."""

    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        secret.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    encoded_salt = base64.urlsafe_b64encode(salt).decode("ascii").rstrip("=")
    encoded_digest = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${encoded_salt}${encoded_digest}"


def verify_secret(secret: str, stored_hash: str) -> bool:
    """Verify a secret against the stored PBKDF2 hash."""

    try:
        algorithm, iterations, encoded_salt, encoded_digest = stored_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    try:
        salt = base64.urlsafe_b64decode(encoded_salt + "=" * (-len(encoded_salt) % 4))
        expected = base64.urlsafe_b64decode(
            encoded_digest + "=" * (-len(encoded_digest) % 4)
        )
    except (ValueError, TypeError):
        return False

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        secret.encode("utf-8"),
        salt,
        int(iterations),
    )
    return hmac.compare_digest(digest, expected)


def generate_api_key() -> str:
    """Generate a bearer-style API key for automation."""

    return API_KEY_PREFIX + secrets.token_urlsafe(30)


def generate_session_secret() -> str:
    """Generate a session signing secret for SessionMiddleware."""

    return secrets.token_urlsafe(48)


def verify_api_key(settings: Settings, candidate: str) -> bool:
    """Validate an API key from env or persisted hashed config."""

    token = candidate.strip()
    if not token:
        return False
    if settings.app_api_key_hash:
        return verify_secret(token, settings.app_api_key_hash)
    if settings.app_api_key:
        return hmac.compare_digest(token, settings.app_api_key)
    return False


def verify_bootstrap_token(settings: Settings, candidate: str) -> bool:
    """Validate the optional first-run bootstrap token."""

    token = candidate.strip()
    if not token:
        return False
    if settings.bootstrap_token_hash:
        return verify_secret(token, settings.bootstrap_token_hash)
    if settings.bootstrap_token:
        return hmac.compare_digest(token, settings.bootstrap_token)
    return False


def masked_preview(secret: str) -> str:
    """Create a small preview string safe to display in the UI."""

    if not secret:
        return ""
    tail = secret[-4:] if len(secret) > 4 else secret
    return f"••••{tail}"


def plex_headers(
    settings: Settings,
    *,
    token: str | None = None,
) -> dict[str, str]:
    """Return common Plex client headers."""

    headers = {
        "Accept": "application/json",
        "X-Plex-Client-Identifier": settings.plex_client_id,
        "X-Plex-Product": settings.plex_product_name,
        "X-Plex-Version": settings.plex_product_version,
        "X-Plex-Platform": settings.plex_platform,
    }
    if token:
        headers["X-Plex-Token"] = token
    return headers


def build_plex_auth_url(
    settings: Settings,
    *,
    code: str,
    forward_url: str,
) -> str:
    """Construct the Plex hosted auth URL for browser sign-in."""

    return "https://app.plex.tv/auth#?" + urlencode(
        {
            "clientID": settings.plex_client_id,
            "code": code,
            "forwardUrl": forward_url,
            "context[device][product]": settings.plex_product_name,
        }
    )


async def create_plex_pin(settings: Settings) -> dict[str, Any]:
    """Create a one-time Plex PIN for the auth redirect flow."""

    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        response = await client.post(
            PLEX_PIN_CREATE_URL,
            params={"strong": "true"},
            headers=plex_headers(settings),
        )
        response.raise_for_status()
        return cast(dict[str, Any], response.json())


async def fetch_plex_pin(
    settings: Settings,
    *,
    pin_id: int,
    code: str,
) -> dict[str, Any]:
    """Fetch the current state of a previously created Plex PIN."""

    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        response = await client.get(
            PLEX_PIN_CHECK_URL.format(pin_id=pin_id),
            params={"code": code},
            headers=plex_headers(settings),
        )
        response.raise_for_status()
        return cast(dict[str, Any], response.json())


async def fetch_plex_user(settings: Settings, *, token: str) -> dict[str, Any]:
    """Fetch the logged-in Plex account after PIN completion."""

    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        response = await client.get(
            PLEX_USER_URL,
            headers=plex_headers(settings, token=token),
        )
        response.raise_for_status()
        return cast(dict[str, Any], response.json())


def plex_user_allowed(settings: Settings, user: dict[str, Any]) -> bool:
    """Check whether a Plex account is permitted to access Weebarr."""

    allowed = {entry.casefold() for entry in (settings.plex_allowed_users or [])}
    if not allowed:
        return True

    candidates = {
        str(user.get("username") or "").casefold(),
        str(user.get("email") or "").casefold(),
        str(user.get("title") or "").casefold(),
        str(user.get("friendlyName") or "").casefold(),
    }
    candidates.discard("")
    return bool(candidates & allowed)


def plex_auth_user(user: dict[str, Any]) -> AuthUser:
    """Normalize Plex account payload into the shared auth user model."""

    display_name = (
        str(user.get("friendlyName") or "").strip()
        or str(user.get("title") or "").strip()
        or str(user.get("username") or "").strip()
    )
    username = (
        str(user.get("username") or "").strip()
        or str(user.get("email") or "").strip()
        or display_name
    )
    return AuthUser(
        mode="plex",
        username=username,
        display_name=display_name or username,
        avatar_url=str(user.get("thumb")).strip() if user.get("thumb") else None,
        email=str(user.get("email")).strip() if user.get("email") else None,
    )
