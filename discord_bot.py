import discord
import requests
import asyncio
from concurrent.futures import ThreadPoolExecutor
_executor = ThreadPoolExecutor(max_workers=4)
import os
import time
import base64
import re
import io
import json
from dotenv import load_dotenv

load_dotenv('/workspace/AuraX/.env')

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
AURAX_URL = 'http://localhost:5000/chat'
GENERATE_FILE_URL = 'http://localhost:5000/generate-file'
HISTORY_FILE = '/workspace/AuraX/discord_history.json'

def load_history():
    try:
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_history(data):
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f'Error guardando historial: {e}')
    # Sync a Drive cada 10 mensajes
    total = sum(len(v) for v in data.values())
    if total % 3 == 0:
        try:
            import subprocess
            subprocess.Popen(['rclone', 'copy', HISTORY_FILE, 'drive:AuraX-Historial/'], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f'Sync Drive: {total} mensajes')
        except Exception as re:
            print(f'Error sync Drive: {re}')

thread_histories = load_history()
SUPPORTED_EXTENSIONS = ['.pdf', '.txt', '.docx', '.jpg', '.jpeg', '.png', '.gif', '.webp']

def parse_attachment_block(text):
    match = re.search(r'\[ARCHIVO:([^:\]]+):([^:\]]+):([\s\S]*?)\]\s*$', text)
    if not match:
        return text, None
    file_type, file_name, content = match.groups()
    clean_text = text[:match.start()].strip()
    return clean_text, {'type': file_type, 'name': file_name, 'content': content}

def parse_image_block(text):
    match = re.search(r'\[IMAGEN:([^\]]+)\]\s*$', text)
    if not match:
        return text, None
    prompt = match.group(1)
    clean_text = text[:match.start()].strip()
    return clean_text, prompt

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'AuraX bot conectado como {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if not (client.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel)):
        return

    text = message.content.replace(f'<@{client.user.id}>', '').strip()
    user_id = str(message.author.id)
    username = message.author.display_name

    file_data = None
    file_name = None
    file_type = None

    if message.attachments:
        attachment = message.attachments[0]
        ext = os.path.splitext(attachment.filename)[1].lower()
        if ext in SUPPORTED_EXTENSIONS:
            try:
                file_bytes = await attachment.read()
                file_data = base64.b64encode(file_bytes).decode('utf-8')
                file_name = attachment.filename
                type_map = {'.jpg':'image/jpeg', '.jpeg':'image/jpeg', '.png':'image/png',
                           '.gif':'image/gif', '.webp':'image/webp', '.pdf':'application/pdf',
                           '.txt':'text/plain', '.docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}
                file_type = type_map.get(ext, '')
            except Exception as e:
                print(f'Error leyendo adjunto: {e}')

    if not text and not file_data:
        return

    if message.reference:
        thread_id = str(message.reference.message_id)
        if thread_id not in thread_histories:
            try:
                ref_msg = await message.channel.fetch_message(message.reference.message_id)
                thread_histories[thread_id] = [
                    {'role': 'assistant' if ref_msg.author == client.user else 'user',
                     'content': ref_msg.content}
                ]
            except:
                thread_histories[thread_id] = []
    else:
        thread_id = str(message.id)
        thread_histories[thread_id] = []

    async with message.channel.typing():
        try:
            loop = asyncio.get_event_loop()
            payload = {
                'mensaje': text or f'Analiza este archivo: {file_name}',
                'user_id': user_id,
                'chat_id': thread_id,
                'history': thread_histories.get(thread_id, [])
            }
            if file_data:
                payload['file_data'] = file_data
                payload['file_name'] = file_name
                payload['file_type'] = file_type

            res = await loop.run_in_executor(_executor, lambda: requests.post(AURAX_URL, json=payload, timeout=300))
            reply = res.json().get('respuesta', 'Error al responder')

            thread_histories.setdefault(thread_id, [])
            thread_histories[thread_id].append({'role': 'user', 'content': f"{username}: {text or file_name}", 'timestamp': int(time.time())})
            thread_histories[thread_id].append({'role': 'assistant', 'content': reply, 'timestamp': int(time.time())})

            if len(thread_histories[thread_id]) > 40:
                thread_histories[thread_id] = thread_histories[thread_id][-40:]

            save_history(thread_histories)

            clean_text, file_block = parse_attachment_block(reply)
            clean_text, image_prompt = parse_image_block(clean_text)

            if len(clean_text) > 2000:
                clean_text = clean_text[:1997] + '...'

            discord_files = []

            if file_block:
                try:
                    gen_res = requests.post(GENERATE_FILE_URL, json=file_block, timeout=30)
                    if gen_res.status_code == 200:
                        ext = file_block['type']
                        fname = file_block['name'] if '.' in file_block['name'] else f"{file_block['name']}.{ext}"
                        discord_files.append(discord.File(io.BytesIO(gen_res.content), filename=fname))
                except Exception as fe:
                    print(f'Error generando archivo: {fe}')

            if image_prompt:
                try:
                    img_url = f'https://image.pollinations.ai/prompt/{image_prompt}'
                    img_res = requests.get(img_url, timeout=30)
                    if img_res.status_code == 200:
                        discord_files.append(discord.File(io.BytesIO(img_res.content), filename='imagen.png'))
                except Exception as ie:
                    print(f'Error generando imagen: {ie}')

            if discord_files:
                await message.reply(clean_text or 'Aquí tienes:', files=discord_files)
            else:
                await message.reply(clean_text or reply)

        except Exception as e:
            await message.reply(f'Error: {str(e)}')

client.run(DISCORD_TOKEN)
