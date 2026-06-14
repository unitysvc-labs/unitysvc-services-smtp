# SMTP-to-Email Bridge (Multi-Enrollment) — `labs/smtp-to-email-plus`

Same plumbing as `smtp-to-email` (inbound email → faithful HTTP POST of the full envelope), but with **per-enrollment destination URLs**: one account can run many independent email-to-webhook routes — e.g. `sales@…` → CRM webhook, `support@…` → ticket queue, `ops@…` → on-call paging. Pricing: **$1 per 1,000 emails** (1,000 emails per dollar).

If you only need **one** receiver, use the free single variant — this paid `-plus` exists for the multi-route case.

## Enrollment parameters

Each enrollment binds:

| Parameter | Required | Meaning |
|---|---|---|
| `base_url` | **yes** | The HTTP receiver URL for this enrollment, e.g. `https://hooks.example.com/sales-inbound`. Stored as a literal at enroll time, not as a secret. |
| `api_key_secret` | optional | Name of a customer secret holding the bearer token for *this* enrollment's receiver. Forwarded as `Authorization: Bearer <secret>`. Leave empty when the receiver is public. |

The customer secret named in `api_key_secret` is resolved at request time, so rotating a key is a `usvc_seller secrets set` away — no re-enroll needed. The `base_url` is fixed per enrollment; re-enroll (or update) to point it somewhere else.

## Routing

- **Gateway address**: `SMTP_GATEWAY_BASE_URL` (host:port).
- **SMTP username**: the **6-character enrollment code** issued at enroll time. Each enrollment gets its own code; the code selects which enrollment's `base_url` + `api_key_secret` the gateway resolves.
- **SMTP password**: your `UNITYSVC_API_KEY` (svcpass) — same key across enrollments. The code is what disambiguates, not the password.

## Payload

Identical to `smtp-to-email`'s — see its [description](../smtp-to-email/description.md). The receiver gets the same lossless email JSON regardless of which enrollment routed it.
