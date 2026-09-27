#!/bin/bash
set -x
if [ -f /workspace/secrets.env ]; then source /workspace/secrets.env; else echo "FALTA secrets.env"; exit 1; fi
pip install -q flask flask-cors requests python-dotenv pytz discord.py huggingface_hub --break-system-packages --ignore-installed
curl -fsSL https://ollama.com/install.sh | sh
pkill -f "ollama serve" || true
sleep 2
OLLAMA_HOST=0.0.0.0:11434 nohup ollama serve > /tmp/ollama.log 2>&1 &
sleep 8
mkdir -p /root/.config/rclone
printf '[gdrive]\ntype = drive\nscope = drive\ntoken = %s\n' "$RCLONE_TOKEN" > /root/.config/rclone/rclone.conf
mkdir -p /root/.ollama/models/gguf
cd /root/.ollama/models/gguf
rclone copy gdrive:AuraX-Models/gemma-4-12B-it-uncensored-heretic-Q4_K_M.gguf . --transfers 8 --checkers 16
if [ -f gemma-4-12B-it-uncensored-heretic-Q4_K_M.gguf ]; then
  H=$(sha256sum gemma-4-12B-it-uncensored-heretic-Q4_K_M.gguf | cut -d' ' -f1)
  ln -f gemma-4-12B-it-uncensored-heretic-Q4_K_M.gguf /root/.ollama/models/blobs/sha256-$H
  printf "FROM /root/.ollama/models/gguf/gemma-4-12B-it-uncensored-heretic-Q4_K_M.gguf\n" > /tmp/MF-g
  ollama create gemma4-uncensored -f /tmp/MF-g
  rm -f gemma-4-12B-it-uncensored-heretic-Q4_K_M.gguf
fi
export HF_HUB_ENABLE_HF_TRANSFER=1
hf download mradermacher/Luau-Devstral-24B-Instruct-v0.1-i1-GGUF Luau-Devstral-24B-Instruct-v0.1.i1-Q4_K_M.gguf --local-dir .
if [ -f Luau-Devstral-24B-Instruct-v0.1.i1-Q4_K_M.gguf ]; then
  H=$(sha256sum Luau-Devstral-24B-Instruct-v0.1.i1-Q4_K_M.gguf | cut -d' ' -f1)
  ln -f Luau-Devstral-24B-Instruct-v0.1.i1-Q4_K_M.gguf /root/.ollama/models/blobs/sha256-$H
  printf "FROM /root/.ollama/models/gguf/Luau-Devstral-24B-Instruct-v0.1.i1-Q4_K_M.gguf\n" > /tmp/MF-l
  ollama create luau-coder -f /tmp/MF-l
  rm -f Luau-Devstral-24B-Instruct-v0.1.i1-Q4_K_M.gguf
fi
cd /workspace
git clone https://github.com/searxng/searxng.git 2>/dev/null || (cd searxng && git pull)
cd searxng
pip install --break-system-packages -q msgspec
pip install --break-system-packages -q --no-build-isolation .
mkdir -p /etc/searxng
S=$(openssl rand -hex 32)
printf 'use_default_settings: true\nserver:\n  secret_key: "%s"\n  bind_address: "0.0.0.0"\n  port: 8888\n  limiter: false\nimage_proxy: false\nsearch:\n  safe_search: 0\n  default_lang: "es"\n  formats: [html, json]\n' "$S" > /etc/searxng/settings.yml
SEARXNG_SETTINGS_PATH=/etc/searxng/settings.yml nohup python3 -m searx.webapp > /tmp/searxng.log 2>&1 &
sleep 8
cd /workspace
git clone -b discord-only https://github.com/Juanitooo22/AuraX.git 2>/dev/null || (cd AuraX && git pull)
cd AuraX
printf 'DISCORD_TOKEN=%s\nDISCORD_OWNER_ID=1086360701632794666\nSEARXNG_URL=http://localhost:8888\n' "$DISCORD_TOKEN" > .env
nohup python3 servidor.py > /tmp/flask.log 2>&1 &
sleep 3
nohup python3 discord_bot.py > /tmp/bot.log 2>&1 &
echo "===== TODO LISTO ====="
ollama list
