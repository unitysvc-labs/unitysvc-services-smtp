# SMTP-to-Email Bridge — `smtp-to-email`

Inbound email arrives at the UnitySVC SMTP gateway and is forwarded to **your own HTTP endpoint** as a faithful, lossless email envelope. Useful when something you already operate (a webhook receiver, an automation runner, a custom inbox processor) needs to react to email but can only speak HTTP.

This service is **free**: you supply the receiver, UnitySVC handles the SMTP-to-HTTP plumbing. For multiple receivers under one account, use the paid [`labs/smtp-to-email-plus`](../smtp-to-email-plus/).

## What gets POSTed to your endpoint

When mail arrives the gateway POSTs a single JSON body to `${ customer_secrets.HTTP_RELAY_BASE_URL }` containing the **full email envelope**, structured for downstream code:

| Field | Meaning |
|---|---|
| `from`, `to`, `cc`, `bcc`, `reply_to` | RFC addresses |
| `subject`, `date`, `message_id` | Standard email headers |
| `text_body`, `html_body` | Both bodies if present (else `null`) |
| `headers` | All raw headers, in order |
| `attachments[]` | `filename`, `content_type`, `size`, base64-encoded `content` |
| `spf`, `dkim`, `dmarc` | Authentication results from the gateway |

This is the **faithful** rendering — every field present in the original email is present in the POST. If you want a smaller `{title, body, type, format}` shape instead (closer to a notification envelope), use [`smtp-to-msg`](../smtp-to-msg/) instead.

## Authentication

- The **gateway** authenticates you via your UnitySVC svcpass — used as the SMTP password.
- The **receiver** is yours; you decide whether to gate it. Set `HTTP_RELAY_API_KEY` as a customer secret and the gateway forwards it as `Authorization: Bearer <api_key>`. Leave it unset and no auth header is added.

## Required customer secrets

| Name | Required | Purpose |
|---|---|---|
| `HTTP_RELAY_BASE_URL` | yes | URL of your HTTP receiver (e.g. `https://hooks.example.com/inbound-mail`) |
| `HTTP_RELAY_API_KEY` | optional | Token forwarded as `Authorization: Bearer …`. Omit when the receiver is public or uses a side-channel auth (e.g. signed query param). |

## Routing

- **Gateway address**: configured by `SMTP_GATEWAY_BASE_URL` (host:port) — e.g. `smtp.unitysvc.com:587`.
- **SMTP username**: `smtp-to-email` (the literal service name).
- **SMTP password**: your `UNITYSVC_API_KEY` (svcpass).

There is no per-customer SMTP username — customer attribution happens through the svcpass; all customers of this service share the literal `smtp-to-email` username.
