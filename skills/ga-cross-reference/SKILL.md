# GA Cross-Reference Skill

**Purpose:** Cross-reference Google Analytics measurement IDs across all client sites in our GitHub org against the GA properties we own — without needing local clones. Identifies wrong IDs, missing tracking, and IDs outside our GA access.

---

## When to use this

- Auditing all sites at once for GA health
- Onboarding a new client site where GA was already set up
- Suspecting a site is tracking to the wrong GA property
- Cleaning up sites with multiple commented-out GA IDs
- Verifying GA is pointed at our managed property (not the client's personal account)

---

## Step 1 — Pull GA IDs from ALL repos (no local clone needed)

Use the GitHub API to read `app/layout.tsx` from every repo in the org:

```bash
gh repo list medi-edge-marketing-com --limit 100 --json name -q '.[].name' | while read repo; do
  # Walk the tree to find app/layout.tsx
  APP_SHA=$(gh api repos/medi-edge-marketing-com/$repo/git/trees/HEAD --jq '.tree[] | select(.path == "app") | .sha' 2>/dev/null)
  [ -z "$APP_SHA" ] && continue
  FILE_SHA=$(gh api repos/medi-edge-marketing-com/$repo/git/trees/$APP_SHA --jq '.tree[] | select(.path == "layout.tsx") | .sha' 2>/dev/null)
  [ -z "$FILE_SHA" ] && continue
  IDS=$(gh api repos/medi-edge-marketing-com/$repo/git/blobs/$FILE_SHA --jq '.content' 2>/dev/null | base64 -d | grep -oP "G-[A-Z0-9]+" | sort -u | tr '\n' ',')
  echo "$repo | ${IDS%,}"
done
```

For local projects you already have cloned:
```bash
for f in ~/projects/*/app/layout.tsx; do
  site=$(echo $f | sed 's|.*/projects/||' | sed 's|/app/layout.tsx||')
  ids=$(grep -oP "G-[A-Z0-9]+" $f | tr '\n' ',' | sed 's/,$//')
  echo "$site | $ids"
done
```

---

## Step 2 — Get OAuth credentials

Read credentials from the contact server:

```bash
ssh mem-contact "cat ~/analytics-dashboard/.env" | grep -E "CLIENT_ID|CLIENT_SECRET|REFRESH_TOKEN"
```

You need: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`

---

## Step 3 — Get a fresh access token

```bash
ACCESS_TOKEN=$(curl -s -X POST "https://oauth2.googleapis.com/token" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "refresh_token=YOUR_REFRESH_TOKEN" \
  -d "grant_type=refresh_token" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

Tokens expire — always generate fresh per session.

---

## Step 4 — Dump all GA accounts

```bash
curl -s "https://analyticsadmin.googleapis.com/v1beta/accounts" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for a in data.get('accounts', []):
    print(a['name'], '|', a.get('displayName',''))
"
```

---

## Step 5 — Get all properties and measurement IDs in one pass

```bash
# Replace with actual account IDs from Step 4
ACCOUNT_IDS="111111111 222222222 ..."

for ACCT in $ACCOUNT_IDS; do
  curl -s "https://analyticsadmin.googleapis.com/v1beta/properties?filter=ancestor:accounts/$ACCT" \
    -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -c "
import sys, json
for p in json.load(sys.stdin).get('properties', []):
    print(p['name'])
" 2>/dev/null
done | while read PROP; do
  PROP_ID="${PROP#properties/}"
  curl -s "https://analyticsadmin.googleapis.com/v1beta/properties/$PROP_ID/dataStreams" \
    -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -c "
import sys, json
for s in json.load(sys.stdin).get('dataStreams', []):
    mid = s.get('webStreamData', {}).get('measurementId', '')
    if mid: print(f\"$PROP_ID | {s.get('displayName','')} | {mid}\")
" 2>/dev/null
done
```

Output: `PROPERTY_ID | Property Display Name | G-XXXXXXX`

---

## Step 6 — Cross-reference and classify

Compare the measurement IDs from Step 1 against the IDs from Step 5:

| Situation | Classification |
|---|---|
| ID in code matches a GA property we own | ✅ Clean — we manage the property |
| ID in code not found in our API results | ✅ Normal — client owns their GA account, we're added as users. Admin API only returns accounts we *own*, not ones where we have user access. Tracking is correct. |
| Placeholder like `G-XXXXXXXXXX` or `G-FISHSHOP123` | ❌ Fake — no tracking at all |
| No GA tag in layout.tsx | ❌ Missing — site has zero tracking |
| Same ID used on 2+ sites | ⚠️ Shared — check if intentional (same client) |
| GA property name doesn't match site domain | ⚠️ Name mismatch — tracking likely works but may be confusing in reports |

**Important:** The GA Admin API only returns properties where *we are the account owner*. Client-owned accounts where we're added as a viewer/editor will not appear in API results — this is expected and does not mean the tracking is wrong.

---

## Step 7 — Fix and deploy

To fix a wrong/missing ID in `layout.tsx`:

```tsx
{/* Google Analytics (GA4) */}
<Script
  src="https://www.googletagmanager.com/gtag/js?id=G-CORRECT_ID"
  strategy="afterInteractive"
/>
<Script id="google-analytics" strategy="afterInteractive">
  {`
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-CORRECT_ID');
  `}
</Script>
```

Deploy:
```bash
yes | ~/projects/mem-deploy/bin/push --live --server main-1 -m "fix GA measurement ID to G-CORRECT_ID" clientdomain.com
```

---

## Our GA Org Accounts (as of April 2026)

| Account ID | Display Name | Measurement ID | Site/Project |
|---|---|---|---|
| 132223467 | Tierzero | G-68PLD9CE4W | tierzero.com (GA4 property) |
| 329257397 | Mediedge Marketing | G-R7GWZMF1L5 | mediedgemarketing.com |
| 362189600 | garagelabusa.com | G-WQJDQ2R0C2 | garagelabusa.com |
| 365838418 | littlemissmedspa.com | G-K4331MGYNG | littlemissmedspa.com |
| 366882879 | santafesoul.com | G-W8CD2R4JRN | santafesoul.com |
| 366937873 | codenverdentist.com | G-FP5CWKB0ES | codenverdentist.com |
| 368353751 | nursingpnp.com | G-6LYPYV2E0W | nursingpnp.com / aestheticpnp.com |
| 375192201 | socalskinmedspa.com | G-YFB7XC4XK0 | socalskinaesthetics.com |
| 376444432 | tierzero.com | G-54N09LP3JR | tierzero.com |
| 382737202 | ccaesthetics.net | G-R6JFM1N6NH | ccaesthetics.net |
| 383251866 | empirechiropractic.com | G-MEQD6EX789 | (duplicate — not in use) |
| 384005829 | empirechiropractic.com | G-JLMC134CEK | empirechiropractic.com ✅ |
| 385140241 | vipaestheticsla.com | G-J766858ZYF | vipaestheticsla.com |
| 385365333 | faceitaesthetics.net | G-44P81Y590H | faceitaesthetics.com |
| 385777249 | owossodental.com | G-WX1WNGGJMS | owossodental.com + owossodentalcenter.com |
| 386855283 | aestheticnursingces.com | G-8JC567141R | aestheticnursingces.com + course.nursingpnp.com |
| 387611557 | destinationregenerate.com | G-M8Q8NN7GX3 | destinationregenerate.com |
| 387662258 | rekindlesexualhealth.com | G-DYPVBF90WE | rekindlesexualhealth.com |
| 388979440 | ohiofootandanklecare.com | G-CP498340TP | BendsFootandAnkle project |
| 493862149 (nested) | drrobertgonzalezdc.com | G-KD0P038XQM | drrobertgonzalezdc.com + aestehticnp.com |
| 490141923 (nested) | origin.health | G-V2RK56N6HJ | origin.health |

*Note: Several IDs appear under account 329257397 (Mediedge Marketing) as nested properties — including SoCal Skin (G-BNDZJVG60R, G-N24RN5HFWN), Christine Ngwazini/Del Mar Injector (G-S90CVQ0Z88, G-TTM1B6NTJB), and Cbooth Innovations (G-BP3VV780DK, G-1ZSP7792WR).*

---

## Known Issues (April 2026)

| Site | ID | Issue |
|---|---|---|
| thefishshops.com | G-FISHSHOP123 | Placeholder — no real tracking |

**Sites tracking to client-owned GA (we're added as users — normal):**
7systems-drhaas.com (G-7FD1C9J56J), n2perio.com (G-0NFL7DVFVW), ricksraingutterservices.com (G-PNZ8Z7FVBG), tierzero.com
