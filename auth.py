"""
GeoEdge authentication via Microsoft SSO using Playwright + system Chrome.

First run: opens a visible Chrome window, auto-fills credentials, waits for
MFA approval if needed (up to 3 minutes), then saves the session.

Subsequent runs: reuses the saved session silently (headless).
"""

import os
import sys
from pathlib import Path

INTERNAL    = "https://internal.geoedge.com"
TARGET      = f"{INTERNAL}/admin_geinternalpage/analytics/snapshots_jobs"
LOGIN_URL   = f"{INTERNAL}/admin_geinternalpage/login/"
SESSION_DIR = Path.home() / ".geoedge_session"

LAUNCH_OPTS = dict(
    channel="chrome",
    args=["--no-sandbox", "--disable-dev-shm-usage"],
)


def _cookie_string(context):
    return "; ".join(
        f"{c['name']}={c['value']}"
        for c in context.cookies()
        if "geoedge.com" in c.get("domain", "")
    )


def _is_on_internal(url):
    return "internal.geoedge.com" in url and "login" not in url.lower()


def _session_still_valid(context):
    page = context.new_page()
    try:
        page.goto(TARGET, wait_until="domcontentloaded", timeout=20_000)
        return _is_on_internal(page.url)
    except Exception:
        return False
    finally:
        page.close()


def get_cookie():
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        print("  playwright not installed — run: pip install playwright && python -m playwright install chromium", file=sys.stderr)
        return ""

    user = os.environ.get("GEOEDGE_USER", "")
    pwd  = os.environ.get("GEOEDGE_PASS", "")
    ms_user = user if "@" in user else f"{user}@geoedge.com"

    with sync_playwright() as p:

        # 1. Try saved session silently (headless)
        if SESSION_DIR.exists():
            try:
                ctx = p.chromium.launch_persistent_context(
                    str(SESSION_DIR), headless=True, **LAUNCH_OPTS
                )
                if _session_still_valid(ctx):
                    cookie = _cookie_string(ctx)
                    ctx.close()
                    print("  Using saved GeoEdge session.")
                    return cookie
                ctx.close()
            except Exception:
                pass  # session corrupt or Chrome not found — fall through to login

        # 2. Full SSO login in visible browser
        if not user or not pwd:
            print(
                "ERROR: No saved session found. Set credentials to auto-login:\n"
                "  $env:GEOEDGE_USER = 'your.name@geoedge.com'\n"
                "  $env:GEOEDGE_PASS = 'your_password'\n"
                "Or pass a raw cookie:\n"
                "  $env:GEOEDGE_COOKIE = 'ci_session=…'\n",
                file=sys.stderr,
            )
            return ""

        print("  Opening Chrome for GeoEdge SSO login ...")
        print("  If MFA is required, approve it in the browser window (up to 3 min).")
        ctx = p.chromium.launch_persistent_context(
            str(SESSION_DIR), headless=False, **LAUNCH_OPTS
        )
        page = ctx.new_page()
        page.goto(LOGIN_URL, wait_until="domcontentloaded")

        try:
            try:
                page.wait_for_selector("input[type=email]", timeout=12_000)
                page.fill("input[type=email]", ms_user)
                page.keyboard.press("Enter")
            except PWTimeout:
                pass

            try:
                page.wait_for_selector("input[type=password]", timeout=12_000)
                page.fill("input[type=password]", pwd)
                page.keyboard.press("Enter")
            except PWTimeout:
                pass

            # "Stay signed in?" prompt
            try:
                page.wait_for_selector("#idBtn_Accept", timeout=8_000)
                page.click("#idBtn_Accept")
            except PWTimeout:
                pass

            print("  Waiting for login to complete ...")
            page.wait_for_url(f"{INTERNAL}/**", timeout=180_000)

        except PWTimeout:
            print(f"  Login timed out. Current URL: {page.url}", file=sys.stderr)
            ctx.close()
            return ""

        cookie = _cookie_string(ctx)
        ctx.close()
        print("  Login successful — session saved for future runs.")
        return cookie
