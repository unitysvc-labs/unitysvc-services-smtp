# SMTP-to-Message Bridge — `smtp-to-msg`

Send an email to the UnitySVC SMTP gateway and it is delivered to your own HTTP endpoint as a compact JSON notification — the platform `msg` envelope `{title, body, type, format}` plus `attachment` when the email carries files, with the subject as `title` and the body as `body`. Any system that can send email becomes a webhook to a receiver you control. For the full message (all headers, attachments, both bodies, DKIM/SPF), use `smtp-to-http` instead.

## What your endpoint receives

| Field        | Source                                                                    | Default |
| ------------ | ------------------------------------------------------------------------- | ------- |
| `title`      | email `Subject`                                                           | `""`    |
| `body`       | the plain-text part; an HTML-only email is converted to markdown          | `""`    |
| `type`       | always `info` (advisory)                                                  | `info`  |
| `format`     | `text` for a plain-text part, `markdown` for a converted HTML-only email  | `text`  |
| `attachment` | the email's attached files as `{base64, filename}` entries (omitted when none) | —  |

An HTML-only email keeps bold, italic, code and links: they become the markdown subset every `msg-to-*` channel renders, and everything else becomes plain text. `html` is no longer sent as a `format`.

Attachments are capped at 10 files, 5 MiB each and 10 MiB in total; inline images embedded in the HTML (`cid:` parts) are not included. A file that exceeds a cap is left out, and the message is still delivered. When you forward the result to a `msg-to-*` service, channels that upload files (the Apprise-based ones) deliver the attachments; other channels ignore them.

## Channels

Authenticate with your svcpass as the SMTP password, then pick a channel — you can use both:

|               | `byok` — stored receiver (free)                                            | `plus` — per-enrollment receivers ($0.001/email)          |
| ------------- | -------------------------------------------------------------------------- | --------------------------------------------------------- |
| Destination   | `SMTP_HTTP_RELAY_BASE_URL` secret (+ optional `SMTP_HTTP_RELAY_API_KEY` bearer) | a `base_url` per enrollment (+ optional `api_key_secret`) |
| SMTP username | `smtp-to-msg`                                                              | the enrollment's 6-character code                         |
| Reached at    | the canonical gateway address                                              | a unique `/e/<code>` address                              |

See the attached **shell** and **python** code examples for how to send. Any endpoint that accepts `POST application/json` with the envelope works; the platform sink `https://sink.unitysvc.dev` records each POST — query it at `/retrieve?search=<marker>&wait=<s>` to confirm delivery in a smoke test.

## Troubleshooting

- **No notification arrives** — confirm your receiver accepts a `POST` of the `msg` envelope (`{title, body, type, format}`, plus `attachment` when present) at that URL.
- **`plus`: all mail hits one receiver** — wrong enrollment code as the SMTP username; each route has its own.
- **One route 401s, others work** — that enrollment's `api_key_secret` doesn't match the receiver, or is stale. Re-set it.
