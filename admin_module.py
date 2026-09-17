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


    # EDITAR ROL (color, nombre)
    if command == '!editar-rol':
        # !editar-rol nombre #color
        resto = cmd[len('!editar-rol'):].strip()
        color_match = re.search(r'#([0-9a-fA-F]{6})', resto)
        nombre_match = re.match(r'(.+?)(?:\s+#[0-9a-fA-F]{6})?$', resto)
        rol = encontrar_rol(guild, nombre_match.group(1).strip() if nombre_match else resto)
        if not rol:
            await message.reply(f"❌ No encontré el rol **{resto}**.")
            return True
        kwargs = {}
        if color_match:
            kwargs['color'] = discord.Color(int(color_match.group(1), 16))
        if kwargs:
            await rol.edit(**kwargs)
            await message.reply(f"✅ Rol **{rol.name}** editado.")
        else:
            await message.reply("❌ Especifica qué editar: `!editar-rol nombre #color`")
        return True

    # PERMISOS DE ROL
    if command == '!permiso-rol':
        # !permiso-rol nombre-rol +permiso o -permiso
        resto = cmd[len('!permiso-rol'):].strip()
        m = re.match(r'(.+?)\s+([+-])(\S+)', resto)
        if not m:
            await message.reply("❌ Uso: `!permiso-rol nombre-rol +permiso` o `-permiso`")
            return True
        nombre_rol, accion, permiso = m.group(1).strip(), m.group(2), m.group(3).strip()
        rol = encontrar_rol(guild, nombre_rol)
        if not rol:
            await message.reply(f"❌ No encontré el rol **{nombre_rol}**.")
            return True
        PERMISOS_MAP = {
            'ver_canales': 'view_channel', 'gestionar_canales': 'manage_channels',
            'gestionar_roles': 'manage_roles', 'crear_expresiones': 'create_expressions',
            'gestionar_expresiones': 'manage_expressions', 'ver_auditoria': 'view_audit_log',
            'gestionar_webhooks': 'manage_webhooks', 'gestionar_servidor': 'manage_guild',
            'crear_invitacion': 'create_instant_invite', 'cambiar_apodo': 'change_nickname',
            'gestionar_apodos': 'manage_nicknames', 'expulsar': 'kick_members',
            'banear': 'ban_members', 'aislar': 'moderate_members',
            'enviar_mensajes': 'send_messages', 'enviar_en_hilos': 'send_messages_in_threads',
            'crear_hilos': 'create_public_threads', 'embeber_links': 'embed_links',
            'adjuntar_archivos': 'attach_files', 'añadir_reacciones': 'add_reactions',
            'emojis_externos': 'use_external_emojis', 'stickers_externos': 'use_external_stickers',
            'mencionar_everyone': 'mention_everyone', 'gestionar_mensajes': 'manage_messages',
            'ver_historial': 'read_message_history', 'conectar': 'connect',
            'hablar': 'speak', 'silenciar': 'mute_members', 'ensordecer': 'deafen_members',
            'mover_miembros': 'move_members', 'administrador': 'administrator',
            # aliases cortos
            'admin': 'administrator', 'kick': 'kick_members', 'ban': 'ban_members',
        }
        perm_key = PERMISOS_MAP.get(normalizar(permiso).replace(' ', '_'), normalizar(permiso).replace(' ', '_'))
        perms = rol.permissions
        try:
            current = discord.Permissions(**{perm_key: accion == '+'})
            new_perms = discord.Permissions(rol.permissions.value)
            setattr(new_perms, perm_key, accion == '+')
            await rol.edit(permissions=new_perms)
            estado = "activado ✅" if accion == '+' else "desactivado ❌"
            await message.reply(f"Permiso **{permiso}** {estado} para el rol **{rol.name}**.")
        except AttributeError:
            await message.reply(f"❌ Permiso **{permiso}** no reconocido.")
        except Exception as e:
            await message.reply(f"❌ Error: {e}")
        return True

    # PERMISOS DE CANAL POR ROL
    if command == '!permiso-canal':
        # !permiso-canal nombre-canal @rol +permiso
        resto = cmd[len('!permiso-canal'):].strip()
        m = re.match(r'(.+?)\s+<@&?(\d+)>\s+([+-])(\S+)', resto)
        if not m:
            await message.reply("❌ Uso: `!permiso-canal nombre-canal @rol +permiso`")
            return True
        nombre_canal, rol_id, accion, permiso = m.group(1).strip(), int(m.group(2)), m.group(3), m.group(4).strip()
        ch = encontrar_canal(guild, nombre_canal)
        rol = guild.get_role(rol_id)
        if not ch or not rol:
            await message.reply(f"❌ No encontré canal o rol.")
            return True
        overwrite = ch.overwrites_for(rol)
        PERMISOS_MAP = {
            'ver_canal': 'view_channel', 'enviar_mensajes': 'send_messages',
            'leer_historial': 'read_message_history', 'adjuntar': 'attach_files',
            'embeber': 'embed_links', 'mencionar_everyone': 'mention_everyone',
            'gestionar_mensajes': 'manage_messages', 'añadir_reacciones': 'add_reactions',
            'conectar': 'connect', 'hablar': 'speak',
        }
        perm_key = PERMISOS_MAP.get(normalizar(permiso).replace(' ', '_'), normalizar(permiso).replace(' ', '_'))
        try:
            setattr(overwrite, perm_key, accion == '+')
            await ch.set_permissions(rol, overwrite=overwrite)
            estado = "activado ✅" if accion == '+' else "desactivado ❌"
            await message.reply(f"Permiso **{permiso}** {estado} para **{rol.name}** en **#{ch.name}**.")
        except Exception as e:
            await message.reply(f"❌ Error: {e}")
        return True

    # CANAL PRIVADO (solo un rol puede verlo)
    if command == '!canal-privado':
        # !canal-privado nombre-canal @rol
        resto = cmd[len('!canal-privado'):].strip()
        m = re.match(r'(.+?)\s+<@&?(\d+)>', resto)
        if not m:
            await message.reply("❌ Uso: `!canal-privado nombre-canal @rol`")
            return True
        ch = encontrar_canal(guild, m.group(1).strip())
        rol = guild.get_role(int(m.group(2)))
        if not ch or not rol:
            await message.reply("❌ No encontré canal o rol.")
            return True
        await ch.set_permissions(guild.default_role, view_channel=False)
        await ch.set_permissions(rol, view_channel=True)
        await message.reply(f"✅ Canal **#{ch.name}** ahora es privado — solo visible para **{rol.name}**.")
        return True

    # CANAL PÚBLICO
    if command == '!canal-publico':
        nombre = cmd[len('!canal-publico'):].strip()
        ch = encontrar_canal(guild, nombre)
        if not ch:
            await message.reply(f"❌ No encontré el canal **{nombre}**.")
            return True
        await ch.set_permissions(guild.default_role, view_channel=True)
        await message.reply(f"✅ Canal **#{ch.name}** ahora es público.")
        return True


    # ROLES VACÍOS (listar)
    if command == '!roles-vacios':
        roles_vacios = [r for r in guild.roles if len(r.members) == 0 and r.name != '@everyone' and not r.managed]
        if not roles_vacios:
            await message.reply("No hay roles vacíos.")
            return True
        lines = [f"**🗑️ Roles sin miembros ({len(roles_vacios)}):**\n"]
        for r in roles_vacios:
            lines.append(f"- {r.name}")
        await message.reply("\n".join(lines)[:2000])
        return True

    # LIMPIAR ROLES VACÍOS
    if command in ("!limpiar-roles", "!eliminar-roles-vacios"):
        roles_vacios = [r for r in guild.roles if len(r.members) == 0 and r.name != "@everyone" and not r.managed]
        if not roles_vacios:
            await message.reply("✅ No hay roles vacíos.")
            return True
        eliminados = []
        errores = []
        for r in roles_vacios:
            try:
                await r.delete()
                eliminados.append(r.name)
            except Exception as e:
                errores.append(r.name)
        resp = f"✅ Eliminé {len(eliminados)} roles vacíos:\n" + "\n".join(f"- {n}" for n in eliminados)
        if errores:
            resp += f"\n\n❌ No pude eliminar:\n" + "\n".join(errores)
        await message.reply(resp[:2000])
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

    # Si el comando empieza con ! pero no hizo match, usar IA para interpretarlo
    if cmd.startswith('!'):
        import requests as _req
        prompt = f"""Eres un intérprete de comandos de Discord. El usuario escribió: "{cmd}"
Convierte eso al comando exacto correcto de esta lista:
!canales, !crear-canal, !eliminar-canal, !renombrar-canal [viejo] -> [nuevo], !mover-canal [canal] -> [categoria]
!crear-categoria, !eliminar-categoria, !renombrar-categoria [viejo] -> [nuevo], !eliminar-canales-categoria
!roles, !crear-rol, !eliminar-rol, !renombrar-rol [viejo] -> [nuevo], !editar-rol [nombre] #color
!dar-rol @usuario rol, !quitar-rol @usuario rol
!permiso-rol [rol] +/-[permiso], !canal-privado [canal] @rol, !canal-publico [canal]
!miembros, !kick @usuario, !ban @usuario, !timeout @usuario minutos
!info, !invitaciones, !crear-invitacion, !emojis, !auditoria
!onboarding-ver, !onboarding-activar, !onboarding-desactivar, !onboarding-pregunta, !onboarding-canal, !onboarding-limpiar
!buscar-emoji [termino]

Responde SOLO con el comando exacto, nada más. Sin explicación."""
        try:
            res = _req.post('http://localhost:5000/chat', json={
                'mensaje': prompt,
                'es_owner': True,
                'user_id': '0',
                'username': 'system',
                'chat_id': 'cmd_interpreter',
                'history': []
            }, timeout=30)
            interpreted = res.json().get('respuesta', '').strip().split('\n')[0].strip()
            if interpreted.startswith('!'):
                return await handle_admin_command(message, interpreted, bot_token)
        except Exception as e:
            print(f"Error interpretando comando: {e}")
        return False


    # Si el comando empieza con ! pero no hizo match, usar IA para interpretarlo
    if cmd.startswith('!'):
        import requests as _req
        try:
            res = _req.post('http://localhost:5000/interpret-cmd', json={'cmd': cmd}, timeout=30)
            interpreted = res.json().get('cmd', '').strip()
            print(f"INTERPRET: {cmd} -> {interpreted}")
            if interpreted.startswith('!') and interpreted != cmd:
                return await handle_admin_command(message, interpreted, bot_token)
        except Exception as e:
            print(f"Error interpretando: {e}")
        return False


    return False
