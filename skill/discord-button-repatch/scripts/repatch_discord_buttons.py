#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable

DEFAULT_DIST = Path.home() / '.npm-global/lib/node_modules/openclaw/dist'

SEND_PARSE_OLD = r'''function parseButtonSpec(raw, label) {
	const obj = requireObject(raw, label);
	const style = readOptionalString(obj.style);
	const url = readOptionalString(obj.url);
	if ((style === "link" || url) && !url) throw new Error(`${label}.url is required for link buttons`);
	return {
		label: readString(obj.label, `${label}.label`),
		style,
		url,
		emoji: typeof obj.emoji === "object" && obj.emoji && !Array.isArray(obj.emoji) ? {
			name: readString(obj.emoji.name, `${label}.emoji.name`),
			id: readOptionalString(obj.emoji.id),
			animated: typeof obj.emoji.animated === "boolean" ? obj.emoji.animated : void 0
		} : void 0,
		disabled: typeof obj.disabled === "boolean" ? obj.disabled : void 0,
		allowedUsers: readOptionalStringArray(obj.allowedUsers, `${label}.allowedUsers`)
	};
}'''

SEND_PARSE_NEW = r'''function parseButtonSpec(raw, label) {
	const obj = requireObject(raw, label);
	const style = readOptionalString(obj.style);
	const url = readOptionalString(obj.url);
	const callbackData = readOptionalString(obj.callbackData) ?? readOptionalString(obj.callback_data) ?? readOptionalString(obj.customId) ?? readOptionalString(obj.custom_id);
	if ((style === "link" || url) && !url) throw new Error(`${label}.url is required for link buttons`);
	if (callbackData && url) throw new Error(`${label}.callbackData is not supported for link buttons`);
	return {
		label: readString(obj.label, `${label}.label`),
		style,
		url,
		callbackData,
		emoji: typeof obj.emoji === "object" && obj.emoji && !Array.isArray(obj.emoji) ? {
			name: readString(obj.emoji.name, `${label}.emoji.name`),
			id: readOptionalString(obj.emoji.id),
			animated: typeof obj.emoji.animated === "boolean" ? obj.emoji.animated : void 0
		} : void 0,
		disabled: typeof obj.disabled === "boolean" ? obj.disabled : void 0,
		allowedUsers: readOptionalStringArray(obj.allowedUsers, `${label}.allowedUsers`)
	};
}'''

SEND_ENTRY_OLD = r'''		entry: {
			id: componentId,
			kind: params.modalId ? "modal-trigger" : "button",
			label: params.spec.label,
			modalId: params.modalId,
			allowedUsers: params.spec.allowedUsers
		}
	};'''

SEND_ENTRY_NEW = r'''		entry: {
			id: componentId,
			kind: params.modalId ? "modal-trigger" : "button",
			label: params.spec.label,
			modalId: params.modalId,
			allowedUsers: params.spec.allowedUsers,
			callbackData: params.spec.callbackData
		}
	};'''

HANDLE_MARKER = 'async function handleDiscordComponentEvent(params) {'
FASTPATH_NEEDLE = 'const parsedScoped = parseScopedCallbackKey(parsed.componentId);'
CONSUMED_NEEDLE = 'const callbackData = typeof consumed.callbackData === "string" ? consumed.callbackData.trim() : "";'
HELPER_NEEDLE = 'const AUTOBET_DETAIL_CACHE_PATH = '
SEND_PARSE_NEEDLE = 'const callbackData = readOptionalString(obj.callbackData) ?? readOptionalString(obj.callback_data) ?? readOptionalString(obj.customId) ?? readOptionalString(obj.custom_id);'
SEND_ENTRY_NEEDLE = 'callbackData: params.spec.callbackData'
SENDER_REUSABLE_NEEDLE = '      reusable: true,'

SENDER_COMPONENTS_OLD = r'''    const components = JSON.stringify({
      blocks: [{
        type: 'actions',
        buttons: [{ label: 'more detail', style: 'primary', callbackData: String(entry.key) }]
      }]
    });'''

SENDER_COMPONENTS_NEW = r'''    const components = JSON.stringify({
      reusable: true,
      blocks: [{
        type: 'actions',
        buttons: [{ label: 'more detail', style: 'primary', callbackData: String(entry.key) }]
      }]
    });'''


def build_helper_block(cache_path: Path) -> str:
    cache_literal = str(cache_path).replace('\\', '/')
    return f'''const AUTOBET_DETAIL_CACHE_PATH = "{cache_literal}";
function readAutobetDetailCacheEntry(callbackData) {{
	if (typeof callbackData !== "string") return null;
	const key = callbackData.trim();
	if (!key) return null;
	try {{
		const raw = fs.readFileSync(AUTOBET_DETAIL_CACHE_PATH, "utf-8");
		const parsed = JSON.parse(raw);
		const entry = parsed?.[key];
		if (!entry || typeof entry !== "object") return null;
		const detail = typeof entry.detail === "string" ? entry.detail.trim() : "";
		const short = typeof entry.short === "string" ? entry.short.trim() : "";
		return {{ key, detail, short }};
	}} catch {{
		return null;
	}}
}}
function parseScopedCallbackKey(callbackData) {{
	if (typeof callbackData !== "string") return null;
	const trimmed = callbackData.trim();
	if (!trimmed) return null;
	const parts = trimmed.split(":");
	if (parts.length < 4) return {{ raw: trimmed, ns: null, sessionScope: null, action: null, id: null }};
	const [ns, sessionScope, action, ...rest] = parts;
	return {{ raw: trimmed, ns, sessionScope, action, id: rest.join(":") || null }};
}}
async function handleLegacyCallbackDataInteraction(interaction, callbackData) {{
	const parsed = parseScopedCallbackKey(callbackData);
	if (!parsed) return false;
	if (parsed.ns === "abt") {{
		const cached = readAutobetDetailCacheEntry(parsed.raw);
		const content = cached?.detail || cached?.short || ("⚠️ detail not found: " + parsed.raw);
		try {{
			await interaction.update({{
				content,
				components: []
			}});
		}} catch {{
			try {{
				await interaction.reply({{
					content,
					ephemeral: true
				}});
			}} catch {{}}
		}}
		return true;
	}}
	if (parsed.ns) {{
		const content = "✅ Selected: " + parsed.raw;
		try {{
			await interaction.update({{
				content,
				components: []
			}});
		}} catch {{
			try {{
				await interaction.reply({{
					content,
					ephemeral: true
				}});
			}} catch {{}}
		}}
		return true;
	}}
	return false;
}}
'''


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding='utf-8')


def replace_once(text: str, old: str, new: str):
    if old not in text:
        return text, False
    return text.replace(old, new, 1), True


def collect_send_files(dist: Path) -> list[Path]:
    paths = []
    for pattern in [str(dist / 'send-*.js'), str(dist / 'plugin-sdk' / 'send-*.js')]:
        for raw in sorted(glob.glob(pattern)):
            path = Path(raw)
            try:
                content = read_text(path)
            except Exception:
                continue
            if 'function createButtonComponent(params)' in content and 'function parseButtonSpec(raw, label)' in content:
                paths.append(path)
    return paths


def collect_reply_files(dist: Path) -> list[Path]:
    paths = []
    for pattern in [
        str(dist / 'reply-*.js'),
        str(dist / 'plugin-sdk' / 'reply-*.js'),
        str(dist / 'subagent-registry-*.js'),
        str(dist / 'pi-embedded-*.js'),
    ]:
        for raw in sorted(glob.glob(pattern)):
            path = Path(raw)
            try:
                content = read_text(path)
            except Exception:
                continue
            if HANDLE_MARKER in content:
                paths.append(path)
    return paths


def patch_send_file(path: Path) -> dict:
    content = read_text(path)
    original = content
    changes = []

    if SEND_PARSE_NEEDLE not in content:
        content, changed = replace_once(content, SEND_PARSE_OLD, SEND_PARSE_NEW)
        if changed:
            changes.append('parseButtonSpec.callbackData')
    if SEND_ENTRY_NEEDLE not in content:
        content, changed = replace_once(content, SEND_ENTRY_OLD, SEND_ENTRY_NEW)
        if changed:
            changes.append('createButtonComponent.entry.callbackData')

    if content != original:
        write_text(path, content)

    ok = SEND_PARSE_NEEDLE in content and SEND_ENTRY_NEEDLE in content
    return {'path': str(path), 'changed': bool(changes), 'changes': changes, 'ok': ok}


def patch_reply_file(path: Path, cache_path: Path) -> dict:
    content = read_text(path)
    original = content
    changes = []

    marker_idx = content.find(HANDLE_MARKER)
    if marker_idx == -1:
        return {'path': str(path), 'changed': False, 'changes': [], 'ok': False, 'reason': 'missing handleDiscordComponentEvent'}

    if HELPER_NEEDLE not in content:
        content = content[:marker_idx] + build_helper_block(cache_path) + content[marker_idx:]
        marker_idx = content.find(HANDLE_MARKER)
        changes.append('helper.block')

    if FASTPATH_NEEDLE not in content:
        entry_marker = '\tconst entry = resolveDiscordComponentEntry({'
        entry_idx = content.find(entry_marker, marker_idx)
        if entry_idx != -1:
            fastpath = '\tconst parsedScoped = parseScopedCallbackKey(parsed.componentId);\n\tif (parsedScoped?.ns === "abt" && await handleLegacyCallbackDataInteraction(params.interaction, parsed.componentId)) return;\n'
            content = content[:entry_idx] + fastpath + content[entry_idx:]
            changes.append('pre-registry.abt.fastpath')

    if CONSUMED_NEEDLE not in content:
        modal_marker = '\tif (consumed.kind === "modal-trigger") {'
        modal_idx = content.find(modal_marker, marker_idx)
        if modal_idx != -1:
            intercept = '\tconst callbackData = typeof consumed.callbackData === "string" ? consumed.callbackData.trim() : "";\n\tif (callbackData && await handleLegacyCallbackDataInteraction(params.interaction, callbackData)) return;\n'
            content = content[:modal_idx] + intercept + content[modal_idx:]
            changes.append('post-consume.callback.intercept')

    if content != original:
        write_text(path, content)

    ok = HELPER_NEEDLE in content and FASTPATH_NEEDLE in content and CONSUMED_NEEDLE in content
    return {'path': str(path), 'changed': bool(changes), 'changes': changes, 'ok': ok}


def patch_sender_file(path: Path) -> dict:
    if not path.exists():
        return {'path': str(path), 'changed': False, 'changes': [], 'ok': True, 'reason': 'missing optional sender file'}
    content = read_text(path)
    original = content
    changes = []

    if SENDER_REUSABLE_NEEDLE not in content:
        content, changed = replace_once(content, SENDER_COMPONENTS_OLD, SENDER_COMPONENTS_NEW)
        if changed:
            changes.append('components.reusable.true')

    if content != original:
        write_text(path, content)

    ok = SENDER_REUSABLE_NEEDLE in content
    return {'path': str(path), 'changed': bool(changes), 'changes': changes, 'ok': ok}


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True)


def restart_gateway(service_name: str) -> dict:
    restart = run(['systemctl', '--user', 'restart', service_name])
    active = run(['systemctl', '--user', 'is-active', service_name])
    status = run(['systemctl', '--user', 'status', service_name, '--no-pager'])
    return {
        'restartReturnCode': restart.returncode,
        'restartStdout': restart.stdout.strip(),
        'restartStderr': restart.stderr.strip(),
        'isActive': active.stdout.strip(),
        'statusSnippet': '\n'.join(status.stdout.splitlines()[:12]).strip(),
        'ok': restart.returncode == 0 and active.stdout.strip() == 'active',
    }


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Repatch OpenClaw Discord button runtime and sender paths.')
    p.add_argument('--workspace', type=Path, default=Path.cwd(), help='Workspace root (default: current working directory).')
    p.add_argument('--dist-root', type=Path, default=DEFAULT_DIST, help='Path to OpenClaw dist/ directory.')
    p.add_argument('--cache-path', type=Path, default=None, help='Override callback detail cache JSON path.')
    p.add_argument('--sender-file', action='append', default=[], help='Optional sender shell script to patch. Repeatable.')
    p.add_argument('--service-name', default='openclaw-gateway.service', help='systemd --user service to restart.')
    p.add_argument('--verify-only', action='store_true', help='Verify/patch files but skip gateway restart.')
    p.add_argument('--restart', action='store_true', help='Hard restart systemd user service after patching.')
    return p.parse_args(list(argv))


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)
    workspace = args.workspace.resolve()
    dist = args.dist_root.expanduser().resolve()
    cache_path = args.cache_path.expanduser().resolve() if args.cache_path else (workspace / 'memory/autobet-detail-cache.json')
    sender_files = [Path(p).expanduser().resolve() for p in args.sender_file] if args.sender_file else [
        workspace / 'scripts/cron-phase1/btc-eth-15m-auto.sh',
        workspace / 'scripts/cron-phase1/btc-5m-auto.sh',
    ]

    send_files = collect_send_files(dist)
    reply_files = collect_reply_files(dist)

    send_results = [patch_send_file(path) for path in send_files]
    reply_results = [patch_reply_file(path, cache_path) for path in reply_files]
    sender_results = [patch_sender_file(path) for path in sender_files]

    all_ok = all(item.get('ok') for item in [*send_results, *reply_results, *sender_results])
    changed_files = [r['path'] for r in [*send_results, *reply_results, *sender_results] if r.get('changed')]

    restart_result = None
    if args.restart and not args.verify_only:
        restart_result = restart_gateway(args.service_name)
        all_ok = all_ok and restart_result.get('ok', False)

    summary = {
        'ok': all_ok,
        'workspace': str(workspace),
        'distRoot': str(dist),
        'cachePath': str(cache_path),
        'sendFiles': send_results,
        'replyFiles': reply_results,
        'senderFiles': sender_results,
        'changedFiles': changed_files,
        'restart': restart_result,
        'notes': [
            'Old Discord messages created before sender/runtime fixes may still need resend.',
            'Use --restart after OpenClaw updates or dist rebuilds so the gateway loads the new code.',
        ],
    }

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if all_ok else 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
