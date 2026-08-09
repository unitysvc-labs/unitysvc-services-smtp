# CLAUDE.md — unitysvc-services-smtp

Guidance for working on this seller-services repo. See also the
`writing-unitysvc-services` skill for the full authoring/verification workflow.

## Testing services — read before diagnosing a `run-tests` failure

- **Draft status is NOT a cause of test failures.** When you run
  `usvc_seller services run-tests` (or `specs run-tests`), the platform
  **temporarily flips the service to `pending`** for the duration of the test so
  the gateway will route to it. A service sitting in `draft` (or `rejected`) on
  the staging listing is expected and fine while testing. Do **not** chase
  service status when a `run-tests` send fails — it has repeatedly sent us down
  the wrong path.
- A gateway send-path **550 "No active enrollment found"** for an
  enrollment-required SMTP service is about **enrollment → AccessInterface
  routing** (the enrollment-scoped AI / bridge and the rendered
  `routing_key.username`), not the service status.
- The backend enrollment-access logic is verified correct against clean data
  (see the backend repro `test_smtp_enrollment_provisioning_repro.py`): the ops
  enrollment is a **shared** enrollment (`customer_id = OPS_CUSTOMER_ID`,
  `owner_id = NULL`) and resolves owner-agnostically. So a staging 550 that a
  clean re-provision doesn't fix is a **staging data condition** (stale /
  conflicting AccessInterface rows), not a code defect.

## Pipeline order (all four must be green)

`specs validate` → `specs format` → `specs run-tests <name>` (upstream) →
`specs upload <name>` → `services run-tests <name> --force` (gateway).

- The upstream-side connectivity test needs the SMTP host in the environment; an
  `expected '220' greeting from :587` / **empty-host** failure run locally is an
  env gap (missing `SMTP_GATEWAY_HOST`), not a service defect.
- `service.json` sidecars: commit the **minimal** `{ "service_id": "…" }` form.
  `run-tests`/`upload` may write back a richer sidecar (name/status/…) — that is
  transient tool output; revert it before committing.
