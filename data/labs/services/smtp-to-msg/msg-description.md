# SMTP-to-Message Bridge — `smtp-to-msg`

Inbound email arrives at the UnitySVC SMTP gateway and is forwarded to **your HTTP endpoint as the strict notification envelope** `{title, body, type, format}` — the same shape `apprise-api`'s `/notify` accepts and `mailrise` emits. Drop in an existing apprise-api / mailrise compatible receiver and it just works.

This is the **summary** rendering of an email — only what a notification cares about. If you need the full email (headers, attachments, dkim/spf, both bodies, etc.), use the `smtp-to-email` service instead. For multiple receivers under one account, use the paid `labs/smtp-to-msg-plus` service.

## What gets POSTed to your endpoint

A single JSON body, fields drawn from the email:

| Field | Source | Default |
|---|---|---|
| `title`  | email `Subject` header | empty string if missing |
| `body`   | email `text_body` (preferred) or stripped `html_body` | empty string if missing |
| `type`   | `info` (always — `type` is advisory) | `info` |
| `format` | `text` when the email body is text/plain; `html` when text/html | `text` |

No other fields. The mapping is intentionally narrow so the same payload can target any Apprise-compatible receiver without per-channel branching.

## When to pick this over `smtp-to-email`

- ✅ **Pick `smtp-to-msg`** when your receiver only wants the "what to display in a notification" pieces — a chat post, a phone push, a desk lamp blinking.
- ❌ **Don't** pick it when you need attachments, multiple recipients, raw headers, or the original HTML body — those are dropped. Use `smtp-to-email`.

## Authentication

Identical to `smtp-to-email`: gateway via SMTP-AUTH with the svcpass, receiver via `HTTP_RELAY_API_KEY` if set.

## Required customer secrets

| Name | Required | Purpose |
|---|---|---|
| `HTTP_RELAY_BASE_URL` | yes | URL of your apprise-api / mailrise-compatible receiver |
| `HTTP_RELAY_API_KEY` | optional | Bearer token forwarded as `Authorization: Bearer …` |

## Routing

- **Gateway address**: `SMTP_GATEWAY_BASE_URL`.
- **SMTP username**: `smtp-to-msg`.
- **SMTP password**: your `UNITYSVC_API_KEY` (svcpass).
