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
        async with message.channel.typing():
            try:
                res = requests.post(AURAX_URL, json={
                    'mensaje': text,
                    'user_id': str(message.author.id),
                    'chat_id': str(message.channel.id),
                    'history': []
                }, timeout=300)
                reply = res.json().get('respuesta', 'Error al responder')
                if len(reply) > 2000:
                    reply = reply[:1997] + '...'
                await message.reply(reply)
            except Exception as e:
                await message.reply(f'Error: {str(e)}')

client.run(DISCORD_TOKEN)
