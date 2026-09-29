# AuraX - Estado de automatización

Fecha del checkpoint: 2026-09-28

## REGLA PRINCIPAL

Todo arreglo que se haga manualmente debe terminar incorporado a los scripts.
Una instancia nueva de Vast no debe requerir repetir configuraciones manuales.

## WINDOWS - ESTADO PERSISTENTE

Estos elementos NO dependen de que sobreviva la instancia Vast:

- Repositorio AuraX:
  C:\Users\Juan G\Desktop\AuraX

- Secretos locales cifrados:
  C:\Users\Juan G\Desktop\AuraX-Local\secrets.clixml

- MCPBridge:
  C:\Users\Juan G\Desktop\MCPBridge

- Plugin Roblox:
  C:\Users\Juan G\AppData\Local\Roblox\Plugins\OllamaMCP.lua

- Clave SSH:
  C:\Users\Juan G\.ssh\id_ed25519

No guardar tokens ni secretos reales en GitHub.

## VAST / OLLAMA

Ollama remoto escucha en:

127.0.0.1:11434

Windows crea túnel:

localhost:11435 -> Vast 127.0.0.1:11434

El túnel fue comprobado con:

Test-NetConnection 127.0.0.1 -Port 11435

Resultado confirmado:

TcpTestSucceeded : True

Cline debe usar:

Base URL: http://localhost:11435
Model: luau-coder

## MODELOS

Modelos que setup_full.sh debe poder reconstruir:

- gemma4-uncensored
- luau-coder

Se utiliza un modelo cargado en VRAM a la vez.

Selector remoto:

aurax-model luau
aurax-model gemma

## SERVICIOS AURAX

setup_full.sh / start_all.sh deben dejar funcionando:

- Ollama : 11434
- SearXNG : 8888
- Flask AuraX : 5000
- Discord bot
- modelos de Ollama

## MCPBRIDGE

IMPORTANTE:

conectar.ps1 NO debe arrancar MCPBridge mediante "node index.js".

Cline ya tiene configurado el servidor MCP "roblox" y Cline debe ser
el UNICO proceso que arranque:

C:\Users\Juan G\Desktop\MCPBridge\mcp-server\index.js

Si conectar.ps1 también lo arranca, se crean dos MCPBridge distintos y
Cline puede consultar uno mientras Roblox está conectado al otro.

Puertos MCPBridge:

Roblox  : 127.0.0.1:7842
Blender : 127.0.0.1:7843

## ROBLOX

Plugin:

OllamaMCP.lua

Destino:

C:\Users\Juan G\AppData\Local\Roblox\Plugins\OllamaMCP.lua

El plugin original fue restaurado desde MCPBridge.

Prueba HTTP hecha DESDE ROBLOX STUDIO:

HttpService:GetAsync("http://127.0.0.1:7842/poll")

Resultado confirmado:

TEST MCP: true {"hasCommand":false}

Por lo tanto:

Roblox -> 127.0.0.1:7842 funciona.

El plugin mostró:

Starting bridge to:
http://127.0.0.1:7842

y dejó de mostrar ConnectFail después de restaurarlo.

## ULTIMO PROBLEMA ENCONTRADO

Había DOS MCPBridge ejecutándose.

Se encontró y cerró un proceso duplicado:

PID 28000

La solución permanente es:

- conectar.ps1 NO inicia MCPBridge.
- VS Code / Cline inicia MCPBridge.
- Roblox se conecta a ese mismo MCPBridge en 7842.

## PRUEBA QUE QUEDA PENDIENTE

Después de arrancar VS Code/Cline con un solo MCPBridge:

Cline -> studio_status

Debe indicar Roblox Studio conectado.

Después probar:

studio_execute_lua

creando un Part rojo llamado TestPart.

## AUTOMATIZACION TODAVIA PENDIENTE

crear.ps1 todavía debe mejorarse para hacer TODO esto automáticamente:

1. Buscar una oferta RTX 2080 Ti adecuada/barata en Vast.
2. Crear la instancia sin pedir OfferId.
3. Esperar a que SSH esté disponible.
4. Detectar IP y puerto SSH directos.
5. Ejecutar conectar.ps1 automáticamente.
6. Inyectar secretos desde secrets.clixml.
7. Instalar/restaurar AuraX.
8. Instalar Ollama si hace falta.
9. Descargar/importar los modelos.
10. Arrancar SearXNG, Flask y Discord.
11. Abrir el túnel 11435.
12. Verificar que Ollama responda.
13. Abrir VS Code.
14. Cline inicia su propio MCPBridge.
15. Roblox utiliza 127.0.0.1:7842.

OBJETIVO FINAL:

.\crear.ps1

y nada más.

No volver a introducir tokens.
No volver a escoger puertos.
No volver a editar scripts manualmente.
No volver a arrancar MCPBridge por separado.
