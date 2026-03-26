# Discord Buttons Shared Handler (public-safe pattern)

## Goal
Use one button protocol that works across multiple workflows, not only one feature.

## Callback key pattern
Use scoped callback keys:

`<ns>:<sessionScope>:<action>:<id>`

Examples:
- `abt:disc<channelId>:detail:<lookupId>`
- `ops:disc<channelId>:approve:<jobId>`
- `bt:disc<channelId>:rerun:<configId>`

Where:
- `ns` = feature namespace (`abt`, `ops`, `bt`, ...)
- `sessionScope` = channel/session scope tag
- `action` = semantic action (`detail`, `approve`, `retry`, ...)
- `id` = lookup key / nonce

## Routing model
1. Parse callback key into `{ns, sessionScope, action, id}`
2. Resolve handler by `ns`
3. Verify session/channel matches `sessionScope` when required
4. Resolve payload from feature cache/store
5. Update message (or fallback ack if no resolver)

## Fallback behavior
- If no resolver matched, show a generic ack such as `✅ Selected: <value>`.

## Operational requirement
After any gateway `dist` button-handler patch:
- use a **hard restart** of the relevant systemd user service
- do not rely on soft reload/SIGUSR1 for this workflow
