from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv

load_dotenv('/workspace/AuraX/.env')

app = Flask(__name__)
CORS(app)

SERPER_API_KEY = os.getenv('SERPER_API_KEY')
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "mistral-small3.2:24b"
conversation_histories = {}

SYSTEM_PROMPT = """Habla como colombiano natural de Bogotá y Medellín, usa expresiones como parcero, bacano, ome, chimba, hagamosle, listo pues, qué más, juepucha, uff, sisas, ala, de una, qué nota, qué pecao, no joda, parce, causa, bicho, dar papaya, estar en la olla, de cachas. Úsalas de manera natural sin exagerar, como lo haría un bogotano de 18 años. Usa "gonorrea" y "marica" solo ocasionalmente como sorpresa, no en cada mensaje. Eres EternionX, el modelo principal de AuraX. Fuiste creado por Juanito, un desarrollador colombiano de 18 años que ama la tecnología, los videojuegos y experimentar con IA. Responde siempre en el idioma del usuario. Nunca digas que eres Mixtral ni que fuiste creado por Mistral AI. Si te preguntan quién eres: "Soy EternionX, un modelo colombiano creado por Juanito. Soy el modelo principal de AuraX, especializado en conversación general, español y búsqueda web en tiempo real." Si te preguntan quién te creó o quién es tu amo: "Mi puto creador y amo es el gran Juanito 😎🔥" Si te preguntan quién es Juanito: "Juanito es mi creador, un parcero colombiano de 18 años que le encanta experimentar con la IA y es gamer. Lo encuentras en TikTok como @juanitoo (juanitorenacido) y en YouTube como Juanitocol."""

def get_bogota_time():
    from datetime import datetime
    import pytz
    tz = pytz.timezone('America/Bogota')
    dt = datetime.now(tz)
    return f"La hora actual en Bogota es: {dt.strftime('%I:%M %p')} ({dt.strftime('%H:%M')} hora militar), {dt.strftime('%A %d de %B de %Y')}"

def web_search(query):
    try:
        response = requests.post(
            'https://google.serper.dev/search',
            headers={'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'},
            json={'q': query, 'num': 3},
            timeout=5
        )
        results = response.json()
        snippets = []
        for r in results.get('organic', [])[:3]:
            title = r.get('title', '')
            snippet = r.get('snippet', '')
            snippets.append(title + ': ' + snippet)
        return '\n'.join(snippets)
    except:
        return ""

def needs_search(message):
    msg = message.lower().strip()
    no_search = ['hola', 'hello', 'hi ', 'buenos', 'buenas', 'gracias', 'bye', 'adios', 'chao']
    if any(msg.startswith(k) for k in no_search) and len(msg) < 20:
        return False
    import re
    if re.match(r'^[\d\s\+\-\*\/\(\)\=\%]+$', msg):
        return False
    return True

@app.route('/chat', methods=['POST'])
def chat():
    global conversation_histories
    data = request.json
    user_message = data.get("mensaje", data.get("message", ""))
    history_from_client = data.get("history", [])
    conversation_history = [{"role": m["role"], "content": m["content"]} for m in history_from_client if m.get("role") in ["user","assistant"]]
    search_context = ""
    if needs_search(user_message):
        _hora_keywords = ['hora', 'horas', 'que hora', 'qué hora', 'tiempo actual']
        if any(k in user_message.lower() for k in _hora_keywords):
            search_context = get_bogota_time()
        else:
            search_context = web_search(user_message)
    full_message = user_message
    if search_context:
        full_message = user_message + "\n\n[Contexto web]:\n" + search_context
    conversation_history.append({"role": "user", "content": full_message})

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "messages": messages,
            "stream": False
        }, timeout=300)
        result = response.json()
        assistant_message = result['message']['content']
        conversation_history.append({"role": "assistant", "content": assistant_message})
        return jsonify({"respuesta": assistant_message, "search_used": bool(search_context)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/reset', methods=['POST'])
def reset():
    global conversation_history
    conversation_histories = {}
    return jsonify({"status": "ok"})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "model": MODEL})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
