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

# Ngrok
pkill ngrok 2>/dev/null; sleep 1
nohup ngrok http 5000 --url=drained-expand-implosive.ngrok-free.dev > /tmp/ngrok.log 2>&1 &
echo "⏳ Esperando Ngrok..."
sleep 5
echo "✅ Ngrok listo"

# Discord bot
pkill -f discord_bot.py 2>/dev/null; sleep 1
cd /workspace/AuraX && nohup python discord_bot.py > /tmp/discord.log 2>&1 &
sleep 3
echo "✅ Discord bot listo"

echo "🚀 AuraX completamente listo!"
