# openclaw-discord-button-repatch

Public-safe patch bundle for repairing OpenClaw Discord button/component regressions after updates, dist rebuilds, or local runtime drift.

This repo is for OpenClaw self-hosters who run into problems like:
- Discord buttons showing **"This component has expired"**
- `callbackData` / `customId` metadata no longer round-tripping correctly
- reusable buttons regressing after an `npm update` or rebuilt `dist/`
- local hotfixes getting overwritten and needing a repeatable repair path

## What this repo provides
- a sanitized `discord-button-repatch` skill under `skill/discord-button-repatch/`
- repatch wrapper scripts under `scripts/`
- a public-safe protocol note under `docs/`
- a packaged `.skill` artifact under `dist/`

## What gets patched
The repatch flow can repair three layers:

1. **OpenClaw Discord send modules**
   - preserves button callback metadata such as `callbackData`, `callback_data`, and `customId`

2. **OpenClaw Discord runtime / reply handlers**
   - restores callback handling paths so button interactions can still resolve correctly after dist regressions

3. **Optional sender shell scripts**
   - updates known sender flows so outgoing Discord button payloads include `reusable: true`

## Why this repo is public-safe
This version was sanitized before publishing:
- removed hardcoded local absolute paths
- removed internal runbook examples with real Discord channel IDs
- parameterized workspace, dist-root, cache-path, service-name, and sender-file inputs
- kept the patch logic, verification workflow, and restart guidance

## Quick start
### Verify / patch without restarting
```bash
python3 skill/discord-button-repatch/scripts/repatch_discord_buttons.py \
  --verify-only \
  --workspace /path/to/workspace
```

### Patch and hard-restart the gateway service
```bash
python3 skill/discord-button-repatch/scripts/repatch_discord_buttons.py \
  --restart \
  --workspace /path/to/workspace
```

### If OpenClaw is installed in a non-default location
```bash
python3 skill/discord-button-repatch/scripts/repatch_discord_buttons.py \
  --restart \
  --workspace /path/to/workspace \
  --dist-root /path/to/openclaw/dist
```

### If you want to patch additional sender scripts
```bash
python3 skill/discord-button-repatch/scripts/repatch_discord_buttons.py \
  --restart \
  --workspace /path/to/workspace \
  --sender-file /path/to/script-a.sh \
  --sender-file /path/to/script-b.sh
```

## Expected success signals
Read the JSON summary and confirm:
- every item in `sendFiles` is `ok: true`
- every item in `replyFiles` is `ok: true`
- expected items in `senderFiles` are `ok: true`
- `restart.ok` is `true` when `--restart` was used

## Repo layout
```text
skill/discord-button-repatch/   Source-of-truth skill contents
scripts/                        Convenience wrappers
docs/                           Public-safe protocol / design notes
dist/                           Packaged .skill artifact
```

## Safety / caveats
- This repo patches **compiled `dist/` files**, not upstream OpenClaw source.
- A **hard restart** is recommended after runtime-handler patching; do not rely on soft reload/SIGUSR1 for this workflow.
- Older Discord messages created before the fix may still need to be resent.
- Treat this repo as a repeatable hotfix toolkit, not a substitute for upstreaming proper source-level fixes.

## Packaging the skill
If you edit the skill and want to rebuild the `.skill` artifact, run the `package_skill.py` script from your local OpenClaw installation, for example:

```bash
python3 <path-to-openclaw>/skills/skill-creator/scripts/package_skill.py \
  skill/discord-button-repatch \
  dist
```

## Related files
- `skill/discord-button-repatch/SKILL.md`
- `skill/discord-button-repatch/references/targets.md`
- `skill/discord-button-repatch/scripts/repatch_discord_buttons.py`
- `docs/discord-buttons-shared-handler.public.md`

## Scope note
This public repo is the sanitized shareable variant. Keep host-specific deployment details, real channel IDs, and internal operational runbooks in a separate private repo.