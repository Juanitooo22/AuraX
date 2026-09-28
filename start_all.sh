#!/usr/bin/env bash

cd /workspace/AuraX

if [ -f /workspace/secrets.env ]; then
    set -a
    source /workspace/secrets.env
    set +a
fi

pkill -f '[o]llama serve' 2>/dev/null || true

nohup env \
    OLLAMA_HOST=0.0.0.0:11434 \
    OLLAMA_MAX_LOADED_MODELS=1 \
    OLLAMA_NUM_PARALLEL=1 \
    OLLAMA_KEEP_ALIVE=5m \
    OLLAMA_FLASH_ATTENTION=1 \
    ollama serve \
    >/tmp/ollama.log 2>&1 &

sleep 3

pkill -f '[s]earx.webapp' 2>/dev/null || true

cd /workspace/searxng

SEARXNG_SETTINGS_PATH=/etc/searxng/settings.yml \
nohup python3 -m searx.webapp \
>/tmp/searxng.log 2>&1 &

cd /workspace/AuraX

pkill -f '[p]ython3 servidor.py' 2>/dev/null || true

nohup python3 servidor.py \
>/tmp/flask.log 2>&1 &

if [ -n "${DISCORD_TOKEN:-}" ]; then

    pkill -f '[p]ython3 discord_bot.py' 2>/dev/null || true

    nohup python3 discord_bot.py \
    >/tmp/bot.log 2>&1 &

fi

echo "AuraX iniciado."
