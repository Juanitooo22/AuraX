#!/bin/bash
echo "🚀 Instalando AuraX..."

# Instalar Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Instalar ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok -y

# Instalar rclone
curl https://rclone.org/install.sh | sudo bash

# Instalar dependencias Python
pip install flask flask-cors requests python-dotenv pytz pymupdf python-docx openpyxl firebase-admin --break-system-packages

# Configurar ngrok
ngrok config add-authtoken 2uV9bYFJoT8RXfTGxjz2MCVMYTU_7d4XBbLN9x7PGEjnJtyHM

# Configurar rclone - copia el rclone.conf manualmente despues del setup
echo "⚠️  Recuerda copiar tu rclone.conf a ~/.config/rclone/rclone.conf"

# Iniciar Ollama
ollama serve > /tmp/ollama.log 2>&1 &
sleep 5

# Descargar modelos
ollama pull gemma3:27b
ollama pull hf.co/bartowski/Qwen2.5-Coder-14B-Instruct-abliterated-GGUF:Q4_K_M
ollama pull dolphin3:8b

echo "✅ Setup completo! Crea el .env y corre: bash start.sh"

# Descargar rclone.conf desde Gist privado
source .env 2>/dev/null || true
mkdir -p ~/.config/rclone
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/gists/$GIST_ID \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['files']['rclone.conf']['content'])" \
  > ~/.config/rclone/rclone.conf
echo "✅ rclone configurado"
