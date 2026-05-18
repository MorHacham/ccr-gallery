# ccr-gallery

Build a GeoEdge screenshot inspection gallery from a CSV of domains. Each run is fresh — input your CSV, get a self-contained HTML gallery with thumbnails, job links, search, and filters.

## Usage

```bash
pip install -r requirements.txt
python main.py input.csv
```

The gallery opens automatically in your browser when done.

## Authentication

You must be logged into `internal.geoedge.com`. Pass your session cookie via env var or flag:

```bash
# Option 1: environment variable (recommended)
export GEOEDGE_COOKIE="sessionid=abc123; csrftoken=xyz"
python main.py input.csv

# Option 2: command-line flag
python main.py input.csv --cookie "sessionid=abc123"
```

**How to get your cookie:**
1. Open `internal.geoedge.com` in Chrome while logged in
2. Press `F12` → **Application** tab → **Cookies** → `internal.geoedge.com`
3. Copy all `Name=Value` pairs as a single semicolon-separated string

## CSV format

Column names are case-insensitive. Supported columns:

| Column | Required | Description |
|--------|----------|-------------|
| `display` (or `host`, `domain`) | ✅ | Full hostname, e.g. `paymentsite.netlify.app` |
| `query` (or `tld`) | optional | Parent domain for GeoEdge search. Auto-computed if omitted. |
| `vendor` | optional | `confiant` or `TMT` — shown as a colored badge |
| `should_bl` | optional | `true`/`false` — shown as a red BL badge |

**Minimal CSV example:**
```csv
display
cleardriftessence.com
paymentsucessfullyapprovedsystems.netlify.app
buyretailelite.z13.web.core.windows.net
```

**Full CSV example:**
```csv
display,query,vendor,should_bl
cleardriftessence.com,cleardriftessence.com,confiant,true
paymentsucessfullyapprovedsystems.netlify.app,netlify.app,confiant,false
buyretailelite.z13.web.core.windows.net,z13.web.core.windows.net,TMT,true
```

## How it works

- Rows where `display == query` → searched with **Top Domain In Requests** (`search_type=tld`)
- Rows where `display != query` (subdomains) → searched with **Host In Requests** (`search_type=host`)
- TLD queries are deduplicated — one fetch per unique TLD
- Up to 20 screenshots per domain, last 30 days, grouped by landing title

## Options

```
python main.py input.csv [OPTIONS]

Options:
  --cookie TEXT    GeoEdge cookie string
  --out PATH       Output HTML file (default: ccr_gallery.html)
  --no-open        Don't open the browser automatically
```
