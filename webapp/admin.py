#!/usr/bin/env python3
"""Manage accounts and subscriptions of the hosted guide (EG_AUTH=1).

    python3 webapp/admin.py users
    python3 webapp/admin.py grant  person@example.com pro --days 30
    python3 webapp/admin.py grant  person@example.com pro_max          (no expiry)
    python3 webapp/admin.py revoke person@example.com                  (back to free)
    python3 webapp/admin.py signout person@example.com                 (end every session)
    python3 webapp/admin.py disable person@example.com | enable person@example.com
    python3 webapp/admin.py delete person@example.com
    python3 webapp/admin.py events [--limit 50]

Tiers: free, base, pro, pro_max (webapp/entitlements.py says what each one reads).
Runs against the same database as the server (EG_AUTH_DB, default
webapp/data/auth.sqlite3); a billing integration would call AuthStore.set_tier()
the same way `grant` does. Standard library only.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import auth            # noqa: E402
import entitlements    # noqa: E402
import server          # noqa: E402  (paths and EG_AUTH_DB)


def fmt_time(ts) -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts)) if ts else "-"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("users", help="list accounts")
    g = sub.add_parser("grant", help="set a subscription tier")
    g.add_argument("email")
    g.add_argument("tier", choices=entitlements.TIERS)
    g.add_argument("--days", type=int, help="expires after N days (default: never)")
    for name in ("revoke", "signout", "disable", "enable", "delete"):
        sub.add_parser(name).add_argument("email")
    e = sub.add_parser("events", help="recent sign-in events")
    e.add_argument("--limit", type=int, default=50)
    args = ap.parse_args()

    store = auth.AuthStore(server.AUTH_DB, auth.load_secret(server.AUTH_DB.parent), auth.Mailer({}))
    try:
        if args.cmd == "users":
            rows = store.list_users()
            print(f"{'email':38} {'tier':8} {'expires':16} {'devices':7} {'last sign-in':16} status")
            for u in rows:
                tier = store.effective_tier(u)
                print(f"{u['email']:38} {tier:8} {fmt_time(u['tier_expires_at']):16} {u['sessions']:<7} "
                      f"{fmt_time(u['last_login_at']):16} {'disabled' if u['disabled'] else 'verified' if u['verified_at'] else 'not signed in yet'}")
            print(f"{len(rows)} account(s)")
        elif args.cmd == "grant":
            expires = store.now() + args.days * 86400 if args.days else None
            store.set_tier(args.email, args.tier, expires)
            print(f"{args.email}: {entitlements.TIER_NAMES[args.tier]}"
                  + (f" until {fmt_time(expires)}" if expires else " (no expiry)"))
        elif args.cmd == "revoke":
            store.set_tier(args.email, "free", None)
            print(f"{args.email}: back to Free")
        elif args.cmd == "signout":
            print(f"{store.revoke_sessions(args.email)} session(s) ended")
        elif args.cmd in ("disable", "enable"):
            store.set_disabled(args.email, args.cmd == "disable")
            print(f"{args.email}: {args.cmd}d")
        elif args.cmd == "delete":
            print("deleted" if store.delete_user(args.email) else "no such account")
        elif args.cmd == "events":
            for r in reversed(store._q("SELECT * FROM auth_events ORDER BY id DESC LIMIT ?", (args.limit,))):
                print(f"{fmt_time(r['ts'])}  {r['kind']:20} {r['email'] or '':34} {r['ip'] or '':15} {r['note'] or ''}")
    except auth.AuthError as e:
        sys.exit(e.message)


if __name__ == "__main__":
    main()
