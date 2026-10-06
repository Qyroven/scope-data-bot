#!/bin/sh
set -eu
BOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ ! -x "$BOT_DIR/.venv/bin/python" ]; then
  python3 -m venv "$BOT_DIR/.venv"
  "$BOT_DIR/.venv/bin/python" -m pip install -r "$BOT_DIR/requirements.txt"
fi
exec "$BOT_DIR/.venv/bin/python" "$BOT_DIR/bot.py" "$@"
