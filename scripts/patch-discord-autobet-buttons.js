#!/usr/bin/env node
const path = require('path');
const { spawnSync } = require('child_process');
const target = path.resolve(__dirname, '..', 'skill', 'discord-button-repatch', 'scripts', 'repatch_discord_buttons.py');
const result = spawnSync('python3', [target, ...process.argv.slice(2)], { stdio: 'inherit' });
if (result.error) throw result.error;
process.exit(result.status ?? 0);
