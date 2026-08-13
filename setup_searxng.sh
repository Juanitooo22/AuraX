#!/bin/bash
echo "🔍 Instalando SearXNG..."

# Clonar SearXNG
cd /workspace && git clone https://github.com/searxng/searxng.git
cd /workspace/searxng

# Instalar dependencias
pip install msgspec --break-system-packages
pip install -r requirements.txt --break-system-packages

# Configurar settings
mkdir -p /etc/searxng
cp searx/settings.yml /etc/searxng/settings.yml

# Cambiar secret key
sed -i 's/ultrasecretkey/aurax_secret_2026_juanito/' /etc/searxng/settings.yml

# Habilitar formato JSON
python3 -c "
content = open('/etc/searxng/settings.yml').read()
content = content.replace('  formats:\n    - html', '  formats:\n    - html\n    - json')
open('/etc/searxng/settings.yml', 'w').write(content)
print('OK')
"

# Cambiar bind address
sed -i 's/bind_address: "127.0.0.1"/bind_address: "0.0.0.0"/' /etc/searxng/settings.yml

# Arrancar SearXNG
SEARXNG_SETTINGS_PATH=/etc/searxng/settings.yml python -m searx.webapp > /tmp/searxng.log 2>&1 &
sleep 5

# Verificar
curl -s "http://localhost:8888/search?q=test&format=json" | python3 -c "import sys,json; d=json.load(sys.stdin); print('✅ SearXNG funcionando:', d['results'][0]['title'])" 2>/dev/null || echo "❌ SearXNG falló - revisa /tmp/searxng.log"
