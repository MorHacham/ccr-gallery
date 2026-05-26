"""
Quick test: compare 'tld' vs 'top_domain_in_requests' for a few domains.
Usage: python test_search_type.py netlify.app cloudfront.net example.com
"""
import os, sys
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup

INTERNAL = "https://internal.geoedge.com"
COMMON = (
    "req_rpt_period=last30days&job_status=all&no_ads=all&scan_type=-1"
    "&code_type=-1&is_manual=&location=0&emulation_category=-1&location_via=all"
    "&malware_type=0&is_sound=&is_fake=&event_type=-1&is_screenshot=&security_rule="
    "&security_rule_extra_id=0&preview=landing"
    "&group=landing_title&rows_limit=500&rows_order=&submit=Search"
)

def count_results(session, query, search_type):
    url = (f"{INTERNAL}/admin_geinternalpage/analytics/snapshots_jobs?{COMMON}"
           f"&search_type%5B%5D={search_type}&search_q%5B%5D={quote(query)}")
    r = session.get(url, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")
    rows = soup.select("#tblRows tbody tr")
    shots = sum(1 for row in rows if row.select_one("label.lp-preview img"))
    return shots

cookie = os.environ.get("GEOEDGE_COOKIE", "")
if not cookie:
    print("Set $env:GEOEDGE_COOKIE first"); sys.exit(1)

queries = sys.argv[1:] or ["netlify.app", "cloudfront.net", "com"]

session = requests.Session()
session.headers.update({"Cookie": cookie, "User-Agent": "Mozilla/5.0"})

print(f"{'Domain':<35} {'tld':>6} {'top_domain_in_requests':>22}  winner")
print("-" * 72)
for q in queries:
    a = count_results(session, q, "tld")
    b = count_results(session, q, "top_domain_in_requests")
    winner = "tld" if a > b else ("top_domain_in_requests" if b > a else "same")
    print(f"{q:<35} {a:>6} {b:>22}  {winner}")
