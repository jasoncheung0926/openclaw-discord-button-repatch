# openclaw-discord-button-repatch

Public-safe repo for the OpenClaw Discord button/component hotfix workflow.

## What is inside
- a sanitized `discord-button-repatch` skill under `skill/discord-button-repatch/`
- convenience wrappers under `scripts/`
- a public-safe protocol note under `docs/`
- packaged `.skill` artifact under `dist/`

## What was sanitized
- removed hardcoded local absolute paths
- removed internal runbook examples with real Discord channel ids
- parameterized workspace / dist-root / sender file selection
- kept the patch logic, verification workflow, and restart guidance

## Quick start
```bash
python3 skill/discord-button-repatch/scripts/repatch_discord_buttons.py --restart --workspace /path/to/workspace
```

If OpenClaw is installed outside the default npm-global path, also pass:

```bash
--dist-root /path/to/openclaw/dist
```
