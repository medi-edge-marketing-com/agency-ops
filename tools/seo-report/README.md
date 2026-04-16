# SEO Report Generator

Generates a clean, client-ready monthly SEO report as a self-contained HTML file.  
Open in any browser → File → Print → Save as PDF to deliver to the client.

## What it pulls

- Total visitors, sessions, page views, avg. time on site — month vs. prior month
- Traffic by channel (organic, direct, email, referral, social)
- Top pages with sessions and time-on-page
- Daily sessions trend chart (inline SVG — no dependencies)
- Device breakdown donut chart
- Top US locations
- New vs. returning visitor ratio
- Data-driven recommendations based on the actual numbers

Data source: Google Analytics 4 (GA4 Data API).

## Setup

Credentials go in a `.env` file in this directory or as environment variables:

```
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REFRESH_TOKEN=...
```

**Where to find creds:** `ssh mem-contact` → `cat ~/analytics-dashboard/.env`

## Usage

```bash
python3 generate_report.py \
  --property 514842555 \
  --month 3 \
  --year 2026 \
  --client "Tierzero"
```

Output: `report_tierzero_03_2026.html`

## GA4 Property IDs

| Client | Property ID |
|---|---|
| Tierzero | 514842555 |
| Mediedge Marketing | 458803830 |
| garagelabusa.com | 497662116 |
| santafesoul.com | 503242676 |
| codenverdentist.com | 503303381 |
| nursingpnp.com | 505011234 |
| ccaesthetics.net | 522501483 |
| empirechiropractic.com | 524002220 |
| vipaestheticsla.com | 525403863 |
| faceitaesthetics.com | 525694075 |
| owossodental.com | 526187270 |
| aestheticnursingces.com | 527557241 |
| destinationregenerate.com | 528381823 |
| rekindlesexualhealth.com | 528466003 |
| ohiofootandanklecare.com | 530116547 |

*For client-owned accounts (where we're added as users), use the property ID from their GA account.*

## Notes

- Google Search Console data requires additional OAuth scopes — not currently included
- Filters out obvious bot/spam traffic from top pages (sub-5s session pages like /privacy/, /legal/)
- Cities filtered to US only — Singapore/Lanzhou traffic flagged internally as likely bot traffic
- Recommendations are generated automatically based on the data (not hardcoded)
