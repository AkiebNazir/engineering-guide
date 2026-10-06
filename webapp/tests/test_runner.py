"""Tests for running code: job staging, the hosted run routes, and the sandbox daemon.

    python3 -m unittest discover -s webapp/tests -v

The hosted tests talk to a stand-in runner on a Unix socket. The daemon tests start
real sandboxed processes and need root on Linux (they are skipped otherwise, e.g. CI).
"""
from __future__ import annotations

import http.client
import json
import os
import socketserver
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

WEBAPP = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WEBAPP))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import auth            # noqa: E402
import entitlements    # noqa: E402
import sandbox         # noqa: E402
import server          # noqa: E402
from test_auth import Clock, last_code, new_store   # noqa: E402


class StagingTests(unittest.TestCase):
    def test_validate_refuses_escapes(self):
        ok = {"kind": "python", "files": {"main.py": "print(1)"}, "args": ["main.py"]}
        sandbox.validate(ok)
        for bad in ("../x.py", "/etc/x", "a/../../x", "a//b", "a\\b", "", "./x"):
            with self.assertRaises(sandbox.JobError, msg=bad):
                sandbox.validate({**ok, "files": {bad: "x"}})
        with self.assertRaises(sandbox.JobError):
            sandbox.validate({**ok, "kind": "shell"})
        with self.assertRaises(sandbox.JobError):
            sandbox.validate({**ok, "cwd": "../"})
        with self.assertRaises(sandbox.JobError):
            sandbox.validate({**ok, "timeout": 10_000})
        with self.assertRaises(sandbox.JobError):
            sandbox.validate({**ok, "files": {"big.py": "x" * (sandbox.MAX_JOB_BYTES + 1)}})

    def test_go_module_follows_local_imports_only(self):
        root = Path(tempfile.mkdtemp())
        (root / "go.mod").write_text("module example.com/m\n\ngo 1.21\n")
        for rel, src in {
            "a/a.go": 'package a\nimport (\n\t"fmt"\n\t"example.com/m/b"\n)\nfunc A() { fmt.Println(b.B) }\n',
            "a/a_test.go": "package a\n",
            "a/testdata/in.txt": "data",
            "b/b.go": 'package b\nimport "example.com/m/c"\nvar B = c.C\n',
            "c/c.go": "package c\nvar C = 1\n",
            "unrelated/u.go": "package unrelated\n",
            "a/__pycache__/x.pyc": "junk",
        }.items():
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(src)
        files = sandbox.stage_go_module(root, ["a"], {"a/a.go": 'package a\nimport "example.com/m/b"\nvar _ = b.B\n'})
        self.assertEqual(sorted(files), ["a/a.go", "a/a_test.go", "a/testdata/in.txt", "b/b.go", "c/c.go", "go.mod"])
        self.assertIn("var _ = b.B", files["a/a.go"])          # the learner's buffer wins

    def test_scratch_package_imports(self):
        root = Path(tempfile.mkdtemp())
        (root / "go.mod").write_text("module m\n")
        (root / "pb").mkdir()
        (root / "pb" / "pb.go").write_text("package pb\n")
        files = sandbox.stage_go_module(root, [], {"scratch_run/main.go": 'package main\nimport _ "m/pb"\n'})
        self.assertEqual(sorted(files), ["go.mod", "pb/pb.go", "scratch_run/main.go"])

    def test_local_runner_python(self):
        r = sandbox.LocalRunner({"default": sys.executable}, None)
        out = r.run({"kind": "python", "args": ["main.py"], "files": {"main.py": "import helper; print(helper.X)",
                                                                       "helper.py": "X = 42"}})
        self.assertEqual((out["ok"], out["stdout"].strip()), (True, "42"))
        out = r.run({"kind": "python", "args": ["main.py"], "timeout": 1, "files": {"main.py": "while True: pass"}})
        self.assertTrue(out.get("timeout"))
        self.assertIn("Go toolchain", r.run({"kind": "go-run", "files": {}})["stderr"])

    def test_runs_never_write_into_content(self):
        topic = "01_rest_api_service"
        sol = server.eng_file("py", "04_custom_stream_reader_writer", "solution")
        before = sol.read_text()
        seen = []

        class Spy:
            available = {"python": True, "go": True}

            def run(self, job):
                seen.append(job)
                return {"ok": True, "stdout": "", "stderr": "", "exitCode": 0, "ms": 1}

        saved, server.RUNNER = server.RUNNER, Spy()
        try:
            server.run_eng("py", "04_custom_stream_reader_writer", "# mine")
            server.run_eng("go", topic, "package solution // mine")
            self.assertEqual(server.run_eng("go", "../x", "x")["stderr"], "Unknown topic.")
        finally:
            server.RUNNER = saved
        self.assertEqual(sol.read_text(), before)
        py, go = seen
        self.assertEqual(py["files"]["04_custom_stream_reader_writer/04_custom_stream_reader_writer_solution.py"], "# mine")
        self.assertIn("-m", py["args"])
        self.assertEqual(go["kind"], "go-test")
        self.assertEqual(go["files"][f"{topic}/solution/{topic}_solution.go"], "package solution // mine")
        self.assertIn("go.mod", go["files"])
        self.assertFalse([k for k in go["files"] if not (k.startswith(f"{topic}/") or k in ("go.mod", "go.sum"))])


class RunEntitlementTests(unittest.TestCase):
    def test_runs_follow_the_page_plan(self):
        self.assertIsNone(entitlements.check_run("/api/run", {"code": "x"}, "free"))
        self.assertIsNone(entitlements.check_run("/api/format", {}, "free"))
        denied = entitlements.check_run("/api/eng-run", {"lang": "go", "topic": "02_middleware_chain"}, "base")
        self.assertEqual((denied["error"], denied["requires"]), ("upgrade_required", "pro"))
        self.assertIsNone(entitlements.check_run("/api/eng-run", {"lang": "go", "topic": "02_middleware_chain"}, "pro"))
        self.assertIsNone(entitlements.check_run("/api/eng-run", {"lang": "go", "topic": "01_rest_api_service"}, "free"))
        self.assertIsNone(entitlements.check_run("/api/stdlib-run", {"lang": "go", "pkg": "01_os"}, "free"))
        self.assertIsNotNone(entitlements.check_run("/api/stdlib-run", {"lang": "go", "pkg": "02_io"}, "free"))
        self.assertIsNotNone(entitlements.check_run("/api/api-run", {"type": "REST"}, "base"))
        self.assertEqual(entitlements.check_run("/api/eng-run", {"lang": "sh"}, "pro_max")["error"], "forbidden")
        self.assertEqual(entitlements.check_run("/api/nope", {}, "pro_max")["error"], "forbidden")


class FakeRunner(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True


class HostedRunTests(unittest.TestCase):
    """The hosted handler with a stand-in runner on a Unix socket."""

    @classmethod
    def setUpClass(cls):
        cls.jobs = []
        jobs = cls.jobs

        class H(socketserver.BaseRequestHandler):
            def handle(self):
                job = sandbox.recv_frame(self.request, 10_000_000)
                if job.get("kind") == "ping":
                    sandbox.send_frame(self.request, {"ok": True})
                    return
                jobs.append(job)
                if "slow" in json.dumps(job.get("files")):
                    time.sleep(1.0)
                sandbox.send_frame(self.request, {"ok": True, "stdout": f"ran {job['kind']}\n", "stderr": "",
                                                  "exitCode": 0, "ms": 1})

        cls.sock = os.path.join(tempfile.mkdtemp(), "runner.sock")
        cls.fake = FakeRunner(cls.sock, H)
        threading.Thread(target=cls.fake.serve_forever, daemon=True).start()
        cls.saved = {k: getattr(server, k) for k in
                     ("AUTH_ENABLED", "AUTH", "GOOGLE", "COOKIE_SECURE", "SESSION_COOKIE", "RUNNER",
                      "RUNNER_SOCKET", "RUN_RATE_MINUTE", "RUN_RATE_HOUR")}
        server.AUTH_ENABLED, server.COOKIE_SECURE, server.SESSION_COOKIE = True, False, "eg_session"
        server.AUTH = cls.store = new_store(Clock(time.time()))
        server.GOOGLE = None
        server.RUNNER, server.RUNNER_SOCKET = None, cls.sock
        server.RUN_RATE_MINUTE = auth.RateLimiter(1000, 60)
        server.RUN_RATE_HOUR = auth.RateLimiter(1000, 3600)
        cls.httpd = server.StudioServer(("127.0.0.1", 0), server.Handler)
        cls.port = cls.httpd.server_address[1]
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.fake.shutdown()
        for k, v in cls.saved.items():
            setattr(server, k, v)

    def req(self, method, path, body=None, cookie=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        headers = {"Origin": f"http://127.0.0.1:{self.port}"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if cookie:
            headers["Cookie"] = cookie
        c.request(method, path, json.dumps(body) if body is not None else None, headers)
        r = c.getresponse()
        data = json.loads(r.read() or b"null")
        c.close()
        return r.status, data

    def login(self, email, tier="free"):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        h = {"Origin": f"http://127.0.0.1:{self.port}", "Content-Type": "application/json"}
        c.request("POST", "/api/auth/request-otp", json.dumps({"email": email}), h)
        c.getresponse().read()
        c.request("POST", "/api/auth/verify-otp", json.dumps({"email": email, "code": last_code(self.store)}), h)
        r = c.getresponse()
        r.read()
        c.close()
        if tier != "free":
            self.store.set_tier(email, tier)
        return r.getheader("Set-Cookie").split(";")[0]

    def test_runs_go_to_the_runner(self):
        cookie = self.login("runner-free@example.com")
        st, boot = self.req("GET", "/api/bootstrap", cookie=cookie)
        self.assertEqual(boot["runtimes"], {"python": True, "go": True})
        st, out = self.req("POST", "/api/run", {"code": "print(1)", "lang": "py"}, cookie=cookie)
        self.assertEqual((st, out["stdout"]), (200, "ran python\n"))
        self.assertEqual(self.jobs[-1]["files"], {"main.py": "print(1)"})

    def test_signed_out_and_plan_checks(self):
        self.assertEqual(self.req("POST", "/api/run", {"code": "print(1)"})[0], 401)
        free = self.login("runner-free2@example.com")
        n = len(self.jobs)
        st, out = self.req("POST", "/api/eng-run", {"lang": "go", "topic": "02_middleware_chain",
                                                     "code": "package solution"}, cookie=free)
        self.assertEqual((st, out["error"]), (403, "upgrade_required"))
        self.assertEqual(len(self.jobs), n)                 # nothing reached the runner
        pro = self.login("runner-pro@example.com", "pro")
        st, out = self.req("POST", "/api/eng-run", {"lang": "go", "topic": "02_middleware_chain",
                                                     "code": "package solution"}, cookie=pro)
        self.assertEqual((st, out["stdout"]), (200, "ran go-test\n"))

    def test_one_run_at_a_time_and_rate_limit(self):
        cookie = self.login("runner-busy@example.com")
        results = []
        slow = threading.Thread(target=lambda: results.append(
            self.req("POST", "/api/run", {"code": "slow()", "lang": "py"}, cookie=cookie)))
        slow.start()
        time.sleep(0.3)
        st, out = self.req("POST", "/api/run", {"code": "print(2)", "lang": "py"}, cookie=cookie)
        self.assertEqual((st, out["error"]), (429, "busy"))
        slow.join()
        self.assertEqual(results[0][0], 200)
        saved, server.RUN_RATE_MINUTE = server.RUN_RATE_MINUTE, auth.RateLimiter(2, 60)
        try:
            other = self.login("runner-rate@example.com")
            codes = [self.req("POST", "/api/format", {"code": "package main"}, cookie=other)[0] for _ in range(3)]
            self.assertEqual(codes, [200, 200, 429])
        finally:
            server.RUN_RATE_MINUTE = saved


@unittest.skipUnless(sys.platform.startswith("linux") and hasattr(os, "geteuid") and os.geteuid() == 0,
                     "the sandbox daemon switches users: needs root on Linux")
class RunnerDaemonTests(unittest.TestCase):
    """runner.handle() for real: throwaway users, limits, cleanup."""

    @classmethod
    def setUpClass(cls):
        import runner
        cls.runner = runner
        cls.saved = (runner.WORK, runner.PYTHON)
        runner.WORK = Path(tempfile.mkdtemp(prefix="egwork-", dir="/tmp"))
        os.chmod(runner.WORK, 0o711)
        runner.PYTHON = sys.executable
        while not runner._slots.empty():
            runner._slots.get()
        for i in range(2):
            runner._slots.put(runner.SANDBOX_UID0 + i)

    @classmethod
    def tearDownClass(cls):
        cls.runner.WORK, cls.runner.PYTHON = cls.saved

    def py(self, code, timeout=5):
        return self.runner.handle({"kind": "python", "args": ["main.py"], "timeout": timeout,
                                   "files": {"main.py": code}})

    def test_runs_as_a_throwaway_user(self):
        out = self.py("import os; print(os.getuid(), os.getgroups())")
        uid, groups = out["stdout"].split(" ", 1)
        self.assertGreaterEqual(int(uid), self.runner.SANDBOX_UID0)
        self.assertEqual(groups.strip(), "[]")
        self.assertIn("PermissionError", self.py("open('/root/.bashrc')")["stderr"] or "PermissionError")

    def test_limits_and_cleanup(self):
        self.assertTrue(self.py("while True: pass", timeout=2).get("timeout"))
        self.assertIn("MemoryError", self.py("x = bytearray(4 * 1024**3)")["stderr"])
        out = self.py("import subprocess; subprocess.Popen(['sleep', '300'], start_new_session=True)")
        self.assertTrue(out["ok"])
        left = [p for p in os.listdir("/proc") if p.isdigit() and
                Path(f"/proc/{p}/cmdline").exists() and b"sleep\x00300" in Path(f"/proc/{p}/cmdline").read_bytes()]
        self.assertEqual(left, [])
        self.assertEqual(list(self.runner.WORK.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
