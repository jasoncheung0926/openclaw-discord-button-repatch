# Discord button repatch targets (public-safe)

## Runtime targets
- `<openclaw-dist>/reply-*.js`
- `<openclaw-dist>/plugin-sdk/reply-*.js`
- `<openclaw-dist>/subagent-registry-*.js`
- `<openclaw-dist>/pi-embedded-*.js`

Expected invariants:
- helper block for callback cache exists
- callback fast-path runs before component-registry lookup when applicable
- consumed callback intercept exists

## Send targets
- `<openclaw-dist>/send-*.js`
- `<openclaw-dist>/plugin-sdk/send-*.js`

Expected invariants:
- `parseButtonSpec` accepts `callbackData` / `callback_data` / `customId`
- button entry stores `callbackData`

## Optional sender targets
Examples:
- `<workspace>/scripts/cron-phase1/btc-eth-15m-auto.sh`
- `<workspace>/scripts/cron-phase1/btc-5m-auto.sh`

Expected invariant:
- outgoing Discord component payload sets `reusable: true`
