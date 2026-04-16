# GA Cross-Reference Skill

**Purpose:** Cross-reference the Google Analytics measurement ID hardcoded in a client site's `layout.tsx` against the GA properties we actually own in our Analytics account — to confirm the right ID is active.

---

## When to use this

- Onboarding a new client site where GA was already set up
- Suspecting a site is tracking to the wrong GA property
- Cleaning up a site with multiple commented-out GA IDs
- Verifying GA is pointed at our managed property (not the client's personal account)

---

## Step 1 — Find the GA ID in the site

Look in the site's `app/layout.tsx` (Next.js) for the Google Analytics script block:

```tsx
<Script src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXX" ... />
<Script id="google-analytics" ...>
  {`gtag('config', 'G-XXXXXXX');`}
</Script>
```

Note the measurement ID(s) — including any commented-out ones.

---

## Step 2 — Get OAuth credentials

SSH into the contact server and read the analytics dashboard env file:

```bash
ssh mem-contact
cat ~/analytics-dashboard/.env
```

You need three values:
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`

---

## Step 3 — Get an access token

```bash
ACCESS_TOKEN=$(curl -s -X POST "https://oauth2.googleapis.com/token" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "refresh_token=YOUR_REFRESH_TOKEN" \
  -d "grant_type=refresh_token" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

---

## Step 4 — List all GA accounts

```bash
curl -s "https://analyticsadmin.googleapis.com/v1beta/accounts" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
```

Look for accounts whose `displayName` matches the client's domain (e.g. `empirechiropractic.com`). Note the account `name` field — format is `accounts/XXXXXXXXX`.

---

## Step 5 — Get properties under each matching account

```bash
curl -s "https://analyticsadmin.googleapis.com/v1beta/properties?filter=ancestor:accounts/XXXXXXXXX" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
```

Note the property `name` field — format is `properties/XXXXXXXXX`.

---

## Step 6 — Get measurement IDs from data streams

```bash
curl -s "https://analyticsadmin.googleapis.com/v1beta/properties/XXXXXXXXX/dataStreams" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
```

Look for `webStreamData.measurementId` — this is the `G-XXXXXXX` ID.

---

## Step 7 — Compare and fix

| ID in layout.tsx | Found in our GA accounts? | Action |
|---|---|---|
| Active ID | Yes | Correct, leave it |
| Active ID | No | Wrong — swap to the verified one |
| Commented-out ID | Yes | This is the right one — activate it |
| Commented-out ID | No | Can remove it |

To fix in `layout.tsx`, update both the `src` on the `<Script>` tag and the `gtag('config', ...)` call to the verified measurement ID, then deploy.

---

## Step 8 — Deploy

```bash
yes | ~/projects/mem-deploy/bin/push --live --server main-1 -m "fix GA measurement ID to G-XXXXXXX" clientdomain.com
```

---

## Notes

- Our GA credentials are managed centrally on `mem-contact` at `~/analytics-dashboard/.env`
- Access tokens expire — always generate a fresh one per session (Step 3)
- A client may have multiple accounts if GA was set up more than once (e.g. by a prior agency). Check `createTime` and `industryCategory` to identify the correct/intentional one
- If a measurement ID doesn't appear in any of our GA accounts, it belongs to a GA account outside our access (likely the client's personal account or a prior agency's account)
