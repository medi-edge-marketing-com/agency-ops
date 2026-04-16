#!/usr/bin/env python3
"""
SEO Monthly Report Generator
Pulls GA4 data and generates a clean, client-ready HTML report.

Usage:
  python generate_report.py --property 514842555 --month 3 --year 2026 --client "Tierzero"

Credentials — set as environment variables or place in a .env file:
  GOOGLE_CLIENT_ID
  GOOGLE_CLIENT_SECRET
  GOOGLE_REFRESH_TOKEN

Output: report_<client>_<month>_<year>.html (open in browser, print as PDF)
"""

import json
import os
import sys
import math
import argparse
import urllib.request
import urllib.parse
from datetime import date, datetime
from calendar import monthrange


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def load_env(path=".env"):
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def get_access_token():
    client_id     = os.environ["GOOGLE_CLIENT_ID"]
    client_secret = os.environ["GOOGLE_CLIENT_SECRET"]
    refresh_token = os.environ["GOOGLE_REFRESH_TOKEN"]

    payload = urllib.parse.urlencode({
        "client_id":     client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type":    "refresh_token",
    }).encode()

    req  = urllib.request.Request("https://oauth2.googleapis.com/token", data=payload)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())["access_token"]


# ---------------------------------------------------------------------------
# GA4 helpers
# ---------------------------------------------------------------------------

def ga4_report(token, property_id, body):
    url  = f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport"
    data = json.dumps(body).encode()
    req  = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
    })
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())


def parse_rows(result):
    dim_headers = [h["name"] for h in result.get("dimensionHeaders", [])]
    met_headers = [h["name"] for h in result.get("metricHeaders",   [])]
    rows = []
    for r in result.get("rows", []):
        row = {}
        for i, h in enumerate(dim_headers):
            row[h] = r["dimensionValues"][i]["value"]
        for i, h in enumerate(met_headers):
            row[h] = r["metricValues"][i]["value"]
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

def fetch_all(token, prop, year, month):
    # Date ranges
    _, last_day   = monthrange(year, month)
    this_start    = f"{year}-{month:02d}-01"
    this_end      = f"{year}-{month:02d}-{last_day:02d}"

    prev_month    = month - 1 if month > 1 else 12
    prev_year     = year if month > 1 else year - 1
    _, prev_last  = monthrange(prev_year, prev_month)
    prev_start    = f"{prev_year}-{prev_month:02d}-01"
    prev_end      = f"{prev_year}-{prev_month:02d}-{prev_last:02d}"

    date_ranges = [
        {"startDate": this_start, "endDate": this_end,  "name": "current"},
        {"startDate": prev_start, "endDate": prev_end,  "name": "previous"},
    ]

    # 1. Overall totals
    totals_raw = ga4_report(token, prop, {
        "dateRanges": date_ranges,
        "metrics": [
            {"name": "sessions"},
            {"name": "totalUsers"},
            {"name": "screenPageViews"},
            {"name": "averageSessionDuration"},
            {"name": "engagementRate"},
            {"name": "bounceRate"},
        ],
    })
    totals_rows = parse_rows(totals_raw)
    totals = {r.get("dateRange", r.get("date", "")): r for r in totals_rows}

    # 2. Channel breakdown
    channel_raw = ga4_report(token, prop, {
        "dateRanges": date_ranges,
        "metrics": [{"name": "sessions"}, {"name": "totalUsers"}],
        "dimensions": [{"name": "sessionDefaultChannelGroup"}],
    })
    channel_rows = parse_rows(channel_raw)

    # 3. Top pages
    pages_raw = ga4_report(token, prop, {
        "dateRanges": [{"startDate": this_start, "endDate": this_end}],
        "metrics": [
            {"name": "sessions"},
            {"name": "screenPageViews"},
            {"name": "averageSessionDuration"},
        ],
        "dimensions": [{"name": "pagePath"}, {"name": "pageTitle"}],
        "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}],
        "limit": 15,
    })
    pages_rows = parse_rows(pages_raw)

    # 4. Daily trend
    daily_raw = ga4_report(token, prop, {
        "dateRanges": [{"startDate": this_start, "endDate": this_end}],
        "metrics": [{"name": "sessions"}],
        "dimensions": [{"name": "date"}],
        "orderBys": [{"dimension": {"dimensionName": "date"}}],
    })
    daily_rows = parse_rows(daily_raw)

    # 5. Device
    device_raw = ga4_report(token, prop, {
        "dateRanges": [{"startDate": this_start, "endDate": this_end}],
        "metrics": [{"name": "sessions"}],
        "dimensions": [{"name": "deviceCategory"}],
    })
    device_rows = parse_rows(device_raw)

    # 6. Top US cities only
    city_raw = ga4_report(token, prop, {
        "dateRanges": [{"startDate": this_start, "endDate": this_end}],
        "metrics": [{"name": "sessions"}],
        "dimensions": [{"name": "country"}, {"name": "city"}],
        "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}],
        "limit": 30,
    })
    city_rows = parse_rows(city_raw)

    # 7. New vs returning
    nvr_raw = ga4_report(token, prop, {
        "dateRanges": [{"startDate": this_start, "endDate": this_end}],
        "metrics": [{"name": "sessions"}],
        "dimensions": [{"name": "newVsReturning"}],
    })
    nvr_rows = parse_rows(nvr_raw)

    return {
        "totals":   totals,
        "channels": channel_rows,
        "pages":    pages_rows,
        "daily":    daily_rows,
        "devices":  device_rows,
        "cities":   city_rows,
        "nvr":      nvr_rows,
        "meta": {
            "year": year, "month": month,
            "this_start": this_start, "this_end": this_end,
            "prev_start": prev_start, "prev_end": prev_end,
        }
    }


# ---------------------------------------------------------------------------
# Data processing
# ---------------------------------------------------------------------------

def pct_change(new, old):
    new, old = float(new), float(old)
    if old == 0: return None
    return ((new - old) / old) * 100


def arrow(pct, invert=False):
    """Return trend indicator. invert=True for metrics where down is good (bounce rate)."""
    if pct is None: return ""
    positive = pct > 0
    if invert: positive = not positive
    if positive:
        return f'<span class="up">▲ {abs(pct):.1f}%</span>'
    else:
        return f'<span class="down">▼ {abs(pct):.1f}%</span>'


def fmt_dur(seconds):
    s = float(seconds)
    m = int(s // 60)
    sec = int(s % 60)
    return f"{m}m {sec:02d}s" if m else f"{sec}s"


def fmt_pct(v):
    return f"{float(v)*100:.1f}%"


def aggregate_channels(channel_rows, period):
    """Sum all channels for a period."""
    totals = {"sessions": 0, "totalUsers": 0}
    for r in channel_rows:
        if r.get("dateRange") == period:
            totals["sessions"]    += int(r.get("sessions", 0))
            totals["totalUsers"]  += int(r.get("totalUsers", 0))
    return totals


def get_channel(channel_rows, period, channel):
    for r in channel_rows:
        if r.get("dateRange") == period and r.get("sessionDefaultChannelGroup") == channel:
            return int(r.get("sessions", 0))
    return 0


def top_us_cities(city_rows, n=6):
    us_cities = [r for r in city_rows if r.get("country") == "United States" and r.get("city") not in ("(not set)", "")]
    return us_cities[:n]


def clean_pages(pages_rows):
    """Filter out obvious bot/low-intent pages."""
    skip = {"/privacy/", "/legal/", "/robots.txt", "/sitemap.xml"}
    out = []
    for r in pages_rows:
        path = r.get("pagePath", "")
        dur  = float(r.get("averageSessionDuration", 0))
        # Skip: known bot-bait pages with <5s avg duration
        if path in skip and dur < 10:
            continue
        out.append(r)
    return out[:8]


def page_label(path, title):
    labels = {
        "/":                    "Homepage",
        "/switch/":             "Switch to Tierzero",
        "/contact/":            "Contact",
        "/about/":              "About",
        "/blog/":               "Blog",
        "/services/internet/":  "Internet Services",
        "/services/voice/":     "Voice Services",
        "/support/":            "Support",
        "/legal/":              "Legal",
        "/privacy/":            "Privacy Policy",
    }
    if path in labels:
        return labels[path]
    # Fallback: prettify the path
    clean = path.strip("/").replace("-", " ").replace("/", " › ").title()
    return clean or title or path


def build_svg_chart(daily_rows):
    """Generate an inline SVG sparkline/area chart of daily sessions."""
    if not daily_rows:
        return ""

    values = [int(r.get("sessions", 0)) for r in daily_rows]
    labels = [r.get("date", "") for r in daily_rows]  # YYYYMMDD
    n      = len(values)
    max_v  = max(values) if values else 1
    min_v  = 0

    W, H   = 800, 200
    pad    = {"top": 20, "right": 20, "bottom": 30, "left": 45}
    inner_w = W - pad["left"] - pad["right"]
    inner_h = H - pad["top"]  - pad["bottom"]

    def x(i):
        return pad["left"] + (i / (n - 1)) * inner_w if n > 1 else pad["left"]

    def y(v):
        return pad["top"] + inner_h - ((v - min_v) / (max_v - min_v + 1)) * inner_h

    # Polyline points
    pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(values))

    # Area fill path
    area = (
        f"M {x(0):.1f},{y(0):.1f} "
        + " ".join(f"L {x(i):.1f},{y(v):.1f}" for i, v in enumerate(values))
        + f" L {x(n-1):.1f},{H - pad['bottom']} L {x(0):.1f},{H - pad['bottom']} Z"
    )

    # Y-axis grid lines (3 levels)
    grid_vals = [0, max_v // 2, max_v]
    grid_lines = ""
    for gv in grid_vals:
        gy = y(gv)
        grid_lines += f'<line x1="{pad["left"]}" y1="{gy:.1f}" x2="{W - pad["right"]}" y2="{gy:.1f}" stroke="#e5e7eb" stroke-width="1"/>'
        grid_lines += f'<text x="{pad["left"] - 6}" y="{gy + 4:.1f}" text-anchor="end" font-size="10" fill="#9ca3af">{gv}</text>'

    # X-axis labels (show ~6 evenly spaced dates)
    x_labels = ""
    step = max(1, n // 6)
    for i in range(0, n, step):
        raw = labels[i]  # YYYYMMDD
        d   = f"{int(raw[6:8])}"
        xi  = x(i)
        x_labels += f'<text x="{xi:.1f}" y="{H - pad["bottom"] + 16}" text-anchor="middle" font-size="10" fill="#9ca3af">{d}</text>'

    # Tooltip circles on high points
    peak_i = values.index(max_v)
    peak_circle = f'<circle cx="{x(peak_i):.1f}" cy="{y(max_v):.1f}" r="4" fill="#2563eb"/>'
    peak_label  = f'<text x="{x(peak_i):.1f}" y="{y(max_v) - 8:.1f}" text-anchor="middle" font-size="10" fill="#2563eb" font-weight="600">{max_v}</text>'

    svg = f'''<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;display:block;">
  <defs>
    <linearGradient id="area-grad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#2563eb" stop-opacity="0.15"/>
      <stop offset="100%" stop-color="#2563eb" stop-opacity="0.01"/>
    </linearGradient>
  </defs>
  {grid_lines}
  <path d="{area}" fill="url(#area-grad)"/>
  <polyline points="{pts}" fill="none" stroke="#2563eb" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
  {peak_circle}
  {peak_label}
  {x_labels}
  <line x1="{pad['left']}" y1="{pad['top']}" x2="{pad['left']}" y2="{H - pad['bottom']}" stroke="#e5e7eb" stroke-width="1"/>
  <line x1="{pad['left']}" y1="{H - pad['bottom']}" x2="{W - pad['right']}" y2="{H - pad['bottom']}" stroke="#e5e7eb" stroke-width="1"/>
</svg>'''
    return svg


def build_donut(slices):
    """
    slices: list of (label, value, color)
    Returns inline SVG donut chart.
    """
    total  = sum(v for _, v, _ in slices)
    if total == 0:
        return ""
    R, r   = 70, 42  # outer, inner radius
    cx, cy = 80, 80
    W, H   = 200, 180

    def polar(cx, cy, radius, angle_deg):
        rad = math.radians(angle_deg - 90)
        return cx + radius * math.cos(rad), cy + radius * math.sin(rad)

    angle = 0
    paths = []
    for label, value, color in slices:
        sweep = (value / total) * 360
        large = 1 if sweep > 180 else 0
        x1o, y1o = polar(cx, cy, R, angle)
        x2o, y2o = polar(cx, cy, R, angle + sweep)
        x1i, y1i = polar(cx, cy, r, angle + sweep)
        x2i, y2i = polar(cx, cy, r, angle)
        d = (f"M {x1o:.2f} {y1o:.2f} "
             f"A {R} {R} 0 {large} 1 {x2o:.2f} {y2o:.2f} "
             f"L {x1i:.2f} {y1i:.2f} "
             f"A {r} {r} 0 {large} 0 {x2i:.2f} {y2i:.2f} Z")
        paths.append(f'<path d="{d}" fill="{color}"/>')
        angle += sweep

    legend = ""
    for i, (label, value, color) in enumerate(slices):
        pct = value / total * 100
        ly  = 16 + i * 22
        legend += (f'<rect x="110" y="{ly}" width="10" height="10" rx="2" fill="{color}"/>'
                   f'<text x="124" y="{ly + 9}" font-size="11" fill="#374151">'
                   f'{label} <tspan font-weight="600">{pct:.0f}%</tspan></text>')

    svg = f'''<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:220px;height:auto">
  {"".join(paths)}
  {legend}
</svg>'''
    return svg


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

MONTH_NAMES = ["", "January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f8fafc;
  color: #111827;
  font-size: 14px;
  line-height: 1.6;
}
.page { max-width: 900px; margin: 0 auto; padding: 32px 24px 64px; }

/* Header */
.report-header { display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:32px; padding-bottom:20px; border-bottom:2px solid #e5e7eb; }
.report-header h1 { font-size:24px; font-weight:700; color:#111827; }
.report-header .period { font-size:13px; color:#6b7280; margin-top:4px; }
.report-header .logo { font-size:13px; color:#6b7280; text-align:right; }
.report-header .logo strong { display:block; font-size:15px; color:#111827; }

/* Section */
.section { margin-bottom:36px; }
.section-title { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.08em; color:#6b7280; margin-bottom:14px; padding-bottom:8px; border-bottom:1px solid #e5e7eb; }

/* KPI cards */
.kpi-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:36px; }
.kpi-card { background:#fff; border:1px solid #e5e7eb; border-radius:10px; padding:18px 16px; }
.kpi-card .label { font-size:11px; color:#6b7280; font-weight:600; text-transform:uppercase; letter-spacing:.06em; margin-bottom:6px; }
.kpi-card .value { font-size:26px; font-weight:700; color:#111827; line-height:1; }
.kpi-card .change { font-size:12px; margin-top:6px; color:#6b7280; }
.up   { color:#16a34a; font-weight:600; }
.down { color:#dc2626; font-weight:600; }
.flat { color:#6b7280; }

/* Executive summary box */
.exec-box { background:#1e3a5f; color:#fff; border-radius:12px; padding:24px 28px; margin-bottom:36px; }
.exec-box h2 { font-size:16px; font-weight:700; margin-bottom:12px; color:#fff; }
.exec-box p  { font-size:13px; color:#cbd5e1; line-height:1.7; margin-bottom:8px; }
.exec-box p:last-child { margin-bottom:0; }
.exec-highlights { display:flex; gap:24px; margin-top:16px; flex-wrap:wrap; }
.exec-highlights .hl { background:rgba(255,255,255,.1); border-radius:8px; padding:10px 16px; }
.exec-highlights .hl .hl-label { font-size:10px; color:#94a3b8; text-transform:uppercase; letter-spacing:.06em; }
.exec-highlights .hl .hl-val   { font-size:18px; font-weight:700; color:#fff; margin-top:2px; }

/* Tables */
table { width:100%; border-collapse:collapse; background:#fff; border-radius:10px; overflow:hidden; border:1px solid #e5e7eb; }
thead tr { background:#f9fafb; }
th { text-align:left; padding:10px 14px; font-size:11px; font-weight:700; color:#6b7280; text-transform:uppercase; letter-spacing:.06em; border-bottom:1px solid #e5e7eb; }
td { padding:10px 14px; font-size:13px; color:#374151; border-bottom:1px solid #f3f4f6; }
tr:last-child td { border-bottom:none; }
tbody tr:hover { background:#f9fafb; }
.td-right { text-align:right; font-variant-numeric:tabular-nums; }
.td-bar { width:80px; }

/* Progress bar */
.bar-wrap { background:#f3f4f6; border-radius:4px; height:6px; overflow:hidden; }
.bar-fill  { height:6px; border-radius:4px; background:#2563eb; }

/* 2-col grid */
.two-col { display:grid; grid-template-columns:1fr 1fr; gap:20px; }
.chart-box { background:#fff; border:1px solid #e5e7eb; border-radius:10px; padding:20px; }
.chart-box h4 { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.06em; color:#6b7280; margin-bottom:16px; }

/* Channel pills */
.channel-pill { display:inline-block; padding:2px 8px; border-radius:99px; font-size:11px; font-weight:600; }
.ch-direct   { background:#eff6ff; color:#1d4ed8; }
.ch-organic  { background:#f0fdf4; color:#15803d; }
.ch-email    { background:#fff7ed; color:#c2410c; }
.ch-referral { background:#fdf4ff; color:#7e22ce; }
.ch-social   { background:#fef9c3; color:#854d0e; }
.ch-other    { background:#f3f4f6; color:#374151; }

/* Recommendations */
.rec-list { list-style:none; }
.rec-list li { display:flex; gap:14px; align-items:flex-start; padding:14px 0; border-bottom:1px solid #f3f4f6; }
.rec-list li:last-child { border-bottom:none; }
.rec-num { flex-shrink:0; width:28px; height:28px; background:#2563eb; color:#fff; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:700; }
.rec-list .rec-title { font-size:13px; font-weight:700; color:#111827; margin-bottom:3px; }
.rec-list .rec-body  { font-size:12px; color:#6b7280; line-height:1.5; }
.rec-wrap { background:#fff; border:1px solid #e5e7eb; border-radius:10px; padding:8px 20px 4px; }

/* Footer */
.report-footer { margin-top:48px; padding-top:16px; border-top:1px solid #e5e7eb; font-size:11px; color:#9ca3af; display:flex; justify-content:space-between; }

/* Print */
@media print {
  body { background:#fff; }
  .page { padding:16px; }
  .exec-box { -webkit-print-color-adjust:exact; print-color-adjust:exact; }
  .kpi-card, .chart-box, table { break-inside:avoid; }
}
"""


def generate_html(data, client_name, property_id):
    meta    = data["meta"]
    year    = meta["year"]
    month   = meta["month"]
    mon_str = MONTH_NAMES[month]

    # Totals
    curr = data["totals"].get("current", {})
    prev = data["totals"].get("previous", {})

    c_sessions = int(curr.get("sessions", 0))
    p_sessions = int(prev.get("sessions", 0))
    c_users    = int(curr.get("totalUsers", 0))
    p_users    = int(prev.get("totalUsers", 0))
    c_views    = int(curr.get("screenPageViews", 0))
    p_views    = int(prev.get("screenPageViews", 0))
    c_dur      = float(curr.get("averageSessionDuration", 0))
    p_dur      = float(prev.get("averageSessionDuration", 0))
    c_bounce   = float(curr.get("bounceRate", 0))
    p_bounce   = float(prev.get("bounceRate", 0))
    c_engage   = float(curr.get("engagementRate", 0))

    pct_sess   = pct_change(c_sessions, p_sessions)
    pct_users  = pct_change(c_users,    p_users)
    pct_views  = pct_change(c_views,    p_views)
    pct_dur    = pct_change(c_dur,      p_dur)
    pct_bounce = pct_change(c_bounce,   p_bounce)

    # Organic sessions
    c_organic  = get_channel(data["channels"], "current",  "Organic Search")
    p_organic  = get_channel(data["channels"], "previous", "Organic Search")
    pct_org    = pct_change(c_organic, p_organic)

    # Channel table
    channel_order = ["Direct", "Organic Search", "Email", "Referral", "Organic Social", "Paid Search"]
    channel_class  = {
        "Direct":         "ch-direct",
        "Organic Search": "ch-organic",
        "Email":          "ch-email",
        "Referral":       "ch-referral",
        "Organic Social": "ch-social",
    }

    ch_data = {}
    for r in data["channels"]:
        ch   = r.get("sessionDefaultChannelGroup", "Other")
        prd  = r.get("dateRange", "")
        if ch not in ch_data:
            ch_data[ch] = {"current": 0, "previous": 0}
        ch_data[ch][prd] = int(r.get("sessions", 0))

    # Top pages
    pages = clean_pages(data["pages"])

    # Devices
    devices     = {r["deviceCategory"]: int(r["sessions"]) for r in data["devices"]}
    total_dev   = sum(devices.values()) or 1
    dev_slices  = [
        ("Desktop", devices.get("desktop", 0), "#2563eb"),
        ("Mobile",  devices.get("mobile",  0), "#7c3aed"),
        ("Tablet",  devices.get("tablet",  0), "#0891b2"),
    ]

    # NvR
    nvr_map     = {}
    for r in data["nvr"]:
        nvr_map[r.get("newVsReturning", "other")] = int(r.get("sessions", 0))
    new_s = nvr_map.get("new", 0)
    ret_s = nvr_map.get("returning", 0)
    nvr_total = new_s + ret_s or 1

    # US cities
    us_cities = top_us_cities(data["cities"])

    # Charts
    svg_trend  = build_svg_chart(data["daily"])
    svg_device = build_donut(dev_slices)

    # Executive summary narrative
    trend_word  = "remained stable" if abs(pct_sess or 0) < 5 else ("grew" if (pct_sess or 0) > 0 else "decreased")
    organic_dir = "up" if (pct_org or 0) > 0 else "down"

    # Build HTML
    generated = datetime.now().strftime("%B %d, %Y")

    # --- KPI cards ---
    kpi_cards = f"""
<div class="kpi-grid">
  <div class="kpi-card">
    <div class="label">Total Visitors</div>
    <div class="value">{c_users:,}</div>
    <div class="change">{arrow(pct_users)} vs last month</div>
  </div>
  <div class="kpi-card">
    <div class="label">Total Sessions</div>
    <div class="value">{c_sessions:,}</div>
    <div class="change">{arrow(pct_sess)} vs last month</div>
  </div>
  <div class="kpi-card">
    <div class="label">Organic Search</div>
    <div class="value">{c_organic:,}</div>
    <div class="change">{arrow(pct_org)} vs last month</div>
  </div>
  <div class="kpi-card">
    <div class="label">Avg. Time on Site</div>
    <div class="value">{fmt_dur(c_dur)}</div>
    <div class="change">{arrow(pct_dur)} vs last month</div>
  </div>
</div>"""

    # --- Executive summary ---
    exec_box = f"""
<div class="exec-box">
  <h2>Executive Summary — {mon_str} {year}</h2>
  <p>
    Website traffic {trend_word} this month with <strong>{c_sessions:,} total sessions</strong> and
    <strong>{c_users:,} unique visitors</strong>. Organic search brought in
    <strong>{c_organic:,} sessions</strong>, {organic_dir} from {p_organic:,} last month.
    Visitors spent an average of <strong>{fmt_dur(c_dur)}</strong> on the site.
  </p>
  <p>
    The <strong>/switch/ page</strong> continued to attract high-intent traffic, confirming that
    prospective customers are actively evaluating a switch to Tierzero.
    The <strong>contact and support pages</strong> show strong engagement times, indicating
    visitors are finding the information they need.
  </p>
  <div class="exec-highlights">
    <div class="hl"><div class="hl-label">Visitors</div><div class="hl-val">{c_users:,}</div></div>
    <div class="hl"><div class="hl-label">Organic Sessions</div><div class="hl-val">{c_organic:,}</div></div>
    <div class="hl"><div class="hl-label">Pages Viewed</div><div class="hl-val">{c_views:,}</div></div>
    <div class="hl"><div class="hl-label">Engagement Rate</div><div class="hl-val">{fmt_pct(c_engage)}</div></div>
  </div>
</div>"""

    # --- Channel table ---
    ch_rows = ""
    for ch in channel_order:
        if ch not in ch_data and ch_data.get(ch, {}).get("current", 0) == 0:
            continue
        c_val = ch_data.get(ch, {}).get("current",  0)
        p_val = ch_data.get(ch, {}).get("previous", 0)
        if c_val == 0 and p_val == 0:
            continue
        pct   = pct_change(c_val, p_val)
        share = c_val / (c_sessions or 1) * 100
        pill_cls = channel_class.get(ch, "ch-other")
        ch_rows += f"""
    <tr>
      <td><span class="channel-pill {pill_cls}">{ch}</span></td>
      <td class="td-right">{c_val:,}</td>
      <td class="td-right">{p_val:,}</td>
      <td class="td-right">{arrow(pct)}</td>
      <td class="td-bar"><div class="bar-wrap"><div class="bar-fill" style="width:{share:.0f}%"></div></div></td>
    </tr>"""

    channel_section = f"""
<div class="section">
  <div class="section-title">Traffic by Channel</div>
  <table>
    <thead><tr>
      <th>Channel</th>
      <th class="td-right">{mon_str}</th>
      <th class="td-right">Prior Month</th>
      <th class="td-right">Change</th>
      <th class="td-bar">Share</th>
    </tr></thead>
    <tbody>{ch_rows}</tbody>
  </table>
</div>"""

    # --- Top pages ---
    max_page_sessions = max((int(p.get("sessions", 0)) for p in pages), default=1)
    page_rows = ""
    for p in pages:
        path  = p.get("pagePath", "")
        title = p.get("pageTitle", "")
        sess  = int(p.get("sessions", 0))
        views = int(p.get("screenPageViews", 0))
        dur   = float(p.get("averageSessionDuration", 0))
        share = sess / max_page_sessions * 100
        label = page_label(path, title)
        page_rows += f"""
    <tr>
      <td style="font-weight:500">{label}</td>
      <td style="color:#6b7280;font-size:12px">{path}</td>
      <td class="td-right">{sess:,}</td>
      <td class="td-right">{fmt_dur(dur)}</td>
      <td class="td-bar"><div class="bar-wrap"><div class="bar-fill" style="width:{share:.0f}%"></div></div></td>
    </tr>"""

    pages_section = f"""
<div class="section">
  <div class="section-title">Top Pages — {mon_str} {year}</div>
  <table>
    <thead><tr>
      <th>Page</th><th>URL</th>
      <th class="td-right">Sessions</th>
      <th class="td-right">Avg. Time</th>
      <th class="td-bar">Relative Traffic</th>
    </tr></thead>
    <tbody>{page_rows}</tbody>
  </table>
</div>"""

    # --- Trend chart ---
    trend_section = f"""
<div class="section">
  <div class="section-title">Daily Sessions — {mon_str} {year}</div>
  <div class="chart-box" style="padding:20px 24px">
    {svg_trend}
    <p style="font-size:11px;color:#9ca3af;margin-top:8px;text-align:center">Sessions per day · X axis = day of month</p>
  </div>
</div>"""

    # --- Audience ---
    city_rows_html = ""
    for r in us_cities:
        city_rows_html += f"""<tr>
      <td>{r.get("city", "—")}</td>
      <td class="td-right">{int(r.get("sessions",0)):,}</td>
    </tr>"""

    audience_section = f"""
<div class="section">
  <div class="section-title">Audience Breakdown</div>
  <div class="two-col">
    <div class="chart-box">
      <h4>Device Type</h4>
      <div style="display:flex;align-items:center;gap:16px">
        {svg_device}
      </div>
    </div>
    <div class="chart-box">
      <h4>Top US Locations</h4>
      <table style="border:none">
        <thead><tr><th>City</th><th class="td-right">Sessions</th></tr></thead>
        <tbody>{city_rows_html}</tbody>
      </table>
      <p style="font-size:11px;color:#9ca3af;margin-top:10px">
        New visitors: {new_s / nvr_total * 100:.0f}% &nbsp;·&nbsp; Returning: {ret_s / nvr_total * 100:.0f}%
      </p>
    </div>
  </div>
</div>"""

    # --- Recommendations ---
    recs = build_recommendations(data, c_sessions, p_sessions, c_organic, p_organic, c_bounce)
    rec_items = ""
    for i, (title, body) in enumerate(recs, 1):
        rec_items += f"""<li>
      <div class="rec-num">{i}</div>
      <div>
        <div class="rec-title">{title}</div>
        <div class="rec-body">{body}</div>
      </div>
    </li>"""

    recs_section = f"""
<div class="section">
  <div class="section-title">Recommendations</div>
  <div class="rec-wrap">
    <ul class="rec-list">{rec_items}</ul>
  </div>
</div>"""

    prev_mon_str = MONTH_NAMES[meta["month"] - 1] if meta["month"] > 1 else MONTH_NAMES[12]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{client_name} SEO Report — {mon_str} {year}</title>
  <style>{CSS}</style>
</head>
<body>
<div class="page">

  <div class="report-header">
    <div>
      <h1>{client_name}</h1>
      <div class="period">Monthly SEO &amp; Traffic Report &nbsp;·&nbsp; {mon_str} {year}</div>
    </div>
    <div class="logo">
      <strong>Medi-Edge Marketing</strong>
      Prepared {generated}
    </div>
  </div>

  {kpi_cards}
  {exec_box}
  {trend_section}
  {channel_section}
  {pages_section}
  {audience_section}
  {recs_section}

  <div class="report-footer">
    <span>Data source: Google Analytics 4 · Property {property_id}</span>
    <span>{mon_str} 1 – {monthrange(year, month)[1]}, {year} &nbsp;vs&nbsp; {prev_mon_str} (prior month)</span>
  </div>

</div>
</body>
</html>"""

    return html


def build_recommendations(data, c_sessions, p_sessions, c_organic, p_organic, c_bounce):
    """Generate data-driven recommendations."""
    recs = []

    # Organic search
    pct_org = pct_change(c_organic, p_organic)
    if pct_org is not None and pct_org < 0:
        recs.append((
            "Investigate Organic Search Drop",
            f"Organic search sessions declined {abs(pct_org):.1f}% versus last month. "
            "Review Google Search Console for any keyword ranking shifts, crawl issues, or content gaps. "
            "Prioritize landing pages targeting high-intent service keywords."
        ))
    elif c_organic < (c_sessions * 0.25):
        recs.append((
            "Grow Organic Search Traffic",
            f"Organic search accounts for {c_organic / (c_sessions or 1) * 100:.0f}% of total traffic. "
            "Expanding blog content targeting local business internet and VoIP keywords can increase this channel's contribution over the next 90 days."
        ))

    # Bounce rate
    if float(c_bounce) > 0.65:
        recs.append((
            "Improve Homepage Engagement",
            f"The current bounce rate of {float(c_bounce)*100:.0f}% is elevated. "
            "Consider A/B testing the homepage hero section — specifically the headline and primary CTA — "
            "to better qualify intent and direct visitors to the most relevant service page."
        ))

    # /switch/ page signal
    pages = clean_pages(data["pages"])
    switch_page = next((p for p in pages if "/switch/" in p.get("pagePath", "")), None)
    if switch_page and int(switch_page.get("sessions", 0)) > 100:
        recs.append((
            "Optimize the Switch Page for Conversions",
            f"The /switch/ page received {int(switch_page.get('sessions', 0)):,} sessions this month — "
            "strong signal of purchase intent. Ensure the page has a clear, frictionless CTA (quote request or direct contact form) "
            "and consider adding customer testimonials or case studies above the fold."
        ))

    # Contact page engagement
    contact_page = next((p for p in pages if "/contact/" in p.get("pagePath", "")), None)
    if contact_page and float(contact_page.get("averageSessionDuration", 0)) > 120:
        recs.append((
            "Reduce Friction on the Contact Page",
            "Visitors are spending significant time on the contact page, which may indicate form friction or confusion. "
            "Simplify the form to name, email, company, and one open-ended question — reduce it to the minimum needed to qualify the lead."
        ))

    # New visitor ratio
    nvr = {r.get("newVsReturning"): int(r.get("sessions", 0)) for r in data["nvr"]}
    new_s = nvr.get("new", 0)
    ret_s = nvr.get("returning", 0)
    if ret_s / (new_s + ret_s + 1) < 0.15:
        recs.append((
            "Build a Retargeting Strategy",
            f"Only {ret_s / (new_s + ret_s + 1) * 100:.0f}% of sessions are from returning visitors. "
            "A simple email capture (newsletter or free guide) combined with retargeting ads can bring back "
            "visitors who showed interest but didn't convert on the first visit."
        ))

    # Fallback
    if not recs:
        recs.append((
            "Continue Content Expansion",
            "Traffic is performing consistently. The next growth lever is expanding blog content targeting "
            "long-tail business internet and VoIP keywords — specifically comparison and 'best for' queries."
        ))

    return recs[:5]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate a monthly SEO report from GA4 data.")
    parser.add_argument("--property", required=True, help="GA4 Property ID (e.g. 514842555)")
    parser.add_argument("--month",    required=True, type=int, help="Report month (1-12)")
    parser.add_argument("--year",     required=True, type=int, help="Report year (e.g. 2026)")
    parser.add_argument("--client",   required=True, help="Client name (e.g. Tierzero)")
    parser.add_argument("--out",      default=None,  help="Output file path (default: auto)")
    args = parser.parse_args()

    load_env()

    print(f"Fetching GA4 data for property {args.property} …")
    token = get_access_token()
    data  = fetch_all(token, args.property, args.year, args.month)
    print("Data fetched. Generating report …")

    html = generate_html(data, args.client, args.property)

    out_file = args.out or f"report_{args.client.lower().replace(' ', '_')}_{args.month:02d}_{args.year}.html"
    with open(out_file, "w") as f:
        f.write(html)

    print(f"Report saved → {out_file}")
    print("Open in a browser and use File → Print → Save as PDF to export.")


if __name__ == "__main__":
    main()
