# SMTP-to-Message Bridge — `smtp-to-msg`

Send an email to the UnitySVC SMTP gateway and it is delivered to your own HTTP endpoint as a compact JSON notification — `{title, body, type, format}`, with the subject as `title` and the body as `body`. Any system that can send email becomes a webhook to a receiver you control. For the full message (all headers, attachments, both bodies, DKIM/SPF), use `smtp-to-http` instead.

## What your endpoint receives

| Field | Source | Default |
|---|---|---|
| `title`  | email `Subject` | `""` |
| `body`   | `text_body`, else stripped `html_body` | `""` |
| `type`   | always `info` (advisory) | `info` |
| `format` | `text` or `html`, from the body's content type | `text` |

## Channels

Authenticate with your svcpass as the SMTP password, then pick a channel — you can use both:

| | `byok` — stored receiver (free) | `plus` — per-enrollment receivers ($0.001/email) |
|---|---|---|
| Destination | `HTTP_RELAY_BASE_URL` secret (+ optional `HTTP_RELAY_API_KEY` bearer) | a `base_url` per enrollment (+ optional `api_key_secret`) |
| SMTP username | `smtp-to-msg` | the enrollment's 6-character code |
| Reached at | the canonical gateway address | a unique `/e/<code>` address |

See the attached **shell** and **python** code examples for how to send. Any endpoint that accepts `POST application/json` with the envelope works; the platform sink `https://sink.unitysvc.dev` records each POST — query it at `/retrieve?search=<marker>&wait=<s>` to confirm delivery in a smoke test.

## Troubleshooting

- **No notification arrives** — confirm your receiver accepts a `POST` of `{title, body, type, format}` at that URL.
- **`plus`: all mail hits one receiver** — wrong enrollment code as the SMTP username; each route has its own.
- **One route 401s, others work** — that enrollment's `api_key_secret` doesn't match the receiver, or is stale. Re-set it.
