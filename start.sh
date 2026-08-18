#!/bin/bash
echo "▶️ Arrancando AuraX..."
pkill ollama 2>/dev/null; sleep 1
OLLAMA_KEEP_ALIVE=-1 OLLAMA_NUM_PARALLEL=4 ollama serve > /tmp/ollama.log 2>&1 &
sleep 8
pkill -f searx.webapp 2>/dev/null; sleep 1
SEARXNG_SETTINGS_PATH=/etc/searxng/settings.yml python -m searx.webapp > /tmp/searxng.log 2>&1 &
sleep 5
curl -s "http://localhost:8888/search?q=test&format=json" | python3 -c "import sys,json; json.load(sys.stdin); print('✅ SearXNG OK')" 2>/dev/null || echo "⚠️ SearXNG falló"
pkill -f servidor.py 2>/dev/null; sleep 1
python /workspace/AuraX/servidor.py > /tmp/servidor.log 2>&1 &
sleep 3
pkill ngrok 2>/dev/null; sleep 1
ngrok http 5000 --url=drained-expand-implosive.ngrok-free.dev > /dev/null 2>&1 &
sleep 2
pkill -f discord_bot.py 2>/dev/null; sleep 1
python /workspace/AuraX/discord_bot.py > /tmp/bot.log 2>&1 &
sleep 3
# Restaurar historial de GitHub si no existe local
if [ ! -f /workspace/AuraX/discord_history.json ]; then
    echo "📥 Restaurando historial..."
    git -C /workspace/AuraX pull origin main 2>/dev/null
fi
echo "✅ AuraX corriendo!"
echo "Logs: /tmp/servidor.log | /tmp/bot.log | /tmp/searxng.log"
