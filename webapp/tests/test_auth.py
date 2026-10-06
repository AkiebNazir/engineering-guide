"""Tests for sign-in, sessions, tiers and the hosted server.

    python3 -m unittest discover -s webapp/tests -v

Standard library only. The HTTP tests start server.py's handler on a free port
in hosted mode, with codes captured from the mailer instead of sent.
"""
from __future__ import annotations

import ast
import http.client
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path

WEBAPP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WEBAPP))

import auth            # noqa: E402
import entitlements    # noqa: E402
import server          # noqa: E402


class Clock:
    def __init__(self, t: float = 1_800_000_000):
        self.t = t

    def __call__(self) -> float:
        return self.t


def new_store(clock=None) -> auth.AuthStore:
    tmp = tempfile.mkdtemp()
    return auth.AuthStore(Path(tmp) / "a.db", b"k" * 64, auth.Mailer({}), clock or Clock())


def last_code(store: auth.AuthStore) -> str:
    return store.mailer.sent[-1][1]


class OtpTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.s = new_store(self.clock)

    def sign_in(self, email="a@example.com", ip="1.1.1.1"):
        self.s.request_otp(email, ip)
        return self.s.verify_otp(email, last_code(self.s), ip)

    def test_sign_in_creates_free_verified_account(self):
        token, account = self.sign_in("New.Person@Example.COM")
        self.assertEqual(account["email"], "new.person@example.com")
        self.assertEqual(account["tier"], "free")
        user = self.s.session_user(token)
        self.assertIsNotNone(user["verified_at"])

    def test_code_is_stored_hashed_and_single_use(self):
        self.s.request_otp("a@example.com", "ip")
        code = last_code(self.s)
        rows = self.s._q("SELECT code_hash FROM otp_codes")
        self.assertNotIn(code, rows[0]["code_hash"])
        self.s.verify_otp("a@example.com", code, "ip")
        with self.assertRaises(auth.AuthError):
            self.s.verify_otp("a@example.com", code, "ip")

    def test_wrong_guesses_burn_the_code(self):
        self.s.request_otp("a@example.com", "ip")
        code = last_code(self.s)
        wrong = f"{(int(code) + 1) % 10**6:06d}"
        for _ in range(auth.OTP_MAX_ATTEMPTS):
            with self.assertRaises(auth.AuthError):
                self.s.verify_otp("a@example.com", wrong, "ip")
        with self.assertRaises(auth.AuthError):           # the right code no longer works
            self.s.verify_otp("a@example.com", code, "ip")

    def test_code_expires(self):
        self.s.request_otp("a@example.com", "ip")
        self.clock.t += auth.OTP_TTL + 1
        with self.assertRaises(auth.AuthError):
            self.s.verify_otp("a@example.com", last_code(self.s), "ip")

    def test_new_code_invalidates_old_one(self):
        self.s.request_otp("a@example.com", "ip")
        old = last_code(self.s)
        self.clock.t += auth.OTP_RESEND_COOLDOWN + 1
        self.s.request_otp("a@example.com", "ip")
        if old != last_code(self.s):
            with self.assertRaises(auth.AuthError):
                self.s.verify_otp("a@example.com", old, "ip")
        self.s.verify_otp("a@example.com", last_code(self.s), "ip")

    def test_resend_cooldown_and_hourly_cap(self):
        self.s.request_otp("a@example.com", "ip")
        with self.assertRaises(auth.AuthError) as e:
            self.s.request_otp("a@example.com", "ip")
        self.assertEqual(e.exception.code, "cooldown")
        for _ in range(auth.OTP_MAX_PER_HOUR - 1):
            self.clock.t += auth.OTP_RESEND_COOLDOWN + 1
            self.s.request_otp("a@example.com", "ip")
        self.clock.t += auth.OTP_RESEND_COOLDOWN + 1
        with self.assertRaises(auth.AuthError) as e:
            self.s.request_otp("a@example.com", "ip")
        self.assertEqual(e.exception.code, "rate_limited")

    def test_invalid_email_rejected(self):
        for bad in ("", "nope", "a@b", "a b@example.com", None, 5, "x" * 250 + "@example.com"):
            with self.assertRaises(auth.AuthError):
                self.s.request_otp(bad, "ip")

    def test_disabled_account_gets_no_code_and_same_answer(self):
        self.s.set_tier("d@example.com", "pro")
        self.s.set_disabled("d@example.com", True)
        sent = len(self.s.mailer.sent)
        self.assertTrue(self.s.request_otp("d@example.com", "ip")["ok"])
        self.assertEqual(len(self.s.mailer.sent), sent)


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.s = new_store(self.clock)

    def login(self, email, ip="ip"):
        self.clock.t += auth.OTP_RESEND_COOLDOWN + 1
        self.s.request_otp(email, ip)
        return self.s.verify_otp(email, last_code(self.s), ip)[0]

    def test_token_stored_hashed_and_logout(self):
        token = self.login("a@example.com")
        self.assertFalse(self.s._q("SELECT 1 FROM sessions WHERE token_hash = ?", (token,)))
        self.s.logout(token)
        self.assertIsNone(self.s.session_user(token))

    def test_expiry_and_idle(self):
        token = self.login("a@example.com")
        self.clock.t += auth.SESSION_IDLE + 1
        self.assertIsNone(self.s.session_user(token))
        token = self.login("a@example.com")
        for _ in range(4):                                  # active, but past the absolute limit
            self.clock.t += auth.SESSION_TTL // 4 + 1
            self.s._x("UPDATE sessions SET last_seen = ?", (int(self.clock.t),))
        self.assertIsNone(self.s.session_user(token))

    def test_device_cap_evicts_oldest(self):
        self.s.set_tier("p@example.com", "pro")             # 2 devices
        t1, t2, t3 = (self.login("p@example.com") for _ in range(3))
        self.assertIsNone(self.s.session_user(t1))
        self.assertIsNotNone(self.s.session_user(t2))
        self.assertIsNotNone(self.s.session_user(t3))

    def test_tier_expiry_falls_back_to_free(self):
        self.s.set_tier("p@example.com", "pro_max", int(self.clock.t) + 3600)
        token = self.login("p@example.com")
        self.assertEqual(self.s.effective_tier(self.s.session_user(token)), "pro_max")
        self.clock.t += 3600
        self.s._x("UPDATE sessions SET last_seen = ?", (int(self.clock.t),))
        self.assertEqual(self.s.effective_tier(self.s.session_user(token)), "free")

    def test_disable_ends_sessions(self):
        token = self.login("a@example.com")
        self.s.set_disabled("a@example.com", True)
        self.assertIsNone(self.s.session_user(token))

    def test_progress_round_trip(self):
        token = self.login("a@example.com")
        uid = self.s.session_user(token)["id"]
        self.s.save_progress(uid, {"problems": {"x": {"status": "solved"}}})
        self.assertEqual(self.s.load_progress(uid, {"docs": {}})["problems"]["x"]["status"], "solved")


class EntitlementTests(unittest.TestCase):
    def test_every_api_route_is_classified(self):
        """Default deny: a GET route missing from ROUTES is refused for everyone."""
        src = (WEBAPP / "server.py").read_text()
        fn = next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.FunctionDef) and n.name == "api_get")
        routes = {c.comparators[0].value for c in ast.walk(fn)
                  if isinstance(c, ast.Compare) and isinstance(c.left, ast.Name) and c.left.id == "p"
                  and isinstance(c.comparators[0], ast.Constant)}
        self.assertTrue(routes)
        self.assertEqual(sorted(routes - set(entitlements.ROUTES)), [])

    def test_tier_ladder(self):
        check = entitlements.check
        q = lambda **kw: {k: [v] for k, v in kw.items()}
        dsa_free = q(topic="01_arrays_hashing", seq="001", kind="solution", lang="py")
        dsa_base = q(topic="16_dp_1d", seq="001", kind="solution", lang="py")
        self.assertIsNone(check("/api/problem", dsa_free, "free"))
        self.assertEqual(check("/api/problem", dsa_base, "free")["requires"], "base")
        self.assertIsNone(check("/api/problem", dsa_base, "base"))
        self.assertEqual(check("/api/sd-doc", q(id="problem/002_rate_limiter"), "base")["requires"], "pro")
        self.assertIsNone(check("/api/sd-doc", q(id="problem/002_rate_limiter"), "pro"))
        self.assertEqual(check("/api/sd-doc", q(id="problem/035_x"), "pro")["requires"], "pro_max")
        self.assertIsNone(check("/api/sd-doc", q(id="readme"), "free"))
        self.assertEqual(check("/api/roadmap-doc", q(id="9_day_x"), "pro")["requires"], "pro_max")
        self.assertEqual(check("/api/query-lab", q(engine="sql"), "base")["requires"], "pro")
        self.assertEqual(check("/api/track-doc", q(m="nope", id="x"), "pro_max")["error"], "forbidden")
        self.assertEqual(check("/api/not-a-route", {}, "pro_max")["error"], "forbidden")

    def test_every_module_has_a_free_sample(self):
        for module in entitlements.MODULE_TIER:
            if module == "qlab":
                continue
            ids = entitlements.FREE_IDS.get(module, set()) | ({"01_arrays_hashing"} if module == "dsa" else set())
            self.assertTrue(ids, module)

    def test_free_ids_exist(self):
        """A renamed file must not silently drop a free sample."""
        lists = {"csfund": "/api/cs-fundamentals", "behavioral": "/api/google-behavioral", "sd": "/api/sd",
                 "swd": "/api/software-design", "api": "/api/apis", "sql": "/api/sql", "nosql": "/api/nosql",
                 "roadmap": "/api/roadmap", "library": "/api/library-guides", "agentic": "/api/agentic-ai"}
        for module, path in lists.items():
            ids = {it["id"] for it in server.api_get(path, {})[0]["items"]}
            self.assertLessEqual(entitlements.FREE_IDS[module], ids, module)
        for m in ("toolkit", "testing", "cicd", "dataeng", "mlops", "maths"):
            ids = {it["id"] for it in server.api_get("/api/track", {"m": [m]})[0]["items"]}
            self.assertLessEqual(entitlements.FREE_IDS[m], ids, m)

    def test_lists_tagged_and_dsa_map_filtered(self):
        items = entitlements.filter_payload("/api/sd", {}, server.api_get("/api/sd", {})[0], "free")["items"]
        self.assertTrue(all("locked" in it and "requires" in it for it in items))
        self.assertFalse(next(it for it in items if it["id"] == "readme")["locked"])
        m = entitlements.filter_payload("/api/dsa-map", {}, server.api_get("/api/dsa-map", {})[0], "free")
        self.assertTrue(m["problems"])
        self.assertTrue(all(pid.split("/")[0] in entitlements.FREE_DSA_TOPICS for pid in m["problems"]))


class HostedServerTests(unittest.TestCase):
    """The real handler in hosted mode, over HTTP."""

    @classmethod
    def setUpClass(cls):
        cls.saved = {k: getattr(server, k) for k in ("AUTH_ENABLED", "AUTH", "COOKIE_SECURE", "SESSION_COOKIE")}
        server.AUTH_ENABLED, server.COOKIE_SECURE, server.SESSION_COOKIE = True, False, "eg_session"
        server.AUTH = cls.store = new_store(Clock(__import__("time").time()))
        cls.httpd = server.StudioServer(("127.0.0.1", 0), server.Handler)
        cls.port = cls.httpd.server_address[1]
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        for k, v in cls.saved.items():
            setattr(server, k, v)

    def req(self, method, path, body=None, cookie=None, origin=True):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        headers = {}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if origin:
            headers["Origin"] = f"http://127.0.0.1:{self.port}"
        if cookie:
            headers["Cookie"] = cookie
        c.request(method, path, json.dumps(body) if body is not None else None, headers)
        r = c.getresponse()
        data = r.read()
        c.close()
        try:
            data = json.loads(data)
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
        return r.status, dict(r.getheaders()), data

    def login(self, email):
        self.req("POST", "/api/auth/request-otp", {"email": email})
        st, h, _ = self.req("POST", "/api/auth/verify-otp", {"email": email, "code": last_code(self.store)})
        self.assertEqual(st, 200)
        cookie = h["Set-Cookie"]
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Strict", cookie)
        return cookie.split(";")[0]

    def test_signed_out(self):
        st, h, _ = self.req("GET", "/")
        self.assertEqual((st, h["Location"]), (302, "login.html"))
        self.assertEqual(self.req("GET", "/app.js")[0], 401)
        self.assertEqual(self.req("GET", "/api/bootstrap")[0], 401)
        self.assertEqual(self.req("GET", "/login.html")[0], 200)
        self.assertIn("Content-Security-Policy", self.req("GET", "/login.html")[1])

    def test_public_prefix_cannot_be_escaped(self):
        for path in ("/vendor/fonts/../app.js", "/vendor/fonts/%2e%2e/app.js", "/login.html/../app.js"):
            c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
            c.putrequest("GET", path, skip_accept_encoding=True)
            c.endheaders()
            r = c.getresponse()
            r.read()
            c.close()
            self.assertIn(r.status, (401, 404), path)

    def test_cross_site_post_refused(self):
        st, _, _ = self.req("POST", "/api/auth/request-otp", {"email": "x@example.com"}, origin=False)
        self.assertEqual(st, 403)

    def test_free_reader(self):
        cookie = self.login("free-reader@example.com")
        st, _, boot = self.req("GET", "/api/bootstrap", cookie=cookie)
        self.assertEqual(st, 200)
        self.assertEqual(boot["account"]["tier"], "free")
        self.assertEqual(boot["root"], "")
        st, _, body = self.req("GET", "/api/sd-doc?id=problem/002_rate_limiter", cookie=cookie)
        self.assertEqual((st, body["error"], body["requires"]), (403, "upgrade_required", "pro"))
        self.assertEqual(self.req("GET", "/api/sd-doc?id=problem/001_url_shortener", cookie=cookie)[0], 200)
        st, _, run = self.req("POST", "/api/run", {"code": "print(1)", "lang": "py"}, cookie=cookie)
        self.assertFalse(run["ok"])
        self.assertIn("switched off", run["stderr"])

    def test_upgrade_takes_effect_and_progress_is_per_user(self):
        cookie = self.login("payer@example.com")
        path = "/api/roadmap-doc?id=5_day_norms_distances"
        self.assertEqual(self.req("GET", path, cookie=cookie)[0], 403)
        self.store.set_tier("payer@example.com", "pro_max")
        self.assertEqual(self.req("GET", path, cookie=cookie)[0], 200)
        self.req("POST", "/api/patch", {"id": "p1", "patch": {"status": "solved"}}, cookie=cookie)
        other = self.login("other@example.com")
        self.assertNotIn("p1", self.req("GET", "/api/state", cookie=other)[2]["problems"])
        self.assertIn("p1", self.req("GET", "/api/state", cookie=cookie)[2]["problems"])

    def test_logout(self):
        cookie = self.login("bye@example.com")
        self.req("POST", "/api/auth/logout", {}, cookie=cookie)
        self.assertEqual(self.req("GET", "/api/bootstrap", cookie=cookie)[0], 401)


if __name__ == "__main__":
    unittest.main()
