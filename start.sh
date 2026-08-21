#!/bin/bash
echo "▶️ Arrancando AuraX..."

# Ollama
pkill ollama 2>/dev/null; sleep 1
OLLAMA_KEEP_ALIVE=-1 OLLAMA_NUM_PARALLEL=4 ollama serve > /tmp/ollama.log 2>&1 &
sleep 8

# Modelos
ollama pull gemma4:12b 2>&1 | tail -1
ollama pull qwen2.5-coder:14b 2>&1 | tail -1
ollama pull dolphin3:8b 2>&1 | tail -1

# SearXNG
bash /workspace/AuraX/setup_searxng.sh

# Flask servidor
pkill -f servidor.py 2>/dev/null; sleep 1
python /workspace/AuraX/servidor.py > /tmp/servidor.log 2>&1 &
sleep 5

# Ngrok
pkill ngrok 2>/dev/null; sleep 1
nohup ngrok http 5000 --url=drained-expand-implosive.ngrok-free.dev > /dev/null 2>&1 &
sleep 3

# Discord bot
pkill -f discord_bot.py 2>/dev/null; sleep 1
python /workspace/AuraX/discord_bot.py > /tmp/bot.log 2>&1 &
sleep 3

echo "✅ AuraX corriendo!"
echo "Logs: /tmp/servidor.log | /tmp/bot.log | /tmp/ollama.log | /tmp/searxng.log"
