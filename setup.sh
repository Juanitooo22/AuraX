#!/bin/bash
echo "🚀 Iniciando setup de AuraX..."

AURAX_DIR="/workspace/AuraX"
SEARXNG_DIR="/workspace/searxng"

# ============ CONFIGURA ESTO ANTES DE CORRER ============
DISCORD_TOKEN="TU_DISCORD_TOKEN_AQUI"
GITHUB_TOKEN="TU_GITHUB_TOKEN_AQUI"
DISCORD_OWNER_ID="1086360701632794666"
SERPER_API_KEY="573f5e3abb5bab592e671afd580f1fbed3b81b87"
GIST_ID="d5b71eefb7402513a11b04ace28096b3"
# ========================================================

pip install flask flask-cors requests python-dotenv discord.py pynacl faster-whisper kokoro-onnx soundfile numpy pytz

cd /workspace
if [ ! -d "$AURAX_DIR" ]; then
    git clone https://$GITHUB_TOKEN@github.com/Juanitooo22/AuraX.git
else
    cd $AURAX_DIR && git pull
fi

cat > $AURAX_DIR/.env << ENVEOF
SERPER_API_KEY=$SERPER_API_KEY
DISCORD_TOKEN=$DISCORD_TOKEN
DISCORD_OWNER_ID=$DISCORD_OWNER_ID
GITHUB_TOKEN=$GITHUB_TOKEN
GIST_ID=$GIST_ID
ENVEOF

curl -fsSL https://ollama.com/install.sh | sh
OLLAMA_KEEP_ALIVE=-1 OLLAMA_NUM_PARALLEL=4 ollama serve > /tmp/ollama.log 2>&1 &
sleep 10
ollama pull gemma3:27b & ollama pull qwen2.5-coder:14b & ollama pull dolphin3:8b & wait

curl -Lo /tmp/ngrok.zip https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.zip
unzip -o /tmp/ngrok.zip -d /usr/local/bin/
ngrok config add-authtoken 3H3y2hxkYdtKYycg0UsEZgvNsZx_6XGAvCBG1X7kzkuxJu4x3

cd /workspace && [ ! -d "$SEARXNG_DIR" ] && git clone https://github.com/searxng/searxng.git
cd $SEARXNG_DIR && pip install msgspec && pip install -r requirements.txt
mkdir -p /etc/searxng && cp searx/settings.yml /etc/searxng/settings.yml
sed -i 's/ultrasecretkey/aurax_secret_2026_juanito/' /etc/searxng/settings.yml
sed -i 's/bind_address: "127.0.0.1"/bind_address: "0.0.0.0"/' /etc/searxng/settings.yml
python3 -c "
c=open('/etc/searxng/settings.yml').read()
if 'json' not in c.split('formats:')[1][:50]:
    c=c.replace('  formats:\n    - html','  formats:\n    - html\n    - json')
    open('/etc/searxng/settings.yml','w').write(c)
"
# Instalar searxng en el venv
cd $SEARXNG_DIR && pip install msgspec && pip install -r requirements.txt

echo "✅ Setup completo. Corre: bash /workspace/AuraX/start.sh"
