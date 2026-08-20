#!/bin/bash
echo "▶️ Configurando SearXNG..."

if [ ! -d /workspace/searxng ]; then
    echo "📥 Clonando SearXNG..."
    git clone https://github.com/searxng/searxng /workspace/searxng
fi

cd /workspace/searxng
pip install msgspec -q --break-system-packages 2>/dev/null
pip install -r requirements.txt -q --break-system-packages 2>/dev/null

pkill -f searx.webapp 2>/dev/null; sleep 1
SEARXNG_SETTINGS_PATH=/etc/searxng/settings.yml python -m searx.webapp > /tmp/searxng.log 2>&1 &
sleep 5

curl -s "http://localhost:8888/search?q=test&format=json" | python3 -c "import sys,json; json.load(sys.stdin); print('✅ SearXNG OK')" 2>/dev/null || echo "❌ SearXNG falló — revisa /tmp/searxng.log"
