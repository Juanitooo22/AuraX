#!/usr/bin/env bash
set -Eeuo pipefail

echo "========================================"
echo "        AURAX FULL AUTO SETUP"
echo "========================================"

export DEBIAN_FRONTEND=noninteractive
export PIP_DISABLE_PIP_VERSION_CHECK=1

AURAX_DIR="/workspace/AuraX"
SEARX_DIR="/workspace/searxng"
GGUF_DIR="/root/.ollama/models/gguf"

# --------------------------------------------------
# 1. Dependencias básicas
# --------------------------------------------------

apt-get update -y

apt-get install -y \
    curl \
    git \
    wget \
    jq \
    openssl \
    ca-certificates \
    build-essential \
    python3-dev

python3 -m pip install -U pip

python3 -m pip install \
    flask \
    flask-cors \
    requests \
    python-dotenv \
    pytz \
    discord.py \
    huggingface_hub \
    hf_transfer \
    firebase-admin

# --------------------------------------------------
# NGROK
# --------------------------------------------------

if ! command -v ngrok >/dev/null 2>&1; then
    echo "[AuraX] Instalando ngrok..."
    cd /tmp
    curl -fsSL https://bin.ngrok.com/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz | tar -xz
    install -m 755 ngrok /usr/local/bin/ngrok
fi

# --------------------------------------------------
# 2. Ollama
# --------------------------------------------------

if ! command -v ollama >/dev/null 2>&1; then
    echo "[AuraX] Instalando Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

pkill -f '[o]llama serve' 2>/dev/null || true

echo "[AuraX] Iniciando Ollama..."

nohup env \
    OLLAMA_HOST=0.0.0.0:11434 \
    OLLAMA_MAX_LOADED_MODELS=1 \
    OLLAMA_NUM_PARALLEL=1 \
    OLLAMA_KEEP_ALIVE=5m \
    OLLAMA_FLASH_ATTENTION=1 \
    ollama serve \
    >/tmp/ollama.log 2>&1 &

for i in $(seq 1 30); do
    if curl -sf http://127.0.0.1:11434/api/tags >/dev/null; then
        break
    fi
    sleep 1
done

curl -sf http://127.0.0.1:11434/api/tags >/dev/null || {
    echo "ERROR: Ollama no arrancó."
    cat /tmp/ollama.log
    exit 1
}

mkdir -p "$GGUF_DIR"
mkdir -p /root/.ollama/models/blobs

# --------------------------------------------------
# 3. Descargar modelos
# --------------------------------------------------

cd "$GGUF_DIR"

GEMMA_FILE="gemma-4-12B-it-uncensored-heretic-Q4_K_M.gguf"
LUAU_FILE="Luau-Devstral-24B-Instruct-v0.1.i1-Q4_K_M.gguf"

if ! ollama list | grep -q '^gemma4-uncensored'; then

    echo "[AuraX] Descargando Gemma 4 12B..."

    hf download \
        llmfan46/gemma-4-12B-it-uncensored-heretic-GGUF \
        "$GEMMA_FILE" \
        --local-dir "$GGUF_DIR"

    echo "[AuraX] Importando Gemma en Ollama..."

    HASH="$(sha256sum "$GEMMA_FILE" | cut -d' ' -f1)"

    ln -f \
        "$GGUF_DIR/$GEMMA_FILE" \
        "/root/.ollama/models/blobs/sha256-$HASH"

    cat >/tmp/Modelfile-gemma <<EOF
FROM $GGUF_DIR/$GEMMA_FILE
EOF

    ollama create gemma4-uncensored -f /tmp/Modelfile-gemma

    rm -f "$GGUF_DIR/$GEMMA_FILE"

else
    echo "[AuraX] gemma4-uncensored ya existe."
fi


if ! ollama list | grep -q '^luau-coder'; then

    echo "[AuraX] Descargando Luau Coder 24B..."

    hf download \
        mradermacher/Luau-Devstral-24B-Instruct-v0.1-i1-GGUF \
        "$LUAU_FILE" \
        --local-dir "$GGUF_DIR"

    echo "[AuraX] Importando Luau Coder en Ollama..."

    HASH="$(sha256sum "$LUAU_FILE" | cut -d' ' -f1)"

    ln -f \
        "$GGUF_DIR/$LUAU_FILE" \
        "/root/.ollama/models/blobs/sha256-$HASH"

    cat >/tmp/Modelfile-luau <<EOF
FROM $GGUF_DIR/$LUAU_FILE
EOF

    ollama create luau-coder -f /tmp/Modelfile-luau

    rm -f "$GGUF_DIR/$LUAU_FILE"

else
    echo "[AuraX] luau-coder ya existe."
fi

# --------------------------------------------------
# 4. Sistema de cambio automático de modelos
# --------------------------------------------------

cat >/usr/local/bin/aurax-model <<'SWAP'
#!/usr/bin/env bash
set -e

case "${1:-}" in

    luau|roblox|coder)
        TARGET="luau-coder"
        ;;

    gemma|aurax)
        TARGET="gemma4-uncensored"
        ;;

    *)
        echo "Uso:"
        echo "  aurax-model luau"
        echo "  aurax-model gemma"
        exit 1
        ;;
esac

echo "Descargando modelos actuales de VRAM..."

ollama ps | awk 'NR>1 {print $1}' | while read -r MODEL; do
    [ -n "$MODEL" ] && ollama stop "$MODEL" >/dev/null 2>&1 || true
done

echo "Cargando $TARGET..."

curl -s \
    http://127.0.0.1:11434/api/generate \
    -d "{\"model\":\"$TARGET\",\"prompt\":\"\",\"stream\":false,\"keep_alive\":\"10m\"}" \
    >/dev/null

echo
echo "Modelo activo:"
ollama ps
SWAP

chmod +x /usr/local/bin/aurax-model

# --------------------------------------------------
# 5. SearXNG
# --------------------------------------------------

cd /workspace

if [ ! -d "$SEARX_DIR/.git" ]; then
    echo "[AuraX] Clonando SearXNG..."
    git clone https://github.com/searxng/searxng.git "$SEARX_DIR"
else
    echo "[AuraX] Actualizando SearXNG..."
    git -C "$SEARX_DIR" pull --ff-only || true
fi

cd "$SEARX_DIR"

python3 -m pip install msgspec
python3 -m pip install --no-build-isolation .

mkdir -p /etc/searxng

SECRET="$(openssl rand -hex 32)"

cat >/etc/searxng/settings.yml <<EOF
use_default_settings: true

server:
  secret_key: "$SECRET"
  bind_address: "0.0.0.0"
  port: 8888
  limiter: false

image_proxy: false

search:
  safe_search: 0
  default_lang: "es"
  formats:
    - html
    - json
EOF

pkill -f '[s]earx.webapp' 2>/dev/null || true

SEARXNG_SETTINGS_PATH=/etc/searxng/settings.yml \
nohup python3 -m searx.webapp \
>/tmp/searxng.log 2>&1 &

sleep 5

# --------------------------------------------------
# 6. AuraX
# --------------------------------------------------

cd /workspace

if [ ! -d "$AURAX_DIR/.git" ]; then

    git clone \
        -b discord-only \
        https://github.com/Juanitooo22/AuraX.git \
        "$AURAX_DIR"

else

    cd "$AURAX_DIR"

    git fetch origin discord-only || true
    git checkout discord-only || true
    git pull --ff-only origin discord-only || true

fi

cd "$AURAX_DIR"

# --------------------------------------------------
# 7. Secrets opcionales
# --------------------------------------------------

if [ -f /workspace/secrets.env ]; then
    set -a
    source /workspace/secrets.env
    set +a
fi

if [ -n "${NGROK_AUTHTOKEN:-}" ] && command -v ngrok >/dev/null 2>&1; then
    ngrok config add-authtoken "$NGROK_AUTHTOKEN" >/dev/null 2>&1
fi

touch .env
chmod 600 .env

grep -q '^SEARXNG_URL=' .env 2>/dev/null || \
    echo 'SEARXNG_URL=http://127.0.0.1:8888' >> .env

grep -q '^DISCORD_OWNER_ID=' .env 2>/dev/null || \
    echo 'DISCORD_OWNER_ID=1086360701632794666' >> .env

if [ -n "${DISCORD_TOKEN:-}" ]; then

    sed -i '/^DISCORD_TOKEN=/d' .env
    printf 'DISCORD_TOKEN=%s\n' "$DISCORD_TOKEN" >> .env

fi

# --------------------------------------------------
# 8. Limpiar procesos anteriores
# --------------------------------------------------

pkill -f '[p]ython3 servidor.py' 2>/dev/null || true
pkill -f '[p]ython3 discord_bot.py' 2>/dev/null || true

# --------------------------------------------------
# 9. Flask
# --------------------------------------------------

echo "[AuraX] Iniciando Flask..."

nohup python3 servidor.py \
    >/tmp/flask.log 2>&1 &

sleep 3

# --------------------------------------------------
# 10. Discord
# --------------------------------------------------

if [ -n "${DISCORD_TOKEN:-}" ]; then

    echo "[AuraX] Iniciando Discord bot..."

    nohup python3 discord_bot.py \
        >/tmp/bot.log 2>&1 &

else

    echo
    echo "AVISO: DISCORD_TOKEN no disponible."
    echo "AuraX funcionará, pero Discord no se inicia."

fi

# --------------------------------------------------
# 11. Script para reiniciar servicios
# --------------------------------------------------

# start_all.sh ya viene versionado en GitHub.
# NO regenerarlo aquí porque se perdería la versión completa.
chmod +x "$AURAX_DIR/start_all.sh"

# --------------------------------------------------
# 12. Gitignore
# --------------------------------------------------

touch "$AURAX_DIR/.gitignore"

for ENTRY in \
    ".env" \
    "secrets.env" \
    "__pycache__/" \
    "*.pyc"
do

    grep -qxF "$ENTRY" "$AURAX_DIR/.gitignore" || \
        echo "$ENTRY" >> "$AURAX_DIR/.gitignore"

done

# --------------------------------------------------
# 13. Estado final
# --------------------------------------------------

echo
echo "========================================"
echo "             AURAX LISTO"
echo "========================================"

echo
echo "MODELOS:"
ollama list

echo
echo "MODELO EN VRAM:"
ollama ps

echo
echo "OLLAMA:"
curl -sf http://127.0.0.1:11434/api/tags >/dev/null \
    && echo "OK - puerto 11434" \
    || echo "ERROR"

echo
echo "SEARXNG:"
curl -sf http://127.0.0.1:8888 >/dev/null \
    && echo "OK - puerto 8888" \
    || echo "Revisar /tmp/searxng.log"

echo
echo "FLASK:"
pgrep -af 'python3 servidor.py' || \
    echo "Revisar /tmp/flask.log"

echo
echo "DISCORD:"
pgrep -af 'python3 discord_bot.py' || \
    echo "No iniciado / falta token"

echo
echo "Cambiar modelo:"
echo "  aurax-model luau"
echo "  aurax-model gemma"

echo
echo "Reiniciar servicios:"
echo "  /workspace/AuraX/start_all.sh"

echo
echo "========================================"
