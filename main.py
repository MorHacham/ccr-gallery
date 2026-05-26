#!/usr/bin/env python3
"""
ccr-gallery: build a GeoEdge screenshot gallery from a CSV of domains.

Usage:
    python main.py input.csv
    python main.py input.csv --cookie "sessionid=abc123; csrftoken=xyz"
    python main.py input.csv --out gallery.html --no-open

Authentication:
    Set the GEOEDGE_COOKIE environment variable, or pass --cookie.
    Get your cookie from: internal.geoedge.com → DevTools (F12) →
    Application → Cookies → copy all cookie values as a single string.

CSV format (any delimiter, column names are case-insensitive):
    Required: a column named 'display' (or 'host'/'domain') with the full hostname.
    Optional: 'query'/'tld'   - parent domain to search (auto-computed if missing)
              'vendor'         - confiant or TMT  (for badge display)
              'should_bl'      - true/false        (for BL badge)
"""

import argparse
import csv
import os
import sys
import webbrowser
from pathlib import Path

from builder import build_gallery
from scraper import scrape_all


# ---------------------------------------------------------------------------
# CSV parsing
# ---------------------------------------------------------------------------

def _compute_query(display):
    """Strip the first DNS label to get the parent domain used for TLD search.
    Domains with only two labels (e.g. 'example.com') are their own query.
    """
    parts = display.split(".")
    if len(parts) <= 2:
        return display
    return ".".join(parts[1:])


def parse_csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        # Sniff delimiter
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel

        reader = csv.DictReader(f, dialect=dialect)
        for raw in reader:
            r = {k.lower().strip(): (v or "").strip() for k, v in raw.items() if k is not None}

            display = r.get("display") or r.get("host") or r.get("domain") or ""
            if not display:
                continue

            query = r.get("query") or r.get("tld") or _compute_query(display)
            vendor = r.get("vendor", "")
            should_bl = r.get("should_bl", "").lower() in ("true", "1", "yes")

            rows.append({
                "display": display,
                "query": query,
                "vendor": vendor,
                "should_bl": should_bl,
                "tld": r.get("tld", query),
                "rdap_creation_date": r.get("rdap_creation_date", ""),
                "rdap_creation_days": r.get("rdap_creation_days", ""),
                "status": r.get("status", ""),
                "track_ads": r.get("track_ads", ""),
                "track_lp": r.get("track_lp", ""),
                "is_malicious": r.get("is_malicious", "").lower() in ("true", "1", "yes"),
            })
    return rows


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Build a GeoEdge screenshot gallery from a CSV of domains.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("csv", help="Input CSV file")
    parser.add_argument(
        "--cookie",
        help="GeoEdge cookie string (or set GEOEDGE_COOKIE env var)",
    )
    parser.add_argument(
        "--out",
        default="ccr_gallery.html",
        help="Output HTML path (default: ccr_gallery.html)",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Skip opening the gallery in the browser",
    )
    args = parser.parse_args()

    cookie = args.cookie or os.environ.get("GEOEDGE_COOKIE", "")
    if not cookie:
        print(
            "ERROR: No GeoEdge cookie provided.\n"
            "  Option 1: set env var  GEOEDGE_COOKIE='sessionid=…'\n"
            "  Option 2: pass flag    --cookie 'sessionid=…'\n"
            "\n"
            "  How to get your cookie:\n"
            "    1. Open internal.geoedge.com in Chrome while logged in\n"
            "    2. Press F12 → Application tab → Cookies → internal.geoedge.com\n"
            "    3. Copy the Name=Value pairs (at minimum 'sessionid')\n",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Loading {args.csv} ...")
    rows = parse_csv(args.csv)
    if not rows:
        print("ERROR: No rows found in CSV.", file=sys.stderr)
        sys.exit(1)
    print(f"  {len(rows)} rows loaded")

    print("Scraping GeoEdge ...")
    screenshot_data = scrape_all(rows, cookie)

    with_data = sum(1 for v in screenshot_data.values() if v)
    total_shots = sum(len(v) for v in screenshot_data.values())
    print(f"  {with_data} domains with screenshots, {total_shots} total shots")

    print("Building gallery ...")
    html = build_gallery(rows, screenshot_data)

    out = Path(args.out)
    out.write_text(html, encoding="utf-8")
    print(f"  Saved → {out.resolve()}")

    if not args.no_open:
        webbrowser.open(out.resolve().as_uri())


if __name__ == "__main__":
    main()
