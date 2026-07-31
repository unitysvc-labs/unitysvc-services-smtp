# SMTP-to-Message Bridge — `smtp-to-msg`

Inbound email arrives at the UnitySVC SMTP gateway and is forwarded to **your HTTP endpoint as the strict notification envelope** `{title, body, type, format}` — the same shape `apprise-api`'s `/notify` accepts and `mailrise` emits. Drop in an existing apprise-api / mailrise compatible receiver and it just works.

This is the **summary** rendering of an email — only what a notification cares about. If you need the full email (headers, attachments, dkim/spf, both bodies), use the `smtp-to-email` service instead.

## What gets POSTed to your endpoint

A single JSON body, fields drawn from the email:

| Field | Source | Default |
|---|---|---|
| `title`  | email `Subject` header | empty string if missing |
| `body`   | email `text_body` (preferred) or stripped `html_body` | empty string if missing |
| `type`   | `info` (always — `type` is advisory) | `info` |
| `format` | `text` when the email body is text/plain; `html` when text/html | `text` |

No other fields. The mapping is intentionally narrow so the same payload can target any Apprise-compatible receiver without per-channel branching.

## Authentication

In both channels the **gateway** authenticates you via your UnitySVC svcpass, used as the SMTP password. The **receiver** is yours; set a bearer token and the gateway forwards `Authorization: Bearer <token>`, or leave it unset for a public receiver.

## Two ways to use this service

This service exposes two **upstream access channels**. Pick whichever fits — you can use both. Every receiver gets the same `{title, body, type, format}` envelope regardless of channel; only **where the destination URL and bearer token come from** changes.

| | `byok` — stored receiver | `plus` — per-enrollment receivers |
|---|---|---|
| Best for | one fixed receiver | different mailboxes → different Apprise instances |
| Destination URL | `HTTP_RELAY_BASE_URL` customer secret | a `base_url` parameter per enrollment |
| Bearer token | `HTTP_RELAY_API_KEY` customer secret (optional) | the secret named by the `api_key_secret` parameter (optional) |
| SMTP username | `smtp-to-msg` | the enrollment's 6-character code |
| Reached at | the canonical gateway address | a unique `/e/<code>` address per enrollment |
| Price | **free** | **$0.001 / email** ($1 per 1,000) |

Any receiver that accepts `POST application/json` with `{title, body, type, format}` works — e.g. run [apprise-api](https://github.com/caronc/apprise-api) yourself (`/notify`), or use the hosted `https://apprise.unitysvc.dev/notify/<key>`. For a bare smoke test, `https://echo.unitysvc.dev` echoes the body back.

### Method 1 — Stored receiver (`byok`, free)

One receiver, configured once via customer secrets.

1. **Set your receiver** as customer secrets:
   - `HTTP_RELAY_BASE_URL` — your apprise-api / mailrise-compatible receiver URL
   - `HTTP_RELAY_API_KEY` — *(optional)* bearer token; omit when the receiver is public.
2. **Send email** to the gateway with SMTP username `smtp-to-msg` and your svcpass as the password. The subject becomes `title`, the body becomes `body`.

```python
import smtplib, os
from email.message import EmailMessage

msg = EmailMessage()
msg["From"]    = "alerts@example.com"
msg["To"]      = "router@unitysvc.com"
msg["Subject"] = "p99 latency over 5s"                              # -> title
msg.set_content("checkout-api p99 = 6.4s for 10m; on-call paged.")  # -> body

with smtplib.SMTP(os.environ["SMTP_GATEWAY_HOST"], int(os.environ["SMTP_GATEWAY_PORT"])) as s:
    s.starttls()
    s.login("smtp-to-msg", os.environ["UNITYSVC_API_KEY"])
    s.send_message(msg)
```

Your receiver gets `{"title": "p99 latency over 5s", "body": "checkout-api p99 = 6.4s …", "type": "info", "format": "text"}`. Plug that into apprise-api with destinations like `discord://…` / `tgram://…` / `ntfy://…` and the same email reaches whichever channels your apprise config targets.

### Method 2 — Per-enrollment receivers (`plus`, metered)

Route different mailboxes to different Apprise instances — e.g. one instance per audience of channels. Each enrollment binds:

| Parameter | Required | Meaning |
|---|---|---|
| `base_url` | **yes** | The Apprise-compatible receiver URL for this enrollment (e.g. `https://apprise.unitysvc.dev/notify/<key>`). A literal, not a secret. |
| `api_key_secret` | optional | Name of a customer secret holding this receiver's bearer token, forwarded as `Authorization: Bearer <secret>`. Omit when the receiver is public. |

Per-route destinations (Slack webhook, Discord URL, etc.) are configured **inside** each Apprise instance — this service routes the email to the right instance; Apprise handles the channel fan-out.

1. **(Optional) Save each receiver's bearer token** as a customer secret — one per route:

   ```bash
   usvc_seller secrets set APPRISE_SALES_KEY --value "<bearer>"
   usvc_seller secrets set APPRISE_OPS_KEY   --value "<bearer>"
   ```

2. **Enroll, one per route**, supplying the destination inline:

   ```json
   { "base_url": "https://apprise-sales.example.com/notify", "api_key_secret": "APPRISE_SALES_KEY" }
   ```
   ```json
   { "base_url": "https://apprise-ops.example.com/notify",   "api_key_secret": "APPRISE_OPS_KEY" }
   ```
   ```json
   { "base_url": "https://apprise.unitysvc.dev/notify/<key>" }
   ```

   Each enrollment returns its own **6-character code** — that's the SMTP username for that route.

3. **Send mail through the right route** — the username selects the enrollment; the same svcpass authenticates every route:

   ```python
   notify("XXXXXX", "lead: Acme Corp",        "asked for demo …")   # -> sales Apprise
   notify("YYYYYY", "ALERT: checkout p99>5s", "see grafana …")      # -> ops Apprise
   notify("ZZZZZZ", "blog: spring promo",     "live now …")         # -> marketing Apprise
   ```

## Troubleshooting

- **`base_url` looks right but no notification arrives** — confirm your Apprise instance accepts the `/notify` shape (`{title, body, type, format}`); older builds use different paths.
- **Wrong channel fires** — that's config inside your Apprise instance, not the gateway. The gateway just delivers the JSON.
- **`plus`: emails all hit one receiver** — you used the wrong enrollment code as the SMTP username. Each route has its own.
- **One route 401s, others work** — that enrollment's `api_key_secret` value doesn't match what the receiver expects, or the secret is stale. Re-set it.
