#!/bin/bash
echo "🚀 Configurando instancia nueva para AuraX..."

# Instalar Ollama si no está
if ! command -v ollama &> /dev/null; then
    echo "📥 Instalando Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Instalar ngrok si no está
if ! command -v ngrok &> /dev/null; then
    echo "📥 Instalando ngrok..."
    curl -Lo /tmp/ngrok.zip https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.zip
    unzip -o /tmp/ngrok.zip -d /usr/local/bin
    ngrok config add-authtoken 3H3y2hxkYdtKYycg0UsEZgvNsZx_6XGAvCBG1X7kzkuxJu4x3
fi

# Instalar dependencias Python
echo "📦 Instalando dependencias Python..."
pip install flask flask-cors requests python-dotenv edge-tts faster-whisper pymupdf python-docx openpyxl pytz kokoro-onnx soundfile discord.py -q --break-system-packages 2>/dev/null

# Descargar Kokoro si no existe
if [ ! -f /workspace/AuraX/kokoro-v1.0.onnx ]; then
    echo "📥 Descargando Kokoro TTS..."
    wget -q https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx -O /workspace/AuraX/kokoro-v1.0.onnx
    wget -q https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin -O /workspace/AuraX/voices-v1.0.bin
fi

# Git config
git config --global user.email "juanito@aurax.com"
git config --global user.name "Juanito"

echo "✅ Setup completo! Ahora corre: bash /workspace/AuraX/start.sh"
