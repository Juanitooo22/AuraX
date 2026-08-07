#!/bin/bash
echo "🔥 Iniciando AuraX..."

# Ollama
ollama serve &
echo "⏳ Esperando Ollama..."
until curl -s http://localhost:11434 > /dev/null 2>&1; do sleep 1; done
echo "✅ Ollama listo"

# Flask
cd /workspace/AuraX && python servidor.py &
echo "⏳ Esperando Flask..."
until curl -s http://localhost:5000/health > /dev/null 2>&1; do sleep 1; done
echo "✅ Flask listo"

# Matar ngrok anterior si existe
pkill ngrok 2>/dev/null
sleep 2

# Ngrok
ngrok http 5000 --url=drained-expand-implosive.ngrok-free.dev &
echo "⏳ Esperando Ngrok..."
until curl -s http://localhost:4040/api/tunnels | grep -q "public_url"; do sleep 1; done
echo "✅ Ngrok listo"

# Discord bot
pkill -f discord_bot.py 2>/dev/null
sleep 1
cd /workspace/AuraX && python discord_bot.py &
echo "⏳ Esperando Discord bot..."
sleep 5
echo "✅ Discord bot listo"

echo "🚀 AuraX completamente listo!"
