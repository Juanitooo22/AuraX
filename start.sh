#!/bin/bash
echo "🚀 Arrancando AuraX..."

# Dependencias
pip install flask flask-cors requests python-dotenv pytz discord.py --break-system-packages --ignore-installed -q

# Ollama
if ! command -v ollama &> /dev/null; then
    echo "📦 Instalando Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# rclone
if ! command -v rclone &> /dev/null; then
    echo "📦 Instalando rclone..."
    curl https://rclone.org/install.sh | bash
fi

# Restaurar config de rclone
mkdir -p ~/.config/rclone
cp /workspace/AuraX/rclone.conf ~/.config/rclone/rclone.conf

# Modelo desde Drive
ollama serve &> /tmp/ollama.log &
sleep 5

if ! ollama list | grep -q "gemma4-uncensored"; then
    echo "📥 Bajando modelo desde Drive..."
    mkdir -p /root/.ollama/models/gguf
    rclone copy gdrive:AuraX-Models/gemma-4-12B-it-uncensored-heretic-Q4_K_M.gguf /root/.ollama/models/gguf/ --progress
    cat > /tmp/Modelfile << 'MODELEOF'
FROM /root/.ollama/models/gguf/gemma-4-12B-it-uncensored-heretic-Q4_K_M.gguf
MODELEOF
    ollama create gemma4-uncensored -f /tmp/Modelfile
fi

# .env
if [ ! -f /workspace/AuraX/.env ]; then
    cat > /workspace/AuraX/.env << 'ENVEOF'
DISCORD_TOKEN=TU_DISCORD_TOKEN_AQUI
DISCORD_OWNER_ID=1086360701632794666
SEARXNG_URL=http://localhost:8888
ENVEOF
fi

# Flask y bot
echo "✅ Arrancando Flask y bot..."
cd /workspace/AuraX
python3 servidor.py &
sleep 2
python3 discord_bot.py &

echo "🔥 AuraX listo!"
