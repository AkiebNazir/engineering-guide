"""Accounts for the hosted guide: email one-time-code sign-in, sessions, tiers.

Used by server.py when EG_AUTH=1 (`make serve`, deploy/Dockerfile). The local
single-user app (`make app`) does not load any of this.

Sign-in is passwordless, two ways:
  * emailed code
      1. POST /api/auth/request-otp {email}  → a 6-digit code is emailed (valid 10 min)
      2. POST /api/auth/verify-otp {email, code} → the account is created on first
         sign-in (Free tier) and an HttpOnly session cookie is set
  * Sign in with Google (google_signin.py): Google vouches for the address
Either way the email address is verified by the same step that signs in, and one
address is one account.

Security choices, each enforced here rather than in the browser:
  * codes come from `secrets`, are stored only as HMAC-SHA256(server key, email, code),
    expire after OTP_TTL, allow OTP_MAX_ATTEMPTS guesses, and are single use;
    requesting a new code invalidates the previous one
  * issuing is rate limited per address (cooldown + hourly cap, kept in the database
    so a restart does not reset it) and per client IP; verifying is limited per IP
  * the reply to a code request never says whether the address has an account
  * session tokens are 256-bit random; only their SHA-256 is stored, so a leaked
    database cannot be replayed as cookies
  * sessions expire (absolute and idle), and each tier has a device cap
    (entitlements.MAX_SESSIONS): signing in on one more device ends the oldest session
  * subscriptions carry an optional expiry; an expired one reads as Free

Standard library only (sqlite3, hmac, secrets, urllib, smtplib).
"""
from __future__ import annotations

import hashlib
import hmac
import html
import json
import os
import re
import secrets
import smtplib
import sqlite3
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import defaultdict, deque
from email.message import EmailMessage
from pathlib import Path

import entitlements

OTP_TTL = 10 * 60                 # seconds a code stays valid
OTP_LENGTH = 6
OTP_MAX_ATTEMPTS = 5              # wrong guesses before the code is burned
OTP_RESEND_COOLDOWN = 60          # seconds between codes for one address
OTP_MAX_PER_HOUR = 5              # codes per address per hour
OTP_IP_PER_HOUR = 20              # code requests per client IP per hour
VERIFY_IP_PER_10MIN = 30          # verify attempts per client IP per 10 minutes
SESSION_TTL = 7 * 24 * 3600       # absolute session lifetime
SESSION_IDLE = 3 * 24 * 3600      # signed out after this long unused
SESSION_TOUCH_EVERY = 300         # write last_seen at most this often
API_PER_MINUTE = 600              # content requests per session per minute (anti-scraping)
MAX_STATE_BYTES = 2_000_000       # per-user progress document

EMAIL_RE = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
                      r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY,
    email           TEXT NOT NULL UNIQUE,
    tier            TEXT NOT NULL DEFAULT 'free',
    tier_expires_at INTEGER,                 -- unix time; NULL = no expiry
    created_at      INTEGER NOT NULL,
    verified_at     INTEGER,                 -- first successful code
    last_login_at   INTEGER,
    disabled        INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS otp_codes (
    id         INTEGER PRIMARY KEY,
    email      TEXT NOT NULL,
    code_hash  TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    attempts   INTEGER NOT NULL DEFAULT 0,
    used       INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS otp_email ON otp_codes(email, created_at);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at INTEGER NOT NULL,
    last_seen  INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    user_agent TEXT,
    ip         TEXT
);
CREATE INDEX IF NOT EXISTS sessions_user ON sessions(user_id, created_at);
CREATE TABLE IF NOT EXISTS progress (
    user_id    INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    state      TEXT NOT NULL,
    updated_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS oauth_states (   -- a Google sign-in between leaving and coming back
    state_hash   TEXT PRIMARY KEY,
    binding_hash TEXT NOT NULL,                -- ties it to the browser that started it (cookie)
    verifier     TEXT NOT NULL,                -- PKCE code_verifier
    nonce        TEXT NOT NULL,
    next         TEXT NOT NULL DEFAULT '',
    expires_at   INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS auth_events (
    id    INTEGER PRIMARY KEY,
    ts    INTEGER NOT NULL,
    kind  TEXT NOT NULL,       -- otp_sent, otp_failed, login, login_google, google_refused, session_evicted, tier_set
    email TEXT,
    ip    TEXT,
    note  TEXT
);
"""


class AuthError(Exception):
    """A refusal the client may show: `status` is the HTTP status, `code` a stable id."""

    def __init__(self, status: int, code: str, message: str, retry_after: int | None = None):
        super().__init__(message)
        self.status, self.code, self.message, self.retry_after = status, code, message, retry_after

    def body(self) -> dict:
        b = {"error": self.code, "message": self.message}
        if self.retry_after:
            b["retryAfter"] = self.retry_after
        return b


def normalize_email(raw) -> str:
    email = (raw or "").strip().lower() if isinstance(raw, str) else ""
    if len(email) > 254 or not EMAIL_RE.match(email):
        raise AuthError(400, "invalid_email", "Enter a valid email address.")
    return email


# ----------------------------------------------------------------------------
# Rate limiting (in memory, per process)
# ----------------------------------------------------------------------------
class RateLimiter:
    """Sliding-window counter: allow(key) is False once `limit` hits fall inside `window`."""

    def __init__(self, limit: int, window: float):
        self.limit, self.window = limit, window
        self.hits: dict[str, deque] = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self.lock:
            q = self.hits[key]
            while q and now - q[0] > self.window:
                q.popleft()
            if len(q) >= self.limit:
                return False
            q.append(now)
            if len(self.hits) > 50_000:            # bound memory under a flood of keys
                for k in [k for k, v in self.hits.items() if not v][:25_000]:
                    del self.hits[k]
            return True


# ----------------------------------------------------------------------------
# Mail
# ----------------------------------------------------------------------------
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


class Mailer:
    """Sends the sign-in code. Providers, first configured wins:

      Brevo   EG_BREVO_API_KEY + EG_MAIL_FROM: Brevo's transactional HTTPS API (port 443,
              which no host blocks, unlike SMTP ports on several clouds)
      SMTP    EG_SMTP_HOST + EG_MAIL_FROM (any provider, Brevo's SMTP relay included)
      console EG_OTP_CONSOLE=1: printed to the server log (development only: anyone who
              can read the log can sign in)
    """

    def __init__(self, env=os.environ):
        self.brevo_key = env.get("EG_BREVO_API_KEY", "")
        self.host = env.get("EG_SMTP_HOST", "")
        self.port = int(env.get("EG_SMTP_PORT", "587"))
        self.user = env.get("EG_SMTP_USER", "")
        self.password = env.get("EG_SMTP_PASSWORD", "")
        self.sender = env.get("EG_MAIL_FROM") or env.get("EG_SMTP_FROM") or self.user
        self.security = env.get("EG_SMTP_SECURITY", "starttls").lower()   # starttls | ssl | none
        self.console = env.get("EG_OTP_CONSOLE", "") == "1"
        self.app_name = env.get("EG_APP_NAME", "Ultimate Engineering Guide")
        self.sender_name = env.get("EG_MAIL_FROM_NAME", self.app_name)
        self.sent: list[tuple[str, str]] = []      # tests read the last code from here

    @property
    def provider(self) -> str:
        if self.brevo_key and self.sender:
            return "brevo"
        if self.host and self.sender:
            return "smtp"
        return "console" if self.console else ""

    @property
    def configured(self) -> bool:
        return bool(self.provider)

    def describe(self) -> str:
        return {
            "brevo": f"Brevo API as {self.sender_name} <{self.sender}>",
            "smtp": f"SMTP {self.host}:{self.port} ({self.security}) as {self.sender}",
            "console": "console (EG_OTP_CONSOLE=1, development only)",
        }.get(self.provider, "NOT CONFIGURED")

    def message(self, code: str) -> tuple[str, str, str]:
        """(subject, plain text, HTML) of the code email."""
        minutes = OTP_TTL // 60
        name = html.escape(self.app_name)
        subject = f"{code} is your {self.app_name} sign-in code"
        text = (f"Your {self.app_name} sign-in code is:\n\n    {code}\n\n"
                f"It expires in {minutes} minutes and works once.\n"
                "If you did not ask for it, ignore this email; nobody can sign in without the code.\n")
        body = (f'<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:420px;margin:0 auto;'
                f'padding:24px;color:#0f141c">'
                f'<p style="margin:0 0 16px;font-size:15px">Your {name} sign-in code is:</p>'
                f'<p style="margin:0 0 16px;font:700 30px/1.2 ui-monospace,Menlo,monospace;letter-spacing:6px">{code}</p>'
                f'<p style="margin:0 0 8px;font-size:14px;color:#4c5566">It expires in {minutes} minutes and works once.</p>'
                f'<p style="margin:0;font-size:13px;color:#6c7688">If you did not ask for it, ignore this email; '
                f'nobody can sign in without the code.</p></div>')
        return subject, text, body

    def send_code(self, email: str, code: str) -> None:
        self.sent.append((email, code))
        del self.sent[:-20]
        provider = self.provider
        if provider == "console":
            print(f"  [otp] sign-in code for {email}: {code}  (valid {OTP_TTL // 60} min)", flush=True)
            return
        if not provider:
            return
        # Sent off the request thread: mail latency must not tell an observer anything,
        # and a slow provider must not hold a request open.
        target = self._deliver_brevo if provider == "brevo" else self._deliver_smtp
        threading.Thread(target=target, args=(email, *self.message(code)), daemon=True).start()

    def _deliver_brevo(self, email: str, subject: str, text: str, body: str) -> None:
        payload = {
            "sender": {"name": self.sender_name, "email": self.sender},
            "to": [{"email": email}],
            "subject": subject,
            "textContent": text,
            "htmlContent": body,
            "tags": ["sign-in-code"],
        }
        req = urllib.request.Request(BREVO_API_URL, data=json.dumps(payload).encode(), method="POST", headers={
            "api-key": self.brevo_key, "Content-Type": "application/json", "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                r.read()
        except urllib.error.HTTPError as e:
            detail = e.read()[:300].decode("utf-8", "replace")
            print(f"  [otp] Brevo refused the mail to {email}: HTTP {e.code} {detail}", file=sys.stderr, flush=True)
        except (OSError, ValueError) as e:
            print(f"  [otp] could not reach Brevo for {email}: {e}", file=sys.stderr, flush=True)

    def _deliver_smtp(self, email: str, subject: str, text: str, body: str) -> None:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{self.sender_name} <{self.sender}>"
        msg["To"] = email
        msg.set_content(text)
        msg.add_alternative(body, subtype="html")
        try:
            if self.security == "ssl":
                smtp = smtplib.SMTP_SSL(self.host, self.port, timeout=15)
            else:
                smtp = smtplib.SMTP(self.host, self.port, timeout=15)
                if self.security == "starttls":
                    smtp.starttls()
            with smtp:
                if self.user:
                    smtp.login(self.user, self.password)
                smtp.send_message(msg)
        except (OSError, smtplib.SMTPException) as e:
            print(f"  [otp] could not send mail to {email}: {e}", file=sys.stderr, flush=True)


# ----------------------------------------------------------------------------
# The store
# ----------------------------------------------------------------------------
def load_secret(data_dir: Path, env=os.environ) -> bytes:
    """EG_SECRET_KEY, or a random key kept in <data_dir>/auth_secret.key (created 0600),
    next to the accounts database so it lives on the same persistent volume."""
    if env.get("EG_SECRET_KEY"):
        key = env["EG_SECRET_KEY"].encode()
        if len(key) < 32:
            sys.exit("EG_SECRET_KEY must be at least 32 characters.")
        return key
    path = data_dir / "auth_secret.key"
    if path.exists():
        return path.read_bytes().strip()
    data_dir.mkdir(parents=True, exist_ok=True)
    key = secrets.token_hex(32).encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(key)
    return key


class AuthStore:
    def __init__(self, db_path: Path, secret: bytes, mailer: Mailer | None = None, clock=time.time):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.secret = secret
        self.mailer = mailer or Mailer()
        self.clock = clock
        self.lock = threading.Lock()
        self.db = sqlite3.connect(self.db_path, check_same_thread=False, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript(SCHEMA)
        # Columns added after the first release: databases created before them get them here.
        cols = {r["name"] for r in self.db.execute("PRAGMA table_info(users)")}
        if "google_sub" not in cols:
            self.db.execute("ALTER TABLE users ADD COLUMN google_sub TEXT")
        try:
            os.chmod(self.db_path, 0o600)
        except OSError:
            pass
        self.otp_ip = RateLimiter(OTP_IP_PER_HOUR, 3600)
        self.verify_ip = RateLimiter(VERIFY_IP_PER_10MIN, 600)
        self.api_rate = RateLimiter(API_PER_MINUTE, 60)

    def now(self) -> int:
        return int(self.clock())

    def _q(self, sql: str, args=()) -> list[sqlite3.Row]:
        with self.lock:
            return self.db.execute(sql, args).fetchall()

    def _x(self, sql: str, args=()) -> sqlite3.Cursor:
        with self.lock:
            return self.db.execute(sql, args)

    def log(self, kind: str, email: str | None = None, ip: str | None = None, note: str | None = None) -> None:
        self._x("INSERT INTO auth_events(ts, kind, email, ip, note) VALUES (?,?,?,?,?)",
                (self.now(), kind, email, ip, note))

    def _hash_code(self, email: str, code: str) -> str:
        return hmac.new(self.secret, f"otp:{email}:{code}".encode(), hashlib.sha256).hexdigest()

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    # -- users ---------------------------------------------------------------
    def user_by_email(self, email: str) -> sqlite3.Row | None:
        rows = self._q("SELECT * FROM users WHERE email = ?", (email,))
        return rows[0] if rows else None

    def effective_tier(self, user) -> str:
        tier = user["tier"] if user["tier"] in entitlements.RANK else "free"
        exp = user["tier_expires_at"]
        return "free" if exp is not None and exp <= self.now() else tier

    def set_tier(self, email: str, tier: str, expires_at: int | None = None) -> sqlite3.Row:
        """Grant a plan (admin.py; a billing webhook would call this too). Creates the
        account if the person has not signed in yet; they verify on first sign-in."""
        email = normalize_email(email)
        if tier not in entitlements.RANK:
            raise AuthError(400, "invalid_tier", f"Tier must be one of {', '.join(entitlements.TIERS)}.")
        with self.lock:
            self.db.execute("INSERT OR IGNORE INTO users(email, created_at) VALUES (?, ?)", (email, self.now()))
            self.db.execute("UPDATE users SET tier = ?, tier_expires_at = ? WHERE email = ?",
                            (tier, expires_at, email))
        self.log("tier_set", email, note=f"{tier} until {expires_at or 'no expiry'}")
        user = self.user_by_email(email)
        self._enforce_device_cap(user["id"], self.effective_tier(user))
        return user

    def set_disabled(self, email: str, disabled: bool) -> None:
        self._x("UPDATE users SET disabled = ? WHERE email = ?", (1 if disabled else 0, normalize_email(email)))
        if disabled:
            self.revoke_sessions(email)

    def delete_user(self, email: str) -> bool:
        return self._x("DELETE FROM users WHERE email = ?", (normalize_email(email),)).rowcount > 0

    def list_users(self) -> list[sqlite3.Row]:
        return self._q("SELECT u.*, (SELECT COUNT(*) FROM sessions s WHERE s.user_id = u.id) AS sessions "
                       "FROM users u ORDER BY u.created_at")

    # -- one-time codes -------------------------------------------------------
    def request_otp(self, raw_email, ip: str = "") -> dict:
        email = normalize_email(raw_email)
        if not self.otp_ip.allow(f"ip:{ip}"):
            raise AuthError(429, "rate_limited", "Too many code requests from this network. Try again later.", 900)
        now = self.now()
        recent = self._q("SELECT created_at FROM otp_codes WHERE email = ? AND created_at > ? ORDER BY created_at DESC",
                         (email, now - 3600))
        if recent and now - recent[0]["created_at"] < OTP_RESEND_COOLDOWN:
            wait = OTP_RESEND_COOLDOWN - (now - recent[0]["created_at"])
            raise AuthError(429, "cooldown", f"A code was just sent. You can ask for another in {wait} s.", wait)
        if len(recent) >= OTP_MAX_PER_HOUR:
            raise AuthError(429, "rate_limited", "Too many codes for this address. Try again in an hour.", 3600)
        user = self.user_by_email(email)
        if user is not None and user["disabled"]:
            # Same answer as success: a disabled account is not revealed, and gets no code.
            self.log("otp_refused_disabled", email, ip)
            return {"ok": True, "expiresIn": OTP_TTL, "resendIn": OTP_RESEND_COOLDOWN}
        code = f"{secrets.randbelow(10 ** OTP_LENGTH):0{OTP_LENGTH}d}"
        with self.lock:
            self.db.execute("UPDATE otp_codes SET used = 1 WHERE email = ? AND used = 0", (email,))
            self.db.execute("INSERT INTO otp_codes(email, code_hash, created_at, expires_at) VALUES (?,?,?,?)",
                            (email, self._hash_code(email, code), now, now + OTP_TTL))
            self.db.execute("DELETE FROM otp_codes WHERE created_at < ?", (now - 86400,))
        self.mailer.send_code(email, code)
        self.log("otp_sent", email, ip)
        return {"ok": True, "expiresIn": OTP_TTL, "resendIn": OTP_RESEND_COOLDOWN}

    def verify_otp(self, raw_email, raw_code, ip: str = "", user_agent: str = "") -> tuple[str, dict]:
        """Check the code; on success return (session token, account). The token goes
        in the cookie only, never in a response body."""
        email = normalize_email(raw_email)
        code = re.sub(r"\s+", "", raw_code) if isinstance(raw_code, str) else ""
        if not self.verify_ip.allow(f"ip:{ip}"):
            raise AuthError(429, "rate_limited", "Too many attempts from this network. Try again in a few minutes.", 600)
        bad = AuthError(400, "invalid_code", "That code is wrong or has expired. Ask for a new one.")
        if not re.fullmatch(rf"\d{{{OTP_LENGTH}}}", code):
            raise bad
        now = self.now()
        with self.lock:
            row = self.db.execute(
                "SELECT * FROM otp_codes WHERE email = ? AND used = 0 AND expires_at > ? ORDER BY created_at DESC LIMIT 1",
                (email, now)).fetchone()
            if row is None:
                ok = False
            else:
                ok = hmac.compare_digest(row["code_hash"], self._hash_code(email, code))
                if ok:
                    self.db.execute("UPDATE otp_codes SET used = 1 WHERE id = ?", (row["id"],))
                else:
                    attempts = row["attempts"] + 1
                    self.db.execute("UPDATE otp_codes SET attempts = ?, used = ? WHERE id = ?",
                                    (attempts, 1 if attempts >= OTP_MAX_ATTEMPTS else 0, row["id"]))
        if not ok:
            self.log("otp_failed", email, ip)
            raise bad
        with self.lock:
            self.db.execute("INSERT OR IGNORE INTO users(email, created_at) VALUES (?, ?)", (email, now))
            self.db.execute("UPDATE users SET verified_at = COALESCE(verified_at, ?), last_login_at = ? WHERE email = ?",
                            (now, now, email))
        user = self.user_by_email(email)
        if user["disabled"]:
            raise AuthError(403, "disabled", "This account is disabled.")
        token = self._create_session(user, ip, user_agent)
        self.log("login", email, ip)
        return token, self.account(user)

    # -- sign-in through an identity provider (google_signin.py) -------------
    def save_oauth_state(self, state: str, binding: str, verifier: str, nonce: str, next_hash: str, ttl: int) -> None:
        now = self.now()
        with self.lock:
            self.db.execute("DELETE FROM oauth_states WHERE expires_at <= ?", (now,))
            self.db.execute("INSERT INTO oauth_states(state_hash, binding_hash, verifier, nonce, next, expires_at) "
                            "VALUES (?,?,?,?,?,?)", (self._hash_token(state), self._hash_token(binding),
                                                     verifier, nonce, next_hash, now + ttl))

    def take_oauth_state(self, state: str, binding: str) -> sqlite3.Row | None:
        """The pending sign-in for `state`, removed so it works once; None unless it exists,
        has not expired and was started by the browser holding `binding`."""
        if not state or not binding or len(state) > 200 or len(binding) > 200:
            return None
        th = self._hash_token(state)
        with self.lock:
            row = self.db.execute("SELECT * FROM oauth_states WHERE state_hash = ?", (th,)).fetchone()
            self.db.execute("DELETE FROM oauth_states WHERE state_hash = ?", (th,))
        if row is None or row["expires_at"] <= self.now():
            return None
        return row if hmac.compare_digest(row["binding_hash"], self._hash_token(binding)) else None

    def sign_in_google(self, raw_email: str, sub: str, ip: str = "", user_agent: str = "") -> tuple[str, dict]:
        """Sign in with an email Google has verified. Creates the account on first use
        (Free) or signs into the existing one with that address, and remembers the Google
        account id: a different Google account later claiming the same address is refused."""
        email = normalize_email(raw_email)
        if not sub or len(sub) > 255:
            raise AuthError(400, "google_failed", "Google did not identify the account.")
        now = self.now()
        with self.lock:
            self.db.execute("INSERT OR IGNORE INTO users(email, created_at) VALUES (?, ?)", (email, now))
            row = self.db.execute("SELECT google_sub FROM users WHERE email = ?", (email,)).fetchone()
            linked = row["google_sub"]
            if linked is None:
                self.db.execute("UPDATE users SET google_sub = ? WHERE email = ?", (sub, email))
        if linked is not None and not hmac.compare_digest(linked, sub):
            self.log("google_refused", email, ip, "a different Google account is linked")
            raise AuthError(403, "google_mismatch",
                            "This email is linked to a different Google account. Sign in with an emailed code instead.")
        self._x("UPDATE users SET verified_at = COALESCE(verified_at, ?), last_login_at = ? WHERE email = ?",
                (now, now, email))
        user = self.user_by_email(email)
        if user["disabled"]:
            raise AuthError(403, "disabled", "This account is disabled.")
        token = self._create_session(user, ip, user_agent)
        self.log("login_google", email, ip)
        return token, self.account(user)

    # -- sessions -------------------------------------------------------------
    def _create_session(self, user, ip: str, user_agent: str) -> str:
        token = secrets.token_urlsafe(32)
        now = self.now()
        self._x("INSERT INTO sessions(token_hash, user_id, created_at, last_seen, expires_at, user_agent, ip) "
                "VALUES (?,?,?,?,?,?,?)",
                (self._hash_token(token), user["id"], now, now, now + SESSION_TTL, (user_agent or "")[:300], ip))
        self._enforce_device_cap(user["id"], self.effective_tier(user))
        return token

    def _enforce_device_cap(self, user_id: int, tier: str) -> None:
        cap = entitlements.MAX_SESSIONS.get(tier, 1)
        rows = self._q("SELECT token_hash FROM sessions WHERE user_id = ? ORDER BY created_at DESC, rowid DESC",
                       (user_id,))
        for r in rows[cap:]:
            self._x("DELETE FROM sessions WHERE token_hash = ?", (r["token_hash"],))
            self.log("session_evicted", note=f"user {user_id}: device cap {cap}")

    def session_user(self, token: str | None) -> sqlite3.Row | None:
        """The signed-in user for a cookie token, or None (expired, idle, revoked, disabled)."""
        if not token or len(token) > 200:
            return None
        th = self._hash_token(token)
        now = self.now()
        rows = self._q("SELECT s.last_seen, s.expires_at, u.* FROM sessions s JOIN users u ON u.id = s.user_id "
                       "WHERE s.token_hash = ?", (th,))
        if not rows:
            return None
        row = rows[0]
        if row["expires_at"] <= now or now - row["last_seen"] > SESSION_IDLE or row["disabled"]:
            self._x("DELETE FROM sessions WHERE token_hash = ?", (th,))
            return None
        if now - row["last_seen"] > SESSION_TOUCH_EVERY:
            self._x("UPDATE sessions SET last_seen = ? WHERE token_hash = ?", (now, th))
        return row

    def logout(self, token: str | None) -> None:
        if token:
            self._x("DELETE FROM sessions WHERE token_hash = ?", (self._hash_token(token),))

    def revoke_sessions(self, email: str) -> int:
        user = self.user_by_email(normalize_email(email))
        return self._x("DELETE FROM sessions WHERE user_id = ?", (user["id"],)).rowcount if user else 0

    def allow_api(self, user) -> bool:
        return self.api_rate.allow(f"user:{user['id']}")

    def account(self, user) -> dict:
        tier = self.effective_tier(user)
        return {"email": user["email"], "tierExpiresAt": user["tier_expires_at"] if tier != "free" else None,
                **entitlements.account_view(tier)}

    # -- per-user progress ----------------------------------------------------
    def load_progress(self, user_id: int, default: dict) -> dict:
        rows = self._q("SELECT state FROM progress WHERE user_id = ?", (user_id,))
        if not rows:
            return default
        try:
            saved = json.loads(rows[0]["state"])
        except json.JSONDecodeError:
            return default
        if isinstance(saved, dict):
            default.update(saved)
        return default

    def save_progress(self, user_id: int, state: dict) -> None:
        blob = json.dumps(state, separators=(",", ":"), sort_keys=True)
        if len(blob) > MAX_STATE_BYTES:
            raise AuthError(413, "too_large", "Progress is too large to save.")
        self._x("INSERT INTO progress(user_id, state, updated_at) VALUES (?,?,?) "
                "ON CONFLICT(user_id) DO UPDATE SET state = excluded.state, updated_at = excluded.updated_at",
                (user_id, blob, self.now()))
