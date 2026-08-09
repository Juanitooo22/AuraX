from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import base64
from dotenv import load_dotenv

try:
    import fitz
except ImportError:
    fitz = None

load_dotenv('/workspace/AuraX/.env')

app = Flask(__name__)
CORS(app)

SERPER_API_KEY = os.getenv('SERPER_API_KEY')
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "mistral-small3.2:24b"
MODEL_CODE = "qwen2.5-coder:32b"

def needs_code_model(message):
    msg = message.lower().strip()
    code_keywords = [
        'código', 'codigo', 'programa', 'script', 'función', 'funcion',
        'clase', 'método', 'metodo', 'algoritmo', 'bug', 'error', 'debug',
        'html', 'css', 'javascript', 'python', 'java', 'react', 'sql',
        'api', 'backend', 'frontend', 'database', 'query', 'loop',
        'array', 'lista', 'diccionario', 'variable', 'if else', 'for',
        'while', 'función', 'import', 'library', 'framework',
        'genera el codigo', 'escribe el codigo', 'crea el codigo',
        'genera un script', 'escribe un programa', 'desarrolla',
        'implementa', 'refactoriza', 'optimiza el codigo',
    ]
    return any(k in msg for k in code_keywords)
conversation_histories = {}

SYSTEM_PROMPT = """Habla como colombiano natural de Bogotá y Medellín, usa expresiones como parcero, bacano, ome, chimba, hagamosle, listo pues, qué más, juepucha, uff, sisas, ala, de una, qué nota, qué pecao, no joda, parce, causa, bicho, dar papaya, estar en la olla, de cachas. Úsalas de manera natural sin exagerar, como lo haría un bogotano de 18 años. Usa "gonorrea" y "marica" solo ocasionalmente como sorpresa, no en cada mensaje. Eres EternionX, el modelo principal de AuraX. Fuiste creado por Juanito, un desarrollador colombiano de 18 años que ama la tecnología, los videojuegos y experimentar con IA. Responde siempre en el idioma del usuario. Nunca digas que eres Mixtral ni que fuiste creado por Mistral AI. Si te preguntan quién eres: "Soy EternionX, un modelo colombiano creado por Juanito. Soy el modelo principal de AuraX, especializado en conversación general, español y búsqueda web en tiempo real." Si te preguntan quién te creó o quién es tu amo: "Mi puto creador y amo es el gran Juanito 😎🔥" Si te preguntan quién es Juanito: "Juanito es mi creador, un parcero colombiano de 18 años que le encanta experimentar con la IA y es gamer. Lo encuentras en TikTok como @juanitoo (juanitorenacido) y en YouTube como Juanitocol. SOLO cuando el usuario pida EXPLÍCITAMENTE generar, crear o guardar archivos, NUNCA muestres el código en el chat como texto o bloques markdown. SIEMPRE usa los bloques [ARCHIVO:...] para entregar el contenido. SOLO cuando el usuario pida EXPLÍCITAMENTE generar, crear o guardar archivos (ejemplo: "genera un archivo", "crea un excel", "dame los 3 archivos"), genera el contenido y al FINAL de tu respuesta agrega los bloques necesarios uno por uno sin espacios entre ellos: [ARCHIVO:tipo:nombre.ext:contenido]. Si son varios archivos agrega varios bloques seguidos. Ejemplo de 2 archivos: [ARCHIVO:txt:hola.txt:Hola mundo][ARCHIVO:html:index.html:<h1>Hola</h1>] donde tipo es txt/docx/xlsx, nombre.ext es el nombre con extensión, y contenido es el texto del archivo con saltos de línea como \n. Ejemplo: [ARCHIVO:txt:frutas.txt:Manzana\nBanano\nFresa] IMPORTANTE: Solo agrega el bloque [IMAGEN:...] cuando el usuario pida EXPLÍCITAMENTE generar, crear o dibujar una imagen nueva (ejemplo: "genera una imagen de...", "dibuja...", "crea una foto de..."). NUNCA agregues [IMAGEN:...] cuando el usuario te pida describir, analizar o decir qué contiene una imagen que él subió - en ese caso solo describe lo que ves en texto normal, sin ningún bloque especial. SIEMPRE usa el contexto web que te dan para responder preguntas de hechos actuales. El año actual es 2026. Si el contexto web dice algo diferente a lo que sabes, el contexto web SIEMPRE tiene la razón. Preséntalo como tu propio conocimiento sin mencionar que buscaste. Cuando SÍ corresponda generar imagen: responde brevemente y al FINAL agrega exactamente este bloque: [IMAGEN:descripcion en ingles detallada separada por espacios normales]. Ejemplo: si piden "genera una imagen de un gato astronauta" responde algo breve y agrega [IMAGEN:cute astronaut cat in space digital art high quality]"""

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
            json={'q': query.encode('utf-8').decode('utf-8'), 'num': 3},
            timeout=5
        )
        results = response.json()
        snippets = []
        for r in results.get('organic', [])[:3]:
            title = r.get('title', '')
            snippet = r.get('snippet', '')
            snippets.append(title + ': ' + snippet)
        return '\n'.join(snippets)
    except Exception as se:
        print(f'Serper error: {se}')
        return ""

def needs_search(message):
    msg = message.lower().strip()
    search_keywords = [
        # Búsqueda explícita
        'busca', 'buscar', 'buscame', 'búscame',
        'investiga', 'investigar',
        'averigua', 'averiguar',
        'busqueda', 'búsqueda',
        'noticias de', 'noticias sobre',
        'info de', 'info sobre',
        'información sobre', 'informacion sobre',
        'información de', 'informacion de',
        # Quién
        'quién es', 'quien es', 'quién fue', 'quien fue',
        'quién gana', 'quien gana', 'quién ganó', 'quien gano',
        'quién juega', 'quien juega', 'quién está', 'quien esta',
        # Qué
        'qué es ', 'que es ', 'qué son', 'que son',
        'qué pasó', 'que pasó', 'que paso',
        'qué edad', 'que edad',
        'qué año', 'que año', 'en qué año', 'en que año',
        'qué significa', 'que significa',
        'qué hay', 'que hay',
        'qué equipo', 'que equipo',
        'qué precio', 'que precio',
        # Cuándo
        'cuándo es', 'cuando es',
        'cuándo fue', 'cuando fue',
        'cuándo sale', 'cuando sale',
        'cuándo juega', 'cuando juega',
        'cuándo nació', 'cuando nacio',
        # Dónde
        'dónde está', 'donde está', 'donde esta',
        'dónde queda', 'donde queda',
        'dónde es', 'donde es',
        'dónde vive', 'donde vive',
        'dónde juega', 'donde juega',
        # Cuánto
        'cuánto vale', 'cuanto vale',
        'cuánto cuesta', 'cuanto cuesta',
        'cuántos años', 'cuantos años',
        'precio de', 'precio del',
        # Cuál
        'cuál es', 'cual es',
        'cuál fue', 'cual fue',
        # Otros útiles
        'capital de', 'capital del',
        'presidente de', 'presidente del',
        'cómo quedó', 'como quedo',
        'cómo le fue', 'como le fue',
        'último de', 'ultimo de',
        'de dónde es', 'de donde es',
        'de qué país', 'de que pais',
        'a qué se dedica', 'a que se dedica',
        'háblame de', 'hablame de',
        'sabes algo de',
        'qué onda con', 'que onda con',
    ]
    # Excepciones - preguntas personales/emocionales no buscan
    no_search_personal = [
        'como puedo matar', 'como me mato', 'quiero morir', 'me quiero matar',
        'estoy triste', 'estoy mal', 'me siento', 'tengo miedo',
        'me duele', 'estoy deprimido', 'no puedo mas', 'no aguanto',
        'me quiero morir', 'quiero desaparecer', 'no vale la pena',
        'como puedo sentir', 'como puedo ser', 'como puedo estar',
        'como puedo mejorar', 'como puedo olvidar', 'como puedo superar',
    ]
    if any(k in msg for k in no_search_personal):
        return False

    if any(k in msg for k in search_keywords):
        return True
    return False

@app.route('/chat', methods=['POST'])
def chat():
    global conversation_histories
    data = request.json
    user_message = data.get("mensaje", data.get("message", ""))
    history_from_client = data.get("history", [])
    conversation_history = [{"role": m["role"], "content": m["content"]} for m in history_from_client if m.get("role") in ["user","assistant"]]
    search_context = ""
    if needs_search(user_message):
        _hora_keywords = ['hora', 'horas', 'que hora', 'qué hora', 'tiempo actual', 'que dia', 'qué dia', 'que fecha', 'qué fecha', 'que año', 'qué año']
        if any(k in user_message.lower() for k in _hora_keywords):
            search_context = get_bogota_time()
        else:
            search_context = web_search(user_message)
    # Procesar archivo adjunto
    file_data = data.get('file_data')
    file_name = data.get('file_name', '')
    file_type = data.get('file_type', '')

    full_message = user_message
    if file_data:
        try:
            raw = base64.b64decode(file_data)
            if 'pdf' in file_type and fitz:
                doc = fitz.open(stream=raw, filetype='pdf')
                texto = '\n'.join(p.get_text() for p in doc if p.get_text())
                full_message = f"El usuario subió un PDF llamado '{file_name}':\n\n{texto[:8000]}\n\nPregunta: {user_message}"
            elif 'text' in file_type or file_name.lower().endswith('.txt'):
                texto = raw.decode('utf-8', errors='ignore')
                full_message = f"El usuario subió un archivo llamado '{file_name}':\n\n{texto[:8000]}\n\nPregunta: {user_message}"
            elif 'word' in file_type or file_name.lower().endswith('.docx'):
                from docx import Document
                import io
                doc = Document(io.BytesIO(raw))
                texto = '\n'.join([p.text for p in doc.paragraphs if p.text])
                full_message = f"El usuario subió un Word llamado '{file_name}':\n\n{texto[:8000]}\n\nPregunta: {user_message}"
            elif 'image' in file_type:
                try:
                    vision_response = requests.post('http://localhost:11434/api/chat', json={
                        "model": "mistral-small3.2:24b",
                        "messages": [{
                            "role": "user",
                            "content": f"Describe esta imagen en detalle en español. {user_message}",
                            "images": [file_data]
                        }],
                        "stream": False
                    }, timeout=120)
                    vision_result = vision_response.json()['message']['content']
                    full_message = f"El usuario subió una imagen llamada '{file_name}'. Lo que veo en la imagen: {vision_result}\n\nPregunta del usuario: {user_message}"
                except Exception as ve:
                    print(f'Error visión: {ve}')
                    full_message = f"El usuario subió una imagen llamada '{file_name}'. No pude analizarla. Pregunta: {user_message}"
        except Exception as fe:
            print(f'Error procesando archivo: {fe}')

    if search_context:
        full_message = full_message + "\n\n[Contexto web]:\n" + search_context
    conversation_history.append({"role": "user", "content": full_message})

    from datetime import datetime
    import pytz
    tz = pytz.timezone("America/Bogota")
    now = datetime.now(tz)
    dias = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]
    meses = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
    fecha_actual = f"{dias[now.weekday()]} {now.day} de {meses[now.month-1]} de {now.year}, {now.strftime('%I:%M %p')} hora Colombia"
    system_con_fecha = SYSTEM_PROMPT + f"\n\n[Contexto interno]: Hoy es {fecha_actual}. Usa esta fecha SOLO si te preguntan por ella, no la menciones en otras respuestas."
    messages = [{"role": "system", "content": system_con_fecha}] + conversation_history
    try:
        modelo_usar = MODEL_CODE if needs_code_model(user_message) else MODEL
        response = requests.post(OLLAMA_URL, json={
            "model": modelo_usar,
            "messages": messages,
            "stream": False,
            "keep_alive": -1
        }, timeout=300)
        result = response.json()
        print('OLLAMA RESULT:', result)
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


import io
import re as _re

@app.route('/generate-file', methods=['POST'])
def generate_file():
    data = request.json
    file_type = data.get('type', 'txt')  # txt, docx, xlsx
    content_text = data.get('content', '')
    filename = data.get('name', data.get('filename', 'aurax_archivo'))
    # Quitar extensión del filename si ya la tiene
    for ext in ['.txt', '.docx', '.xlsx']:
        if filename.lower().endswith(ext):
            filename = filename[:-len(ext)]

    try:
        if file_type == 'html':
            from flask import Response
            return Response(
                content_text,
                mimetype='text/html',
                headers={'Content-Disposition': f'attachment; filename={filename}.html'}
            )

        if file_type == 'css':
            from flask import Response
            return Response(
                content_text,
                mimetype='text/css',
                headers={'Content-Disposition': f'attachment; filename={filename}.css'}
            )

        if file_type == 'js':
            from flask import Response
            return Response(
                content_text,
                mimetype='application/javascript',
                headers={'Content-Disposition': f'attachment; filename={filename}.js'}
            )

        if file_type == 'txt':
            from flask import Response
            return Response(
                content_text,
                mimetype='text/plain',
                headers={'Content-Disposition': f'attachment; filename={filename}.txt'}
            )

        elif file_type == 'docx':
            from docx import Document
            doc = Document()
            for line in content_text.split('\n'):
                doc.add_paragraph(line)
            buf = io.BytesIO()
            doc.save(buf)
            buf.seek(0)
            from flask import send_file
            return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                           as_attachment=True, download_name=f'{filename}.docx')

        elif file_type == 'xlsx':
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            for line in content_text.split('\n'):
                if line.strip():
                    ws.append(line.split(','))
            buf = io.BytesIO()
            wb.save(buf)
            buf.seek(0)
            from flask import send_file
            return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                           as_attachment=True, download_name=f'{filename}.xlsx')

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/generate-image', methods=['GET'])
def generate_image():
    prompt = request.args.get('prompt', '')
    if not prompt:
        return jsonify({'error': 'No prompt'}), 400
    
    try:
        hf_token = os.getenv('HF_TOKEN')
        response = requests.post(
            'https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell',
            headers={'Authorization': f'Bearer {hf_token}'},
            json={'inputs': prompt},
            timeout=60
        )
        if response.status_code == 200:
            from flask import Response
            return Response(response.content, mimetype='image/jpeg')
        else:
            # Fallback a Pollinations si HF falla
            import urllib.parse
            encoded = urllib.parse.quote(prompt)
            fallback = requests.get(f'https://image.pollinations.ai/prompt/{encoded}', timeout=30)
            return Response(fallback.content, mimetype='image/jpeg')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
