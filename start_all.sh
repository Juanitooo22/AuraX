#!/usr/bin/env bash

set -u

AURAX_DIR="/workspace/AuraX"
SEARX_DIR="/workspace/searxng"

cd "$AURAX_DIR"

# ============================================================
# SECRETOS
# ============================================================

if [ -f /workspace/secrets.env ]; then
    set -a
    source /workspace/secrets.env
    set +a
fi

# ============================================================
# OLLAMA
# ============================================================

echo "[AuraX] Iniciando Ollama..."

pkill -f '[o]llama serve' 2>/dev/null || true
sleep 1

nohup env \
    OLLAMA_HOST=0.0.0.0:11434 \
    OLLAMA_MAX_LOADED_MODELS=1 \
    OLLAMA_NUM_PARALLEL=1 \
    OLLAMA_KEEP_ALIVE=5m \
    OLLAMA_FLASH_ATTENTION=1 \
    ollama serve \
    >/workspace/ollama.log 2>&1 &

for i in $(seq 1 20); do
    if curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
        echo "[OK] Ollama :11434"
        break
    fi
    sleep 1
done

# ============================================================
# SEARXNG
# ============================================================

echo "[AuraX] Iniciando SearXNG..."

pkill -f '[s]earx.webapp' 2>/dev/null || true
sleep 1

cd "$SEARX_DIR"

SEARXNG_SETTINGS_PATH=/etc/searxng/settings.yml \
nohup python3 -m searx.webapp \
    >/workspace/searxng.log 2>&1 &

cd "$AURAX_DIR"

for i in $(seq 1 20); do
    if curl -fsS \
        "http://127.0.0.1:8888/search?q=test&format=json" \
        >/dev/null 2>&1; then
        echo "[OK] SearXNG :8888"
        break
    fi
    sleep 1
done

# ============================================================
# FLASK
# ============================================================

echo "[AuraX] Iniciando Flask..."

pkill -f '[p]ython3 servidor.py' 2>/dev/null || true
sleep 1

nohup python3 servidor.py \
    >/workspace/aurax_flask.log 2>&1 &

for i in $(seq 1 20); do
    if ss -ltn 2>/dev/null | grep -q ':5000 '; then
        echo "[OK] Flask :5000"
        break
    fi
    sleep 1
done

# ============================================================
# DISCORD
# ============================================================

if [ -n "${DISCORD_TOKEN:-}" ]; then

    echo "[AuraX] Iniciando Discord..."

    pkill -f '[p]ython3 discord_bot.py' 2>/dev/null || true
    sleep 1

    nohup python3 discord_bot.py \
        >/workspace/discord_bot.log 2>&1 &

    echo "[OK] Discord iniciado"

else

    echo "[WARN] DISCORD_TOKEN no encontrado"

fi

# ============================================================
# NGROK
# ============================================================

echo "[AuraX] Iniciando ngrok..."

pkill -f '[n]grok http' 2>/dev/null || true

if command -v ngrok >/dev/null 2>&1; then

    nohup ngrok http 5000 \
        >/workspace/ngrok.log 2>&1 &

    NGROK_URL=""

    for i in $(seq 1 20); do

        NGROK_URL="$(
            python3 - <<'PY'
import json
import urllib.request

try:
    with urllib.request.urlopen(
        "http://127.0.0.1:4040/api/tunnels",
        timeout=2
    ) as r:
        data = json.load(r)

    for tunnel in data.get("tunnels", []):
        url = tunnel.get("public_url", "")
        if url.startswith("https://"):
            print(url)
            break

except Exception:
    pass
PY
        )"

        if [ -n "$NGROK_URL" ]; then
            break
        fi

        sleep 1
    done

    if [ -n "$NGROK_URL" ]; then

        echo "[OK] ngrok -> $NGROK_URL"

        echo "$NGROK_URL" > /workspace/ngrok_url.txt

        echo "[AuraX] Probando /chat publico..."

        curl -si -X OPTIONS \
            "$NGROK_URL/chat" \
            -H "Origin: https://juanitooo22.github.io" \
            -H "Access-Control-Request-Method: POST" \
            -H "Access-Control-Request-Headers: content-type" \
            2>/dev/null |
            grep -Ei 'HTTP/|access-control-allow-origin' |
            head -5 || true

    else

        echo "[ERROR] ngrok no pudo crear el tunel"
        tail -20 /workspace/ngrok.log 2>/dev/null || true

    fi

else

    echo "[ERROR] ngrok no esta instalado"

fi

# ============================================================
# RESUMEN
# ============================================================

echo
echo "========================================"
echo "             AURAX INICIADO"
echo "========================================"

ss -ltnp 2>/dev/null |
    grep -E ':(11434|8888|5000)\b' || true

echo

if [ -f /workspace/ngrok_url.txt ]; then
    echo "Backend publico:"
    cat /workspace/ngrok_url.txt
fi

echo
echo "GitHub Pages:"
echo "https://juanitooo22.github.io/AuraX/"
echo "========================================"
