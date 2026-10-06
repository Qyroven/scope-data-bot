#!/bin/sh
# Scope -> source discovery -> crawl -> parse/check/save -> chunks -> embeddings -> LLM evidence package.
# ./run-data.sh --scope 'Phạm vi dữ liệu cần thu thập'
# ./run-data.sh --from-run bot-runs/<id>  # Resume a saved crawl, no repeated search.
set -eu
BOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ ! -x "$BOT_DIR/.venv/bin/python" ]; then
    python3 -m venv "$BOT_DIR/.venv"
fi
if ! "$BOT_DIR/.venv/bin/python" -c 'import tiktoken, trafilatura, pypdf, lxml' >/dev/null 2>&1; then
    "$BOT_DIR/.venv/bin/python" -m pip install -r "$BOT_DIR/requirements.txt"
fi
exec "$BOT_DIR/.venv/bin/python" "$BOT_DIR/data_bot.py" "$@"
