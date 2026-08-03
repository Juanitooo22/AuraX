#!/bin/bash
echo "🚀 Instalando AuraX..."

# Instalar Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Instalar ngrok
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc | tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | tee /etc/apt/sources.list.d/ngrok.list
apt-get update -q && apt-get install ngrok -y -q

# Instalar dependencias Python
pip install flask flask-cors requests python-dotenv pytz discord.py -q

# Configurar ngrok
ngrok config add-authtoken 3H3y2hxkYdtKYycg0UsEZgvNsZx_6XGAvCBG1X7kzkuxJu4x3

# Arrancar Ollama y descargar modelo
ollama serve &
sleep 5
ollama pull mistral-small3.2:24b

echo "✅ Setup completo! Crea el .env y corre: bash start.sh"
