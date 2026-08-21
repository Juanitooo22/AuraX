#!/bin/bash
echo "▶️ Configurando SearXNG..."

if [ ! -d /workspace/searxng ]; then
    echo "📥 Clonando SearXNG..."
    git clone https://github.com/searxng/searxng /workspace/searxng
fi

# Fixes en webapp.py
sed -i 's/from searx.botdetection import link_token, ProxyFix/# from searx.botdetection import link_token, ProxyFix/' /workspace/searxng/searx/webapp.py 2>/dev/null
sed -i 's/^app.wsgi_app = ProxyFix(app.wsgi_app)/# app.wsgi_app = ProxyFix(app.wsgi_app)/' /workspace/searxng/searx/webapp.py 2>/dev/null

# Config
mkdir -p /etc/searxng
if [ ! -f /etc/searxng/settings.yml ]; then
    cp /workspace/searxng/searx/settings.yml /etc/searxng/settings.yml 2>/dev/null || cp /workspace/searxng/searx/settings.defaults.yml /etc/searxng/settings.yml
fi

sed -i 's/ultrasecretkey/aurax_secret_key_2026/' /etc/searxng/settings.yml
grep -q "\- json" /etc/searxng/settings.yml || sed -i '/  formats:/a\    - json' /etc/searxng/settings.yml

cat > /etc/searxng/limiter.toml << 'TOML'
[botdetection.ip_limit]
link_token = false

[botdetection.ip_lists]
block_ip = []
pass_ip = ["127.0.0.1", "0.0.0.0/0"]
TOML

cd /workspace/searxng
pip install msgspec -q --break-system-packages 2>/dev/null
pip install -r requirements.txt -q --break-system-packages 2>/dev/null

pkill -f searx.webapp 2>/dev/null; sleep 2
SEARXNG_SETTINGS_PATH=/etc/searxng/settings.yml python -m searx.webapp > /tmp/searxng.log 2>&1 &
sleep 12

curl -s "http://localhost:8888/search?q=test&format=json" | python3 -c "import sys,json; json.load(sys.stdin); print('✅ SearXNG OK')" 2>/dev/null || echo "❌ SearXNG falló"
