# SMTP-to-Message Bridge (Multi-Enrollment) — `labs/smtp-to-msg-plus`

Same plumbing as `smtp-to-msg` (inbound email → strict `{title, body, type, format}` POST to an Apprise-compatible receiver), but with **per-enrollment destinations**: one account can route different mailboxes to different Apprise instances or different Apprise-compatible receivers. Pricing: **$1 per 1,000 emails** (1,000 emails per dollar).

If you only need **one** receiver, use the free single variant.

## Enrollment parameters

Each enrollment binds:

| Parameter | Required | Meaning |
|---|---|---|
| `base_url` | **yes** | The Apprise-compatible HTTP receiver URL for this enrollment (e.g. `https://apprise.unitysvc.dev/notify/<key>`). Stored as a literal at enroll time. |
| `api_key_secret` | optional | Name of a customer secret holding the bearer token for *this* enrollment's receiver. Forwarded as `Authorization: Bearer <secret>`. Omit when the receiver doesn't gate on auth. |

## Routing

- **Gateway address**: `SMTP_GATEWAY_BASE_URL`.
- **SMTP username**: the **6-character enrollment code** issued at enroll time.
- **SMTP password**: your `UNITYSVC_API_KEY` (svcpass) — same across enrollments.

## Payload

Identical to `smtp-to-msg`'s — every receiver gets the strict `{title, body, type, format}` envelope. See the [free variant's description](../smtp-to-msg/description.md) for the mapping table.

## When to pick `-plus` over single

- Several different chat services (one Apprise instance per): different Discord servers, different Slack workspaces, different ntfy topics.
- Per-route auth tokens that should not be shared (the bearer token for an internal apprise-api ≠ the one for the public `apprise.unitysvc.dev/notify/<key>`).
- Per-route URL rotation without disturbing the others.
