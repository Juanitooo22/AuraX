#!/bin/bash
echo "🔥 Iniciando AuraX..."
ollama serve &
sleep 5
cd /workspace/AuraX && python servidor.py &
sleep 2
ngrok http 5000 --url=drained-expand-implosive.ngrok-free.dev &
sleep 2
cd /workspace/AuraX && python discord_bot.py &
echo "✅ AuraX listo!"
