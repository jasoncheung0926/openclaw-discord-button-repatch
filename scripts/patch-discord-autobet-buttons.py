#!/usr/bin/env python3
from pathlib import Path
import os
import sys
TARGET = Path(__file__).resolve().parents[1] / 'skill' / 'discord-button-repatch' / 'scripts' / 'repatch_discord_buttons.py'
os.execvp('python3', ['python3', str(TARGET), *sys.argv[1:]])
