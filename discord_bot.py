import discord
import requests
import os
from dotenv import load_dotenv

load_dotenv('/workspace/AuraX/.env')

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
AURAX_URL = 'http://localhost:5000/chat'

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

thread_histories = {}

def get_thread_id(message):
    if message.reference:
        return str(message.reference.message_id)
    return str(message.id)

@client.event
async def on_ready():
    print(f'AuraX bot conectado como {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if client.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        text = message.content.replace(f'<@{client.user.id}>', '').strip()
        if not text:
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
                res = requests.post(AURAX_URL, json={
                    'mensaje': text,
                    'user_id': str(message.author.id),
                    'chat_id': thread_id,
                    'history': thread_histories[thread_id]
                }, timeout=300)
                reply = res.json().get('respuesta', 'Error al responder')

                thread_histories[thread_id].append({'role': 'user', 'content': f"{message.author.display_name}: {text}"})
                thread_histories[thread_id].append({'role': 'assistant', 'content': reply})

                if len(thread_histories[thread_id]) > 20:
                    thread_histories[thread_id] = thread_histories[thread_id][-20:]

                if len(reply) > 2000:
                    reply = reply[:1997] + '...'
                await message.reply(reply)
            except Exception as e:
                await message.reply(f'Error: {str(e)}')

client.run(DISCORD_TOKEN)
