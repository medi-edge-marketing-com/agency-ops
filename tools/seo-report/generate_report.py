#!/usr/bin/env python3
"""
SEO Monthly Report Generator
Pulls GA4 data and generates a clean, accurate HTML report.

IMPORTANT: This script only reports what the data literally says.
No interpretation, no recommendations, no narrative speculation.
The account manager adds context manually — this tool delivers the numbers.

Usage:
  python generate_report.py --property 514842555 --month 3 --year 2026 --client "Tierzero"

Credentials — set as environment variables or place in .env file:
  GOOGLE_CLIENT_ID
  GOOGLE_CLIENT_SECRET
  GOOGLE_REFRESH_TOKEN

Output: report_<client>_<month>_<year>.html  (open in browser, Ctrl+P → Save as PDF)
"""

import json
import os
import sys
import argparse
import urllib.request
import urllib.parse
from datetime import datetime
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
    payload = urllib.parse.urlencode({
        "client_id":     os.environ["GOOGLE_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_REFRESH_TOKEN"],
        "grant_type":    "refresh_token",
    }).encode()
    req  = urllib.request.Request("https://oauth2.googleapis.com/token", data=payload)
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())["access_token"]


# ---------------------------------------------------------------------------
# GA4
# ---------------------------------------------------------------------------

def ga4_report(token, prop, body):
    url  = f"https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport"
    data = json.dumps(body).encode()
    req  = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
    })
    return json.loads(urllib.request.urlopen(req).read())


def rows(result):
    dh = [h["name"] for h in result.get("dimensionHeaders", [])]
    mh = [h["name"] for h in result.get("metricHeaders",   [])]
    out = []
    for r in result.get("rows", []):
        row = {}
        for i, h in enumerate(dh): row[h] = r["dimensionValues"][i]["value"]
        for i, h in enumerate(mh): row[h] = r["metricValues"][i]["value"]
        out.append(row)
    return out


# ---------------------------------------------------------------------------
# Data fetch
# ---------------------------------------------------------------------------

def fetch(token, prop, year, month):
    _, last   = monthrange(year, month)
    t_start   = f"{year}-{month:02d}-01"
    t_end     = f"{year}-{month:02d}-{last:02d}"
    pm        = month - 1 if month > 1 else 12
    py        = year if month > 1 else year - 1
    _, plast  = monthrange(py, pm)
    p_start   = f"{py}-{pm:02d}-01"
    p_end     = f"{py}-{pm:02d}-{plast:02d}"

    dr = [
        {"startDate": t_start, "endDate": t_end,  "name": "current"},
        {"startDate": p_start, "endDate": p_end,  "name": "previous"},
    ]

    totals = rows(ga4_report(token, prop, {
        "dateRanges": dr,
        "metrics": [
            {"name": "sessions"}, {"name": "totalUsers"},
            {"name": "screenPageViews"}, {"name": "averageSessionDuration"},
            {"name": "engagementRate"}, {"name": "bounceRate"},
        ],
    }))

    channels = rows(ga4_report(token, prop, {
        "dateRanges": dr,
        "metrics": [{"name": "sessions"}, {"name": "totalUsers"}],
        "dimensions": [{"name": "sessionDefaultChannelGroup"}],
    }))

    pages = rows(ga4_report(token, prop, {
        "dateRanges": [{"startDate": t_start, "endDate": t_end}],
        "metrics": [
            {"name": "sessions"}, {"name": "screenPageViews"},
            {"name": "averageSessionDuration"},
        ],
        "dimensions": [{"name": "pagePath"}, {"name": "pageTitle"}],
        "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}],
        "limit": 20,
    }))

    daily = rows(ga4_report(token, prop, {
        "dateRanges": [{"startDate": t_start, "endDate": t_end}],
        "metrics": [{"name": "sessions"}],
        "dimensions": [{"name": "date"}],
        "orderBys": [{"dimension": {"dimensionName": "date"}}],
    }))

    devices = rows(ga4_report(token, prop, {
        "dateRanges": [{"startDate": t_start, "endDate": t_end}],
        "metrics": [{"name": "sessions"}],
        "dimensions": [{"name": "deviceCategory"}],
    }))

    cities = rows(ga4_report(token, prop, {
        "dateRanges": [{"startDate": t_start, "endDate": t_end}],
        "metrics": [{"name": "sessions"}],
        "dimensions": [{"name": "country"}, {"name": "city"}],
        "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}],
        "limit": 40,
    }))

    nvr = rows(ga4_report(token, prop, {
        "dateRanges": [{"startDate": t_start, "endDate": t_end}],
        "metrics": [{"name": "sessions"}],
        "dimensions": [{"name": "newVsReturning"}],
    }))

    return {
        "totals": totals, "channels": channels, "pages": pages,
        "daily": daily, "devices": devices, "cities": cities, "nvr": nvr,
        "meta": {
            "year": year, "month": month, "last_day": last,
            "t_start": t_start, "t_end": t_end,
            "p_start": p_start, "p_end": p_end,
            "prev_month": pm, "prev_year": py,
        },
    }


# ---------------------------------------------------------------------------
# Number helpers — pure math, no narrative
# ---------------------------------------------------------------------------

def pct_change(new_val, old_val):
    n, o = float(new_val), float(old_val)
    if o == 0:
        return None
    return ((n - o) / o) * 100


def fmt_pct_change(pct, invert=False):
    """Return a plain +X.X% / -X.X% string with color class. invert=True means lower is better."""
    if pct is None:
        return '<span class="neutral">—</span>'
    better = pct > 0 if not invert else pct < 0
    cls    = "positive" if better else ("negative" if not better else "neutral")
    sign   = "+" if pct > 0 else ""
    return f'<span class="{cls}">{sign}{pct:.1f}%</span>'


def fmt_dur(seconds):
    s = float(seconds)
    m = int(s // 60)
    r = int(s % 60)
    return f"{m}m {r:02d}s" if m else f"{r}s"


def fmt_rate(v):
    return f"{float(v) * 100:.1f}%"


def get_period(data_rows, period):
    for r in data_rows:
        if r.get("dateRange") == period:
            return r
    return {}


def get_channel_sessions(channel_rows, period, channel):
    for r in channel_rows:
        if r.get("dateRange") == period and r.get("sessionDefaultChannelGroup") == channel:
            return int(r.get("sessions", 0))
    return 0


def us_cities(city_rows, n=6):
    seen = set()
    out  = []
    for r in city_rows:
        if r.get("country") != "United States":
            continue
        city = r.get("city", "")
        if not city or city in ("(not set)", "") or city in seen:
            continue
        seen.add(city)
        out.append(r)
        if len(out) >= n:
            break
    return out


def filter_pages(page_rows):
    """Remove pages that are clearly not content (privacy, legal, robots, etc.)."""
    noise = {"/privacy/", "/legal/", "/robots.txt", "/sitemap.xml", "/favicon.ico"}
    out = []
    for r in page_rows:
        path = r.get("pagePath", "")
        if path in noise:
            continue
        out.append(r)
    return out[:10]


PAGE_LABELS = {
    "/":                    "Homepage",
    "/switch/":             "Switch to Tierzero",
    "/contact/":            "Contact",
    "/about/":              "About Us",
    "/blog/":               "Blog",
    "/services/internet/":  "Internet Services",
    "/services/voice/":     "Voice Services",
    "/support/":            "Support",
    "/pricing/":            "Pricing",
}

def page_label(path):
    if path in PAGE_LABELS:
        return PAGE_LABELS[path]
    clean = path.strip("/").replace("-", " ").replace("/", " › ").title()
    return clean or path


# ---------------------------------------------------------------------------
# SVG trend chart — daily sessions
# ---------------------------------------------------------------------------

def svg_trend_chart(daily_rows):
    if not daily_rows:
        return "<p style='color:#9ca3af;font-size:12px'>No data</p>"

    values = [int(r.get("sessions", 0)) for r in daily_rows]
    labels = [r.get("date", "") for r in daily_rows]
    n      = len(values)
    max_v  = max(values) if values else 1

    W, H   = 820, 180
    pl, pr, pt, pb = 40, 16, 16, 28
    iw = W - pl - pr
    ih = H - pt - pb

    def cx(i):
        return pl + (i / max(n - 1, 1)) * iw

    def cy(v):
        return pt + ih - (v / max_v) * ih

    pts  = " ".join(f"{cx(i):.1f},{cy(v):.1f}" for i, v in enumerate(values))
    area = (
        f"M {cx(0):.1f},{cy(values[0]):.1f} "
        + " ".join(f"L {cx(i):.1f},{cy(v):.1f}" for i, v in enumerate(values))
        + f" L {cx(n-1):.1f},{pt+ih} L {cx(0):.1f},{pt+ih} Z"
    )

    # Y grid
    grid = ""
    for gv in [0, max_v // 2, max_v]:
        gy = cy(gv)
        grid += (f'<line x1="{pl}" y1="{gy:.1f}" x2="{W-pr}" y2="{gy:.1f}" '
                 f'stroke="#f0f0f0" stroke-width="1"/>'
                 f'<text x="{pl-5}" y="{gy+4:.1f}" text-anchor="end" '
                 f'font-size="10" fill="#aaa">{gv}</text>')

    # X labels — show ~7 evenly spaced
    step   = max(1, n // 7)
    xlbls  = ""
    for i in range(0, n, step):
        day = int(labels[i][6:8])
        xlbls += (f'<text x="{cx(i):.1f}" y="{pt+ih+18}" text-anchor="middle" '
                  f'font-size="10" fill="#aaa">{day}</text>')

    # Peak marker
    peak_i = values.index(max_v)
    peak   = (f'<circle cx="{cx(peak_i):.1f}" cy="{cy(max_v):.1f}" r="4" fill="#2563eb" stroke="#fff" stroke-width="1.5"/>'
              f'<text x="{cx(peak_i):.1f}" y="{cy(max_v)-8:.1f}" text-anchor="middle" '
              f'font-size="10" fill="#2563eb" font-weight="700">{max_v}</text>')

    return f'''<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg"
     style="width:100%;height:auto;display:block;overflow:visible">
  <defs>
    <linearGradient id="ag" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#2563eb" stop-opacity="0.12"/>
      <stop offset="100%" stop-color="#2563eb" stop-opacity="0.01"/>
    </linearGradient>
  </defs>
  {grid}
  <path d="{area}" fill="url(#ag)"/>
  <polyline points="{pts}" fill="none" stroke="#2563eb" stroke-width="2"
    stroke-linejoin="round" stroke-linecap="round"/>
  {peak}
  {xlbls}
  <line x1="{pl}" y1="{pt}" x2="{pl}" y2="{pt+ih}" stroke="#e5e7eb" stroke-width="1"/>
  <line x1="{pl}" y1="{pt+ih}" x2="{W-pr}" y2="{pt+ih}" stroke="#e5e7eb" stroke-width="1"/>
</svg>'''


# ---------------------------------------------------------------------------
# CSS bar chart for devices — more reliable than SVG donut
# ---------------------------------------------------------------------------

def device_bars(device_rows):
    d = {r["deviceCategory"]: int(r["sessions"]) for r in device_rows}
    total = sum(d.values()) or 1
    order = [("desktop", "Desktop", "#2563eb"), ("mobile", "Mobile", "#7c3aed"), ("tablet", "Tablet", "#0891b2")]
    html  = '<div style="display:flex;flex-direction:column;gap:10px;margin-top:4px">'
    for key, label, color in order:
        val = d.get(key, 0)
        pct = val / total * 100
        html += f'''
        <div>
          <div style="display:flex;justify-content:space-between;font-size:12px;color:#374151;margin-bottom:4px">
            <span>{label}</span>
            <span style="font-weight:600">{val:,} &nbsp;<span style="color:#6b7280;font-weight:400">({pct:.0f}%)</span></span>
          </div>
          <div style="background:#f3f4f6;border-radius:4px;height:8px;overflow:hidden">
            <div style="width:{pct:.1f}%;height:8px;background:{color};border-radius:4px"></div>
          </div>
        </div>'''
    html += "</div>"
    return html


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

MONTHS = ["", "January", "February", "March", "April", "May", "June",
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

.report-header {
  display: flex; justify-content: space-between; align-items: flex-end;
  margin-bottom: 28px; padding-bottom: 20px; border-bottom: 2px solid #e5e7eb;
}
.report-header h1 { font-size: 22px; font-weight: 700; }
.report-header .sub { font-size: 13px; color: #6b7280; margin-top: 3px; }
.report-header .meta { font-size: 12px; color: #6b7280; text-align: right; }
.report-header .meta strong { display: block; font-size: 14px; color: #111827; font-weight: 700; }

.kpi-grid {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 12px; margin-bottom: 28px;
}
.kpi {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 10px;
  padding: 16px 14px;
}
.kpi .k-label { font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .07em; color: #6b7280; margin-bottom: 6px; }
.kpi .k-val   { font-size: 24px; font-weight: 700; line-height: 1; color: #111827; }
.kpi .k-sub   { font-size: 11px; color: #6b7280; margin-top: 5px; }
.positive { color: #16a34a; font-weight: 600; }
.negative { color: #dc2626; font-weight: 600; }
.neutral  { color: #6b7280; }

.section { margin-bottom: 32px; }
.section-label {
  font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: .08em;
  color: #6b7280; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #e5e7eb;
}

.card {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 20px 22px;
}
.card h4 { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .07em; color: #6b7280; margin-bottom: 14px; }

table { width: 100%; border-collapse: collapse; }
.table-wrap { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; overflow: hidden; }
thead tr { background: #f9fafb; }
th {
  text-align: left; padding: 9px 14px; font-size: 10px; font-weight: 700;
  color: #6b7280; text-transform: uppercase; letter-spacing: .07em;
  border-bottom: 1px solid #e5e7eb;
}
td { padding: 10px 14px; font-size: 13px; color: #374151; border-bottom: 1px solid #f3f4f6; }
tr:last-child td { border-bottom: none; }
.tr { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.bar-cell { width: 90px; }
.bar-bg { background: #f3f4f6; border-radius: 3px; height: 5px; overflow: hidden; }
.bar-fg { height: 5px; border-radius: 3px; background: #2563eb; }

.pill {
  display: inline-block; padding: 2px 8px; border-radius: 99px;
  font-size: 11px; font-weight: 600;
}
.pill-direct   { background: #eff6ff; color: #1d4ed8; }
.pill-organic  { background: #f0fdf4; color: #15803d; }
.pill-email    { background: #fff7ed; color: #c2410c; }
.pill-referral { background: #fdf4ff; color: #7e22ce; }
.pill-social   { background: #fef9c3; color: #854d0e; }
.pill-paid     { background: #fff1f2; color: #be123c; }
.pill-other    { background: #f3f4f6; color: #374151; }

.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

.notes-box {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 10px;
  padding: 20px 22px; min-height: 100px;
}
.notes-box .notes-hint { font-size: 12px; color: #d1d5db; font-style: italic; }

.footer {
  margin-top: 48px; padding-top: 14px; border-top: 1px solid #e5e7eb;
  font-size: 11px; color: #9ca3af; display: flex; justify-content: space-between;
}

@media print {
  body { background: #fff; }
  .page { padding: 16px; max-width: 100%; }
  .kpi, .card, .table-wrap { break-inside: avoid; }
}
"""


def generate_html(data, client_name, property_id):
    meta       = data["meta"]
    year       = meta["year"]
    month      = meta["month"]
    prev_month = meta["prev_month"]
    mon_str    = MONTHS[month]
    prev_str   = MONTHS[prev_month]
    generated  = datetime.now().strftime("%B %d, %Y")

    # --- Totals ---
    curr = get_period(data["totals"], "current")
    prev = get_period(data["totals"], "previous")

    c_sess  = int(curr.get("sessions", 0))
    p_sess  = int(prev.get("sessions", 0))
    c_users = int(curr.get("totalUsers", 0))
    p_users = int(prev.get("totalUsers", 0))
    c_views = int(curr.get("screenPageViews", 0))
    p_views = int(prev.get("screenPageViews", 0))
    c_dur   = float(curr.get("averageSessionDuration", 0))
    p_dur   = float(prev.get("averageSessionDuration", 0))
    c_eng   = float(curr.get("engagementRate", 0))
    p_eng   = float(prev.get("engagementRate", 0))
    c_bnc   = float(curr.get("bounceRate", 0))
    p_bnc   = float(prev.get("bounceRate", 0))

    c_org = get_channel_sessions(data["channels"], "current",  "Organic Search")
    p_org = get_channel_sessions(data["channels"], "previous", "Organic Search")

    # --- KPI cards ---
    kpis = f"""
<div class="kpi-grid">
  <div class="kpi">
    <div class="k-label">Total Visitors</div>
    <div class="k-val">{c_users:,}</div>
    <div class="k-sub">{fmt_pct_change(pct_change(c_users, p_users))} vs {prev_str} ({p_users:,})</div>
  </div>
  <div class="kpi">
    <div class="k-label">Sessions</div>
    <div class="k-val">{c_sess:,}</div>
    <div class="k-sub">{fmt_pct_change(pct_change(c_sess, p_sess))} vs {prev_str} ({p_sess:,})</div>
  </div>
  <div class="kpi">
    <div class="k-label">Organic Search Sessions</div>
    <div class="k-val">{c_org:,}</div>
    <div class="k-sub">{fmt_pct_change(pct_change(c_org, p_org))} vs {prev_str} ({p_org:,})</div>
  </div>
  <div class="kpi">
    <div class="k-label">Avg. Session Duration</div>
    <div class="k-val">{fmt_dur(c_dur)}</div>
    <div class="k-sub">{fmt_pct_change(pct_change(c_dur, p_dur))} vs {prev_str} ({fmt_dur(p_dur)})</div>
  </div>
</div>"""

    # --- Summary table (pure numbers, no narrative) ---
    def row(label, curr_val, prev_val, fmt_fn=lambda x: f"{int(x):,}", invert=False):
        pct = pct_change(float(curr_val), float(prev_val))
        return f"""<tr>
      <td>{label}</td>
      <td class="tr">{fmt_fn(curr_val)}</td>
      <td class="tr">{fmt_fn(prev_val)}</td>
      <td class="tr">{fmt_pct_change(pct, invert=invert)}</td>
    </tr>"""

    summary_rows = (
        row("Sessions",                c_sess,  p_sess)
        + row("Unique Visitors",       c_users, p_users)
        + row("Page Views",            c_views, p_views)
        + row("Avg. Session Duration", c_dur,   p_dur,   fmt_fn=fmt_dur)
        + row("Engagement Rate",       c_eng,   p_eng,   fmt_fn=fmt_rate)
        + row("Bounce Rate",           c_bnc,   p_bnc,   fmt_fn=fmt_rate, invert=True)
        + row("Organic Search Sessions", c_org, p_org)
    )

    summary_section = f"""
<div class="section">
  <div class="section-label">Traffic Summary — {mon_str} {year} vs {prev_str}</div>
  <div class="table-wrap">
    <table>
      <thead><tr>
        <th>Metric</th>
        <th class="tr">{mon_str}</th>
        <th class="tr">{prev_str}</th>
        <th class="tr">Change</th>
      </tr></thead>
      <tbody>{summary_rows}</tbody>
    </table>
  </div>
</div>"""

    # --- Trend chart ---
    trend_section = f"""
<div class="section">
  <div class="section-label">Daily Sessions — {mon_str} {year}</div>
  <div class="card" style="padding:16px 20px">
    {svg_trend_chart(data["daily"])}
    <p style="font-size:11px;color:#9ca3af;margin-top:6px;text-align:center">Sessions per day · X axis = day of month</p>
  </div>
</div>"""

    # --- Channel breakdown ---
    ch_order = [
        ("Direct",         "pill-direct"),
        ("Organic Search", "pill-organic"),
        ("Email",          "pill-email"),
        ("Referral",       "pill-referral"),
        ("Organic Social", "pill-social"),
        ("Paid Search",    "pill-paid"),
    ]
    ch_map = {}
    for r in data["channels"]:
        ch  = r.get("sessionDefaultChannelGroup", "Other")
        prd = r.get("dateRange", "")
        if ch not in ch_map: ch_map[ch] = {"current": 0, "previous": 0}
        ch_map[ch][prd] = int(r.get("sessions", 0))

    ch_rows_html = ""
    for ch, pill_cls in ch_order:
        c_val = ch_map.get(ch, {}).get("current",  0)
        p_val = ch_map.get(ch, {}).get("previous", 0)
        if c_val == 0 and p_val == 0:
            continue
        pct   = pct_change(c_val, p_val)
        share = c_val / (c_sess or 1) * 100
        ch_rows_html += f"""<tr>
      <td><span class="pill {pill_cls}">{ch}</span></td>
      <td class="tr">{c_val:,}</td>
      <td class="tr">{p_val:,}</td>
      <td class="tr">{fmt_pct_change(pct)}</td>
      <td class="bar-cell"><div class="bar-bg"><div class="bar-fg" style="width:{share:.1f}%"></div></div></td>
    </tr>"""

    channel_section = f"""
<div class="section">
  <div class="section-label">Sessions by Channel</div>
  <div class="table-wrap">
    <table>
      <thead><tr>
        <th>Channel</th>
        <th class="tr">{mon_str}</th>
        <th class="tr">{prev_str}</th>
        <th class="tr">Change</th>
        <th class="bar-cell">Share</th>
      </tr></thead>
      <tbody>{ch_rows_html}</tbody>
    </table>
  </div>
</div>"""

    # --- Top pages ---
    pages   = filter_pages(data["pages"])
    max_s   = max((int(p.get("sessions", 0)) for p in pages), default=1)
    pg_rows = ""
    for p in pages:
        path  = p.get("pagePath", "")
        sess  = int(p.get("sessions", 0))
        views = int(p.get("screenPageViews", 0))
        dur   = float(p.get("averageSessionDuration", 0))
        share = sess / max_s * 100
        pg_rows += f"""<tr>
      <td style="font-weight:500">{page_label(path)}</td>
      <td style="color:#9ca3af;font-size:11px">{path}</td>
      <td class="tr">{sess:,}</td>
      <td class="tr">{views:,}</td>
      <td class="tr">{fmt_dur(dur)}</td>
      <td class="bar-cell"><div class="bar-bg"><div class="bar-fg" style="width:{share:.1f}%"></div></div></td>
    </tr>"""

    pages_section = f"""
<div class="section">
  <div class="section-label">Top Pages — {mon_str} {year}</div>
  <div class="table-wrap">
    <table>
      <thead><tr>
        <th>Page</th><th>Path</th>
        <th class="tr">Sessions</th>
        <th class="tr">Views</th>
        <th class="tr">Avg. Time</th>
        <th class="bar-cell">Relative</th>
      </tr></thead>
      <tbody>{pg_rows}</tbody>
    </table>
  </div>
</div>"""

    # --- Audience ---
    nvr_map = {}
    for r in data["nvr"]:
        nvr_map[r.get("newVsReturning", "other")] = int(r.get("sessions", 0))
    new_s = nvr_map.get("new",       0)
    ret_s = nvr_map.get("returning", 0)
    nvr_t = new_s + ret_s or 1

    city_rows_html = ""
    for r in us_cities(data["cities"]):
        city_rows_html += f"""<tr>
      <td>{r.get("city", "—")}</td>
      <td class="tr">{int(r.get("sessions", 0)):,}</td>
    </tr>"""

    audience_section = f"""
<div class="section">
  <div class="section-label">Audience</div>
  <div class="two-col">
    <div class="card">
      <h4>Device Type</h4>
      {device_bars(data["devices"])}
    </div>
    <div class="card">
      <h4>Top US Cities</h4>
      <table>
        <thead><tr><th>City</th><th class="tr">Sessions</th></tr></thead>
        <tbody>{city_rows_html}</tbody>
      </table>
      <p style="font-size:11px;color:#9ca3af;margin-top:12px">
        New visitors: <strong>{new_s / nvr_t * 100:.0f}%</strong> &nbsp;·&nbsp;
        Returning: <strong>{ret_s / nvr_t * 100:.0f}%</strong>
      </p>
    </div>
  </div>
</div>"""

    # --- Notes (blank — account manager fills in manually) ---
    notes_section = f"""
<div class="section">
  <div class="section-label">Account Manager Notes</div>
  <div class="notes-box">
    <p class="notes-hint">[ Add notes, context, and action items here before sending to client ]</p>
  </div>
</div>"""

    _, last_day = monthrange(year, month)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{client_name} — SEO Report {mon_str} {year}</title>
  <style>{CSS}</style>
</head>
<body>
<div class="page">

  <div class="report-header">
    <div>
      <h1>{client_name}</h1>
      <div class="sub">Monthly Traffic Report &nbsp;·&nbsp; {mon_str} {year}</div>
    </div>
    <div class="meta">
      <strong>Medi-Edge Marketing</strong>
      Prepared {generated}
    </div>
  </div>

  {kpis}
  {summary_section}
  {trend_section}
  {channel_section}
  {pages_section}
  {audience_section}
  {notes_section}

  <div class="footer">
    <span>Source: Google Analytics 4 · Property {property_id}</span>
    <span>{mon_str} 1–{last_day}, {year} &nbsp;vs&nbsp; {prev_str} (prior month)</span>
  </div>

</div>
</body>
</html>"""

    return html


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--property", required=True)
    parser.add_argument("--month",    required=True, type=int)
    parser.add_argument("--year",     required=True, type=int)
    parser.add_argument("--client",   required=True)
    parser.add_argument("--out",      default=None)
    args = parser.parse_args()

    load_env()

    print(f"Fetching GA4 data for property {args.property} …")
    token = get_access_token()
    data  = fetch(token, args.property, args.year, args.month)
    print("Generating report …")

    html = generate_html(data, args.client, args.property)

    out  = args.out or f"report_{args.client.lower().replace(' ','_')}_{args.month:02d}_{args.year}.html"
    with open(out, "w") as f:
        f.write(html)

    print(f"Saved → {out}")
    print("Open in browser · Ctrl+P → Save as PDF to export.")


if __name__ == "__main__":
    main()
