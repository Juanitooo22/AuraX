import discord
import requests
import re
import unicodedata
import asyncio

def normalizar(texto):
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto.lower().strip()

def encontrar_categoria(guild, nombre):
    n = normalizar(nombre)
    for cat in guild.categories:
        if n in normalizar(cat.name):
            return cat
    return None

def encontrar_canal(guild, nombre):
    n = normalizar(nombre)
    for ch in guild.channels:
        if n in normalizar(ch.name):
            return ch
    return None

def encontrar_rol(guild, nombre):
    n = normalizar(nombre)
    for r in guild.roles:
        if n in normalizar(r.name):
            return r
    return None

async def handle_admin_command(message, text, bot_token):
    guild = message.guild
    if not guild:
        return False
    cmd = text.strip()
    if not cmd.startswith('!'):
        return False
    parts = cmd.split()
    command = parts[0].lower()

    # CANALES
    if command == '!canales':
        lines = [f"**📋 Canales de {guild.name}:**\n"]
        sin_cat = [c for c in guild.channels if c.category is None and isinstance(c, discord.TextChannel)]
        if sin_cat:
            lines.append("**Sin categoría:**")
            for c in sin_cat:
                lines.append(f"  #{c.name}")
        for cat in guild.categories:
            lines.append(f"\n**{cat.name}:**")
            for c in cat.channels:
                tipo = "🔊" if isinstance(c, discord.VoiceChannel) else "#"
                lines.append(f"  {tipo} {c.name}")
        await message.reply("\n".join(lines)[:2000])
        return True

    if command == '!crear-canal':
        resto = cmd[len('!crear-canal'):].strip()
        m = re.match(r'(.+?)\s+(?:en\s+)?(.+)', resto)
        if m:
            cat = encontrar_categoria(guild, m.group(2).strip())
            ch = await guild.create_text_channel(m.group(1).strip(), category=cat)
            await message.reply(f"✅ Canal **#{ch.name}** creado" + (f" en **{cat.name}**" if cat else "") + ".")
        else:
            ch = await guild.create_text_channel(resto)
            await message.reply(f"✅ Canal **#{ch.name}** creado.")
        return True

    if command == '!eliminar-canal':
        nombre = cmd[len('!eliminar-canal'):].strip()
        ch = encontrar_canal(guild, nombre)
        if not ch:
            await message.reply(f"❌ No encontré el canal **{nombre}**.")
            return True
        nombre_ch = ch.name
        await ch.delete()
        await message.reply(f"✅ Canal **#{nombre_ch}** eliminado.")
        return True

    if command == '!renombrar-canal':
        resto = cmd[len('!renombrar-canal'):].strip()
        m = re.match(r'(.+?)\s+(?:a|como|->)\s+(.+)', resto)
        if not m:
            await message.reply("❌ Uso: `!renombrar-canal viejo -> nuevo`")
            return True
        ch = encontrar_canal(guild, m.group(1).strip())
        if not ch:
            await message.reply(f"❌ No encontré el canal **{m.group(1)}**.")
            return True
        await ch.edit(name=m.group(2).strip())
        await message.reply(f"✅ Canal renombrado a **#{m.group(2).strip()}**.")
        return True

    if command == '!mover-canal':
        resto = cmd[len('!mover-canal'):].strip()
        m = re.match(r'(.+?)\s+(?:a|->)\s+(.+)', resto)
        if not m:
            await message.reply("❌ Uso: `!mover-canal nombre -> categoria`")
            return True
        ch = encontrar_canal(guild, m.group(1).strip())
        cat = encontrar_categoria(guild, m.group(2).strip())
        if not ch:
            await message.reply(f"❌ No encontré el canal **{m.group(1)}**.")
            return True
        await ch.edit(category=cat)
        await message.reply(f"✅ Canal **#{ch.name}** movido a **{cat.name if cat else 'sin categoría'}**.")
        return True

    # CATEGORIAS
    if command == '!crear-categoria':
        nombre = cmd[len('!crear-categoria'):].strip()
        cat = await guild.create_category(nombre)
        await message.reply(f"✅ Categoría **{cat.name}** creada.")
        return True

    if command == '!eliminar-categoria':
        resto = cmd[len('!eliminar-categoria'):].strip()
        con_canales = '--con-canales' in resto
        nombre = resto.replace('--con-canales', '').strip()
        cat = encontrar_categoria(guild, nombre)
        if not cat:
            await message.reply(f"❌ No encontré la categoría **{nombre}**.")
            return True
        if con_canales:
            eliminados = []
            for ch in list(cat.channels):
                await ch.delete()
                eliminados.append(ch.name)
            await cat.delete()
            await message.reply(f"✅ Categoría **{cat.name}** y {len(eliminados)} canales eliminados.")
        else:
            if cat.channels:
                await message.reply(f"⚠️ La categoría tiene {len(cat.channels)} canales. Usa `--con-canales` para eliminar todo.")
            else:
                await cat.delete()
                await message.reply(f"✅ Categoría **{cat.name}** eliminada.")
        return True

    if command == '!renombrar-categoria':
        resto = cmd[len('!renombrar-categoria'):].strip()
        m = re.match(r'(.+?)\s+(?:a|como|->)\s+(.+)', resto)
        if not m:
            await message.reply("❌ Uso: `!renombrar-categoria vieja -> nueva`")
            return True
        cat = encontrar_categoria(guild, m.group(1).strip())
        if not cat:
            await message.reply(f"❌ No encontré la categoría **{m.group(1)}**.")
            return True
        await cat.edit(name=m.group(2).strip())
        await message.reply(f"✅ Categoría renombrada a **{m.group(2).strip()}**.")
        return True

    if command == '!eliminar-canales-categoria':
        nombre = cmd[len('!eliminar-canales-categoria'):].strip()
        cat = encontrar_categoria(guild, nombre)
        if not cat:
            await message.reply(f"❌ No encontré la categoría **{nombre}**.")
            return True
        eliminados = []
        for ch in list(cat.channels):
            await ch.delete()
            eliminados.append(ch.name)
        resp = f"✅ Eliminé {len(eliminados)} canales de **{cat.name}**"
        if eliminados:
            resp += ":\n" + "\n".join(f"- {n}" for n in eliminados)
        await message.reply(resp[:2000])
        return True

    # ROLES
    if command == '!roles':
        roles = [r for r in reversed(guild.roles) if r.name != '@everyone']
        lines = [f"**🎭 Roles ({len(roles)}):**\n"]
        for i, r in enumerate(roles, 1):
            color = f"#{r.color.value:06x}" if r.color.value else "sin color"
            lines.append(f"{i}. **{r.name}** — {color} — {len(r.members)} miembros")
        await message.reply("\n".join(lines)[:2000])
        return True

    if command == '!crear-rol':
        resto = cmd[len('!crear-rol'):].strip()
        color_match = re.search(r'#([0-9a-fA-F]{6})', resto)
        color = discord.Color(int(color_match.group(1), 16)) if color_match else discord.Color.default()
        nombre = re.sub(r'#[0-9a-fA-F]{6}', '', resto).strip()
        rol = await guild.create_role(name=nombre, color=color)
        await message.reply(f"✅ Rol **{rol.name}** creado.")
        return True

    if command == '!eliminar-rol':
        nombre = cmd[len('!eliminar-rol'):].strip()
        rol = encontrar_rol(guild, nombre)
        if not rol:
            await message.reply(f"❌ No encontré el rol **{nombre}**.")
            return True
        nombre_rol = rol.name
        await rol.delete()
        await message.reply(f"✅ Rol **{nombre_rol}** eliminado.")
        return True

    if command == '!renombrar-rol':
        resto = cmd[len('!renombrar-rol'):].strip()
        m = re.match(r'(.+?)\s+(?:a|como|->)\s+(.+)', resto)
        if not m:
            await message.reply("❌ Uso: `!renombrar-rol viejo -> nuevo`")
            return True
        rol = encontrar_rol(guild, m.group(1).strip())
        if not rol:
            await message.reply(f"❌ No encontré el rol **{m.group(1)}**.")
            return True
        await rol.edit(name=m.group(2).strip())
        await message.reply(f"✅ Rol renombrado a **{m.group(2).strip()}**.")
        return True

    if command == '!dar-rol':
        if not message.mentions:
            await message.reply("❌ Uso: `!dar-rol @usuario rol`")
            return True
        usuario = next((m for m in message.mentions if m.id != message.guild.me.id), None)
        if not usuario:
            await message.reply("❌ No encontré el usuario.")
            return True
        nombre_rol = re.sub(r'<@!?\d+>', '', cmd[len('!dar-rol'):]).strip()
        rol = encontrar_rol(guild, nombre_rol)
        if not rol:
            await message.reply(f"❌ No encontré el rol **{nombre_rol}**.")
            return True
        await usuario.add_roles(rol)
        await message.reply(f"✅ Rol **{rol.name}** asignado a **{usuario.display_name}**.")
        return True

    if command == '!quitar-rol':
        if not message.mentions:
            await message.reply("❌ Uso: `!quitar-rol @usuario rol`")
            return True
        usuario = next((m for m in message.mentions if m.id != message.guild.me.id), None)
        if not usuario:
            await message.reply("❌ No encontré el usuario.")
            return True
        nombre_rol = re.sub(r'<@!?\d+>', '', cmd[len('!quitar-rol'):]).strip()
        rol = encontrar_rol(guild, nombre_rol)
        if not rol:
            await message.reply(f"❌ No encontré el rol **{nombre_rol}**.")
            return True
        await usuario.remove_roles(rol)
        await message.reply(f"✅ Rol **{rol.name}** quitado a **{usuario.display_name}**.")
        return True

    # MIEMBROS
    if command == '!miembros':
        members = guild.members
        lines = [f"**👥 Miembros ({len(members)}):**\n"]
        for mb in sorted(members, key=lambda x: x.display_name.lower()):
            roles_str = ", ".join(r.name for r in mb.roles if r.name != '@everyone') or "sin roles"
            lines.append(f"- **{mb.display_name}** — {roles_str}")
        texto = "\n".join(lines)
        if len(texto) > 2000:
            texto = texto[:1950] + f"\n... ({len(members)} miembros total)"
        await message.reply(texto)
        return True

    if command == '!kick':
        print(f'KICK mentions: {message.mentions}')
        if not message.mentions:
            await message.reply("❌ Uso: `!kick @usuario razón`")
            return True
        usuario = next((m for m in message.mentions if m.id != message.guild.me.id), None)
        if not usuario:
            await message.reply('❌ No encontré el usuario.')
            return True
        razon = re.sub(r'<@!?\d+>', '', cmd[len('!kick'):]).strip() or "Sin razón"
        await message.guild.kick(usuario, reason=razon)
        await message.reply(f"✅ **{usuario.display_name}** expulsado. Razón: {razon}")
        return True

    if command == '!ban':
        if not message.mentions:
            await message.reply("❌ Uso: `!ban @usuario razón`")
            return True
        usuario = next((m for m in message.mentions if m.id != message.guild.me.id), None)
        if not usuario:
            await message.reply("❌ No encontré el usuario.")
            return True
        razon = re.sub(r'<@!?\d+>', '', cmd[len('!ban'):]).strip() or "Sin razón"
        await guild.ban(usuario, reason=razon)
        await message.reply(f"✅ **{usuario.display_name}** baneado. Razón: {razon}")
        return True

    if command == '!unban':
        user_id = cmd[len('!unban'):].strip()
        try:
            bans = [b async for b in guild.bans()]
            user = next((b.user for b in bans if str(b.user.id) == user_id), None)
            if user:
                await guild.unban(user)
                await message.reply(f"✅ **{user.name}** desbaneado.")
            else:
                await message.reply(f"❌ No encontré usuario baneado con ID **{user_id}**.")
        except Exception as e:
            await message.reply(f"❌ Error: {e}")
        return True

    if command == '!timeout':
        if not message.mentions:
            await message.reply("❌ Uso: `!timeout @usuario minutos`")
            return True
        usuario = next((m for m in message.mentions if m.id != message.guild.me.id), None)
        if not usuario:
            await message.reply("❌ No encontré el usuario.")
            return True
        resto = re.sub(r'<@!?\d+>', '', cmd[len('!timeout'):]).strip()
        try:
            minutos = int(resto.split()[0])
            from datetime import timedelta, timezone, datetime
            until = discord.utils.utcnow() + timedelta(minutes=minutos)
            await usuario.timeout(until)
            await message.reply(f"✅ **{usuario.display_name}** en timeout por {minutos} minutos.")
        except Exception as e:
            await message.reply(f"❌ Error: {e}")
        return True

    # SERVIDOR
    if command == '!info':
        g = guild
        lines = [
            f"**🏠 {g.name}**",
            f"ID: `{g.id}`",
            f"Dueño: {g.owner}",
            f"Miembros: {g.member_count}",
            f"Canales: {len(g.channels)}",
            f"Roles: {len(g.roles)}",
            f"Creado: {g.created_at.strftime('%d/%m/%Y')}",
            f"Boost level: {g.premium_tier} ({g.premium_subscription_count} boosts)",
            f"Emojis: {len(g.emojis)}/{g.emoji_limit}",
        ]
        await message.reply("\n".join(lines))
        return True

    if command == '!invitaciones':
        invites = await guild.invites()
        if not invites:
            await message.reply("No hay invitaciones activas.")
            return True
        lines = [f"**🔗 Invitaciones activas ({len(invites)}):**\n"]
        for inv in invites:
            uses = f"{inv.uses}/{inv.max_uses if inv.max_uses else '∞'}"
            lines.append(f"- `{inv.code}` — {inv.inviter} — {uses} usos — #{inv.channel.name}")
        await message.reply("\n".join(lines)[:2000])
        return True

    if command == '!crear-invitacion':
        partes = cmd[len('!crear-invitacion'):].strip().split()
        max_uses = int(partes[0]) if partes else 0
        max_age = int(partes[1]) * 3600 if len(partes) > 1 else 0
        inv = await message.channel.create_invite(max_uses=max_uses, max_age=max_age)
        await message.reply(f"✅ Invitación creada: `{inv.url}`")
        return True

    if command == '!emojis':
        emojis = guild.emojis
        if not emojis:
            await message.reply("Este servidor no tiene emojis personalizados.")
            return True
        lines = [f"**😀 Emojis ({len(emojis)}):**\n"]
        for e in emojis:
            anim = "🎬" if e.animated else "🖼️"
            lines.append(f"{anim} `:{e.name}:` — ID: `{e.id}`")
        await message.reply("\n".join(lines)[:2000])
        return True

    if command == '!auditoria':
        n = int(parts[1]) if len(parts) > 1 else 10
        lines = [f"**📋 Últimas {n} acciones:**\n"]
        async for entry in guild.audit_logs(limit=n):
            lines.append(f"- **{entry.action.name}** por {entry.user} — {entry.created_at.strftime('%d/%m %H:%M')}")
        await message.reply("\n".join(lines)[:2000])
        return True

    # ONBOARDING
    if command == '!onboarding-ver':
        headers = {'Authorization': f'Bot {bot_token}', 'Content-Type': 'application/json'}
        resp = requests.get(f'https://discord.com/api/v10/guilds/{guild.id}/onboarding', headers=headers)
        if resp.status_code != 200:
            await message.reply(f"❌ Error: {resp.status_code}")
            return True
        data = resp.json()
        lines = [
            f"**📋 Onboarding de {guild.name}:**",
            f"Estado: {'✅ Activo' if data.get('enabled') else '❌ Inactivo'}",
            f"Canales predeterminados: {len(data.get('default_channel_ids', []))}",
            f"Preguntas: {len(data.get('prompts', []))}\n"
        ]
        for i, p in enumerate(data.get('prompts', []), 1):
            lines.append(f"**Pregunta {i}:** {p.get('title', '')}")
            for opt in p.get('options', []):
                lines.append(f"  - {opt.get('title', '')}")
        await message.reply("\n".join(lines)[:2000])
        return True

    if command in ('!onboarding-activar', '!onboarding-desactivar'):
        enabled = command == '!onboarding-activar'
        headers = {'Authorization': f'Bot {bot_token}', 'Content-Type': 'application/json'}
        resp = requests.get(f'https://discord.com/api/v10/guilds/{guild.id}/onboarding', headers=headers)
        data = resp.json()
        data['enabled'] = enabled
        resp2 = requests.put(f'https://discord.com/api/v10/guilds/{guild.id}/onboarding', headers=headers, json=data)
        if resp2.status_code in (200, 204):
            await message.reply(f"✅ Onboarding {'activado' if enabled else 'desactivado'}.")
        else:
            await message.reply(f"❌ Error: {resp2.status_code} — {resp2.text[:200]}")
        return True

    if command == '!onboarding-pregunta':
        resto = cmd[len('!onboarding-pregunta'):].strip()
        titulo_match = re.match(r'"([^"]+)"\s*(.*)', resto)
        if not titulo_match:
            await message.reply('❌ Uso: `!onboarding-pregunta "¿Título?" Opcion1:rol1 Opcion2:rol2`')
            return True
        titulo = titulo_match.group(1)
        opciones_raw = titulo_match.group(2).strip().split()
        options = []
        for op in opciones_raw:
            if ':' in op:
                op_title, rol_nombre = op.split(':', 1)
                rol = encontrar_rol(guild, rol_nombre)
                options.append({"id": "0", "title": op_title, "description": None, "emoji_id": None, "emoji_name": None, "emoji_animated": False, "role_ids": [str(rol.id)] if rol else [], "channel_ids": []})
            else:
                options.append({"id": "0", "title": op, "description": None, "emoji_id": None, "emoji_name": None, "emoji_animated": False, "role_ids": [], "channel_ids": []})
        headers = {'Authorization': f'Bot {bot_token}', 'Content-Type': 'application/json'}
        resp = requests.get(f'https://discord.com/api/v10/guilds/{guild.id}/onboarding', headers=headers)
        data = resp.json()
        prompts = data.get('prompts', [])
        prompts.append({"id": "0", "title": titulo, "options": options, "single_select": False, "required": False, "in_onboarding": True, "type": 0})
        data['prompts'] = prompts
        data['enabled'] = True
        resp2 = requests.put(f'https://discord.com/api/v10/guilds/{guild.id}/onboarding', headers=headers, json=data)
        if resp2.status_code in (200, 204):
            await message.reply(f"✅ Pregunta **\"{titulo}\"** agregada con {len(options)} opciones.")
        else:
            await message.reply(f"❌ Error: {resp2.status_code} — {resp2.text[:300]}")
        return True

    if command == '!onboarding-limpiar':
        headers = {'Authorization': f'Bot {bot_token}', 'Content-Type': 'application/json'}
        resp = requests.get(f'https://discord.com/api/v10/guilds/{guild.id}/onboarding', headers=headers)
        data = resp.json()
        data['prompts'] = []
        resp2 = requests.put(f'https://discord.com/api/v10/guilds/{guild.id}/onboarding', headers=headers, json=data)
        if resp2.status_code in (200, 204):
            await message.reply("✅ Onboarding limpiado.")
        else:
            await message.reply(f"❌ Error: {resp2.status_code} — {resp2.text[:200]}")
        return True

    if command == '!onboarding-canal':
        nombre = cmd[len('!onboarding-canal'):].strip()
        ch = encontrar_canal(guild, nombre)
        if not ch:
            await message.reply(f"❌ No encontré el canal **{nombre}**.")
            return True
        headers = {'Authorization': f'Bot {bot_token}', 'Content-Type': 'application/json'}
        resp = requests.get(f'https://discord.com/api/v10/guilds/{guild.id}/onboarding', headers=headers)
        data = resp.json()
        ids = data.get('default_channel_ids', [])
        if str(ch.id) not in ids:
            ids.append(str(ch.id))
        data['default_channel_ids'] = ids
        resp2 = requests.put(f'https://discord.com/api/v10/guilds/{guild.id}/onboarding', headers=headers, json=data)
        if resp2.status_code in (200, 204):
            await message.reply(f"✅ Canal **#{ch.name}** agregado al onboarding.")
        else:
            await message.reply(f"❌ Error: {resp2.status_code} — {resp2.text[:200]}")
        return True

    # BUSCAR EMOJIS ANIMADOS
    if command == '!buscar-emoji':
        query = cmd[len('!buscar-emoji'):].strip()
        if not query:
            await message.reply("❌ Uso: `!buscar-emoji termino`")
            return True
        await message.reply(f"🔍 Buscando emojis animados para **{query}**...")
        results = []
        try:
            r = requests.get('https://emoji.gg/api/', timeout=10)
            if r.status_code == 200:
                q = normalizar(query)
                for e in r.json():
                    if q in normalizar(e.get('title', '')) and e.get('animated', False):
                        results.append(e)
                        if len(results) >= 8:
                            break
        except Exception as ex:
            print(f"Error emoji.gg: {ex}")
        if results:
            lines = [f"**🎬 Emojis animados para '{query}':**\n"]
            for e in results:
                lines.append(f"**{e['name']}** — `:{e['name']}:`")
                lines.append(f"{e.get('image', '')}\n")
            await message.reply("\n".join(lines)[:2000])
        else:
            await message.reply(f"No encontré resultados. Busca en: https://emoji.gg/?q={query.replace(' ', '+')}&animated=true")
        return True

    # AYUDA
    if command in ('!ayuda', '!help'):
        await message.reply("""**🤖 Comandos AuraX:**

**📁 Canales:** `!canales` `!crear-canal` `!eliminar-canal` `!renombrar-canal` `!mover-canal`
**📂 Categorías:** `!crear-categoria` `!eliminar-categoria` `!renombrar-categoria` `!eliminar-canales-categoria`
**🎭 Roles:** `!roles` `!crear-rol` `!eliminar-rol` `!renombrar-rol` `!dar-rol` `!quitar-rol`
**👥 Miembros:** `!miembros` `!kick` `!ban` `!unban` `!timeout`
**🏠 Servidor:** `!info` `!invitaciones` `!crear-invitacion` `!emojis` `!auditoria`
**🎉 Onboarding:** `!onboarding-ver` `!onboarding-activar` `!onboarding-desactivar` `!onboarding-pregunta` `!onboarding-canal` `!onboarding-limpiar`
**😀 Emojis:** `!buscar-emoji termino`""")
        return True

    return False
