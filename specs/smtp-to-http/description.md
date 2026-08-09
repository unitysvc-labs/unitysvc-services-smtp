# SMTP-to-HTTP Bridge — `smtp-to-http`

Inbound email arrives at the UnitySVC SMTP gateway and is forwarded to **your own HTTP endpoint** as a faithful, lossless email envelope. Useful when something you already operate (a webhook receiver, an automation runner, a custom inbox processor) needs to react to email but can only speak HTTP.

You supply the receiver; UnitySVC handles the SMTP-to-HTTP plumbing. If you want a smaller `{title, body, type, format}` notification shape instead of the full envelope, use the `smtp-to-msg` service.

## What gets POSTed to your endpoint

When mail arrives the gateway POSTs a single JSON body containing the **full email envelope**, structured for downstream code:

| Field | Meaning |
|---|---|
| `from`, `to`, `cc`, `bcc`, `reply_to` | RFC addresses |
| `subject`, `date`, `message_id` | Standard email headers |
| `text_body`, `html_body` | Both bodies if present (else `null`) |
| `headers` | All raw headers, in order |
| `attachments[]` | `filename`, `content_type`, `size`, base64-encoded `content` |
| `spf`, `dkim`, `dmarc` | Authentication results from the gateway |

This is the **faithful** rendering — every field present in the original email is present in the POST.

## Authentication

In both channels the **gateway** authenticates you via your UnitySVC svcpass, used as the SMTP password. The **receiver** is yours; you decide whether to gate it. Give the gateway a bearer token and it forwards `Authorization: Bearer <token>`; give it none and no auth header is added.

## Two ways to use this service

This service exposes two **upstream access channels**. Pick whichever fits — you can use both. The email envelope the receiver gets is identical regardless of channel; only **where the destination URL and bearer token come from** changes.

| | `byok` — stored receiver | `plus` — per-enrollment receivers |
|---|---|---|
| Best for | one fixed receiver | many email-to-webhook routes under one account |
| Destination URL | `HTTP_RELAY_BASE_URL` customer secret | a `base_url` parameter per enrollment |
| Bearer token | `HTTP_RELAY_API_KEY` customer secret (optional) | the secret named by the `api_key_secret` parameter (optional) |
| SMTP username | `smtp-to-http` | the enrollment's 6-character code |
| Reached at | the canonical gateway address | a unique `/e/<code>` address per enrollment |
| Price | **free** | **$0.001 / email** ($1 per 1,000) |

### Method 1 — Stored receiver (`byok`, free)

One receiver, configured once via customer secrets.

1. **Set your receiver** as customer secrets:
   - `HTTP_RELAY_BASE_URL` — your HTTP receiver URL (e.g. `https://hooks.example.com/inbound-mail`)
   - `HTTP_RELAY_API_KEY` — *(optional)* bearer token; omit when the receiver is public.
2. **Send email** to the gateway with SMTP username `smtp-to-http` and your svcpass as the password. Any `To:` address works — routing is by SMTP user, not recipient.

A minimal Python receiver:

```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/inbound-mail")
async def inbound(req: Request):
    body = await req.json()
    print("from:", body["from"], "subject:", body["subject"])
    return {"ok": True}
```

Send a test through the gateway:

```python
import smtplib, os
from email.message import EmailMessage

msg = EmailMessage()
msg["From"]    = "alice@example.com"
msg["To"]      = "router@unitysvc.com"
msg["Subject"] = "hello from smtp-to-http"
msg.set_content("If you can see this in your HTTP receiver, the bridge works.")

with smtplib.SMTP(os.environ["SMTP_GATEWAY_HOST"], int(os.environ["SMTP_GATEWAY_PORT"])) as s:
    s.starttls()
    s.login("smtp-to-http", os.environ["UNITYSVC_API_KEY"])
    s.send_message(msg)
```

### Method 2 — Per-enrollment receivers (`plus`, metered)

Run **multiple** email-to-webhook routes under one account — e.g. `sales@…` → CRM webhook, `support@…` → ticket queue, `ops@…` → on-call paging. Each enrollment binds:

| Parameter | Required | Meaning |
|---|---|---|
| `base_url` | **yes** | HTTP receiver URL for this enrollment, e.g. `https://hooks.example.com/sales-inbound`. A literal, not a secret. |
| `api_key_secret` | optional | Name of a customer secret holding this receiver's bearer token, forwarded as `Authorization: Bearer <secret>`. Empty when the receiver is public. |

The `base_url` is fixed per enrollment; re-enroll (or update) to move it. The `api_key_secret` value is resolved at request time, so rotating a token is a `usvc_seller secrets set` away — no re-enroll.

1. **(Optional) Save each receiver's bearer token** as a customer secret — one per route:

   ```bash
   usvc_seller secrets set CRM_API_KEY      --value "<crm-bearer>"
   usvc_seller secrets set HELPDESK_API_KEY --value "<helpdesk-bearer>"
   ```

2. **Enroll, one per route**, supplying the destination inline:

   ```json
   { "base_url": "https://crm.example.com/inbound-mail",      "api_key_secret": "CRM_API_KEY" }
   ```
   ```json
   { "base_url": "https://helpdesk.example.com/email-ingest", "api_key_secret": "HELPDESK_API_KEY" }
   ```
   ```json
   { "base_url": "https://oncall.example.com/page" }
   ```

   Each enrollment returns its own **6-character code** — that's the SMTP username for that route.

3. **Send mail through the right route** — the username selects the enrollment; the same svcpass authenticates every route:

   ```python
   send("XXXXXX", "lead: Acme Corp",      "Asked for a demo …")   # -> CRM
   send("YYYYYY", "ticket: login broken", "User foo cannot …")    # -> Helpdesk
   send("ZZZZZZ", "ALERT: api down",      "p99 > 5s for 10m …")   # -> Ops
   ```

## Troubleshooting

- **No POST arrives** — confirm the destination is set (`HTTP_RELAY_BASE_URL` for `byok`, or the enrollment's `base_url` for `plus`); confirm the receiver is publicly reachable; confirm the SMTP login succeeded (a clean `250` only follows a valid svcpass auth).
- **POST arrives, receiver 401s** — bearer-token mismatch; check `HTTP_RELAY_API_KEY` (byok) or the enrollment's `api_key_secret` value, and that the receiver expects `Authorization: Bearer`.
- **All `plus` emails hit the same receiver** — you used the wrong enrollment code as the SMTP username. Each route has its own.
- **Attachments missing** — they're in `attachments[].content` as base64; some clients show only `text_body`/`html_body`.
