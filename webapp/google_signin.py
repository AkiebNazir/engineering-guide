"""Sign in with Google for the hosted guide (OpenID Connect, authorization-code flow).

    GET /api/auth/google/start?next=#/…   → 302 to Google's consent screen
    GET /api/auth/google/callback?code&state → session cookie, then into the app

Enabled when EG_GOOGLE_CLIENT_ID and EG_GOOGLE_CLIENT_SECRET are set. Only the
`openid email` scopes are asked for: the guide needs a verified address, nothing else.

How each step is protected:
  * `state`  random, single use, 10-minute lifetime, stored hashed, and bound to the
             browser that started the sign-in by a separate random cookie, so a sign-in
             link cannot be completed in someone else's browser (login CSRF)
  * PKCE     the code is useless without the S256 verifier that never left the server
  * nonce    must come back inside the ID token, so a token cannot be replayed into
             another sign-in
  * ID token received straight from Google's token endpoint over HTTPS (certificate
             checked) and authenticated with the client secret. OpenID Connect Core
             §3.1.3.7 allows TLS server validation in place of the signature check for a
             token obtained this way; every claim is still checked: issuer, audience,
             authorized party, expiry, issue time, nonce, and email_verified
  * the account is keyed by the verified email; the Google account id (`sub`) is
             remembered and a different Google account claiming that address is refused

Standard library only (urllib, hashlib, secrets).
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
ISSUERS = frozenset({"accounts.google.com", "https://accounts.google.com"})
STATE_TTL = 600            # seconds between leaving for Google and coming back
CLOCK_SKEW = 300           # seconds of clock difference tolerated on exp / iat
NEXT_RE = re.compile(r"^#/[\w\-/%.?=&]*$")   # only in-app hash routes, never another site


class GoogleError(Exception):
    """Sign-in did not complete; `reason` goes to the log, never to the browser."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(part: str) -> bytes:
    return base64.urlsafe_b64decode(part + "=" * (-len(part) % 4))


def safe_next(raw: str | None) -> str:
    return raw if raw and len(raw) <= 300 and NEXT_RE.match(raw) else ""


class GoogleSignIn:
    def __init__(self, store, env=os.environ, clock=time.time):
        self.store = store
        self.client_id = env.get("EG_GOOGLE_CLIENT_ID", "").strip()
        self.client_secret = env.get("EG_GOOGLE_CLIENT_SECRET", "").strip()
        self.clock = clock

    @property
    def enabled(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def start(self, redirect_uri: str, next_hash: str) -> tuple[str, str]:
        """(URL of Google's consent screen, binding token for the browser's cookie)."""
        state, binding = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        verifier, nonce = secrets.token_urlsafe(64), secrets.token_urlsafe(24)
        self.store.save_oauth_state(state, binding, verifier, nonce, safe_next(next_hash), STATE_TTL)
        query = urllib.parse.urlencode({
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email",
            "state": state,
            "nonce": nonce,
            "code_challenge": _b64url(hashlib.sha256(verifier.encode()).digest()),
            "code_challenge_method": "S256",
            "prompt": "select_account",
        })
        return f"{AUTH_URL}?{query}", binding

    def finish(self, state: str, code: str, binding: str, redirect_uri: str) -> tuple[str, str, str]:
        """Check the callback and return (verified email, Google account id, next hash)."""
        pending = self.store.take_oauth_state(state, binding)
        if pending is None:
            raise GoogleError("unknown, expired, reused or foreign state")
        if not code or len(code) > 2048:
            raise GoogleError("no authorization code")
        tokens = self._exchange(code, pending["verifier"], redirect_uri)
        claims = self._claims(tokens.get("id_token"))
        now = self.clock()
        aud = claims.get("aud")
        audiences = aud if isinstance(aud, list) else [aud]
        if claims.get("iss") not in ISSUERS:
            raise GoogleError(f"issuer {claims.get('iss')!r}")
        if self.client_id not in audiences:
            raise GoogleError("audience is not this app")
        if len(audiences) > 1 and claims.get("azp") != self.client_id:
            raise GoogleError("authorized party is not this app")
        if not isinstance(claims.get("exp"), (int, float)) or claims["exp"] + CLOCK_SKEW < now:
            raise GoogleError("token expired")
        if isinstance(claims.get("iat"), (int, float)) and claims["iat"] - CLOCK_SKEW > now:
            raise GoogleError("token issued in the future")
        if not secrets.compare_digest(str(claims.get("nonce", "")), pending["nonce"]):
            raise GoogleError("nonce mismatch")
        if claims.get("email_verified") not in (True, "true"):
            raise GoogleError("email not verified by Google")
        email, sub = claims.get("email"), claims.get("sub")
        if not isinstance(email, str) or not isinstance(sub, str) or not email or not sub:
            raise GoogleError("token has no email or subject")
        return email, sub, pending["next"]

    def _exchange(self, code: str, verifier: str, redirect_uri: str) -> dict:
        """Trade the code for tokens at Google's token endpoint (back channel)."""
        body = urllib.parse.urlencode({
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "code_verifier": verifier,
        }).encode()
        req = urllib.request.Request(TOKEN_URL, data=body, method="POST", headers={
            "Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            raise GoogleError(f"token endpoint HTTP {e.code}: {e.read()[:200].decode('utf-8', 'replace')}") from None
        except (OSError, ValueError) as e:
            raise GoogleError(f"token endpoint unreachable: {e}") from None

    @staticmethod
    def _claims(id_token) -> dict:
        if not isinstance(id_token, str) or id_token.count(".") != 2:
            raise GoogleError("no ID token")
        try:
            claims = json.loads(_b64url_decode(id_token.split(".")[1]))
        except (ValueError, UnicodeDecodeError):
            raise GoogleError("unreadable ID token") from None
        if not isinstance(claims, dict):
            raise GoogleError("unreadable ID token")
        return claims
