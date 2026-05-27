# CCR Gallery — Claude Instructions

## What this project does
Generates a self-contained HTML screenshot gallery from a CSV of suspicious domains,
pulling screenshot data from GeoEdge's internal tool (internal.geoedge.com).
Each run is fresh — input a CSV, get a gallery HTML file with thumbnails, filters, and job links.

## How to run it

### Step 1 — Install dependencies (first time only)
```
python -m pip install -r requirements.txt
python -m playwright install chromium
```

### Step 2 — Set credentials (first time only)
```powershell
$env:GEOEDGE_USER = "your.name@geoedge.com"
$env:GEOEDGE_PASS = "your_password"
```
First run opens Chrome, logs in via Microsoft SSO, saves session to ~/.geoedge_session.
Every run after that is silent — no browser window, no manual cookie copying.

Fallback: if you prefer manual cookie, set $env:GEOEDGE_COOKIE = "ci_session=..."

### Step 3 — Run
```powershell
cd C:\Users\MorHacham\IdeaProjects\ccr-gallery
python main.py C:\Users\MorHacham\Downloads\yourfile.csv
```
Gallery opens automatically in the browser when done (saved as ccr_gallery.html).

## CSV format
Column names are case-insensitive. Supported columns:

| Column | Required | Description |
|--------|----------|-------------|
| display (or host, domain) | YES | Full hostname e.g. paymentsite.netlify.app |
| query (or tld) | optional | Parent domain for GeoEdge search. Auto-computed if missing |
| vendor | optional | confiant or TMT — colored badge |
| should_bl | optional | true/false — red BL badge |
| rdap_creation_date | optional | Domain registration date (YYYY-MM-DD format) |
| rdap_creation_days | optional | Days since registration |
| status | optional | Domain status |
| track_ads | optional | Track ads count |
| track_lp | optional | Track LP count |
| is_malicious | optional | true/false — red MALICIOUS badge |

## Gallery features
- **Lightbox** — click any thumbnail → opens full-resolution screenshot overlay (Escape or click outside to close)
- **Search** — live search by domain name
- **TLD filter** — dropdown to filter by TLD
- **Filter buttons** — All / BL / Confiant / TMT / Malicious / Has data / No data
- **Further Research button** — opens GeoEdge Search Jobs pre-filled with the domain, gallery view, Unique=None
- **Incident label** — shown in red bold per screenshot
- **LP URL** — clickable link per screenshot
- **Meta row** — rdap_creation_date, status, track_ads, track_lp per domain
- **Malicious badge** — red MALICIOUS badge when is_malicious=true

## Search type logic
- display == query → search_type=tld (Top Domain In Requests)
- display != query (subdomain) → search_type=host (Host In Requests)
- TLD queries are deduplicated — one fetch per unique TLD
- Up to 20 screenshots per domain, last 30 days

## Screenshot URL pattern
- Thumbnail: https://geoedge-analytics.s3.amazonaws.com/screenshots/XX/YY/landingthumb_HASH.jpg
- Full size:  https://geoedge-analytics.s3.amazonaws.com/screenshots/XX/YY/landing_HASH.jpg

## Files
- main.py — CLI entrypoint, CSV parsing, orchestration
- auth.py — Microsoft SSO auto-login via Playwright, session caching in ~/.geoedge_session
- scraper.py — fetches screenshot data from GeoEdge internal tool, parses HTML table
- builder.py — renders the self-contained HTML gallery from scraped data
- requirements.txt — requests, beautifulsoup4, playwright
- test_search_type.py — compares tld vs top_domain_in_requests search types (run manually to test)

## Pending: Slack Integration
Not yet implemented. Plan documented below.

### Trigger
A new CSV file is posted in Slack channel C08ENA1U50D

### Normal behavior (Mon–Thu)
When a file is posted → download it → run scraper → build gallery → post result back to channel

### Sunday edge case (Israel work week: Sun–Thu)
On Sunday, collect all CSV files posted since Thursday EOD (Friday + Saturday + Sunday).
Merge into one combined gallery, deduplicate domains, run scraper once, post to Slack.

### Logic
```
if today == Sunday:
    collect files from: Friday + Saturday + Sunday
    merge all rows, deduplicate by display domain
    run scraper on merged list
else:
    collect files from: today only
    run scraper normally
```

### Open questions before building
1. Slack token — bot token or user token? needs to be created
2. File download — download CSV from Slack via API
3. Post result back — upload gallery HTML to Slack or post a download link
4. Where does it run — local machine, server, or scheduled task?

## Options
```
python main.py input.csv --out my_gallery.html   # save to custom filename
python main.py input.csv --no-open               # don't auto-open the browser
python main.py input.csv --cookie "ci_session=…" # override cookie manually
```
