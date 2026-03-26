---
name: discord-button-repatch
description: Repair and reapply OpenClaw Discord button/component hotfixes after OpenClaw updates, dist rebuilds, or runtime regressions. Use when Discord buttons start returning "This component has expired", when callbackData/customId metadata stops round-tripping through Discord send/runtime layers, when reusable buttons regress after npm update, or when you need a one-command patch + verify + hard-restart workflow for Discord component handlers.
---

# Discord Button Repatch

Use the bundled repatch script instead of hand-editing OpenClaw `dist/` files.

## Quick start

- Run `python3 skill/discord-button-repatch/scripts/repatch_discord_buttons.py --restart --workspace <workspace>` for the normal repair path.
- Run `python3 skill/discord-button-repatch/scripts/repatch_discord_buttons.py --verify-only --workspace <workspace>` when you want an idempotent check without restarting the gateway.
- If OpenClaw is installed in a non-default location, also pass `--dist-root <path-to-openclaw-dist>`.
- Read the JSON summary and confirm:
  - all `sendFiles` are `ok: true`
  - all `replyFiles` are `ok: true`
  - expected sender scripts are `ok: true`
  - `restart.ok` is `true` when `--restart` was used

## What the script repairs

- OpenClaw Discord send modules so button specs preserve `callbackData`
- OpenClaw Discord runtime handlers so callback metadata can resolve from cache before/after component-registry lookup
- optional sender shell scripts so outgoing button payloads include `reusable: true`
- optional hard restart of `openclaw-gateway.service`

## Hard rule

For runtime handler patches, use a **hard systemd restart**. Do not rely on soft reload/SIGUSR1 for this workflow.

## Bundled script

- `scripts/repatch_discord_buttons.py`
  - idempotent patcher
  - verifies send/runtime/sender paths
  - optionally restarts `openclaw-gateway.service`
  - prints JSON summary for audit/debugging

## References

- Read `references/targets.md` when you need the expected target patterns and patch invariants.
