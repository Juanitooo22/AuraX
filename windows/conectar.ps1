param([int]$InstanceId = 0)

$ErrorActionPreference = "Stop"

$Base       = Join-Path $env:USERPROFILE "Desktop\AuraX-Local"
$SecretFile = Join-Path $Base "secrets.clixml"
$SshKey     = Join-Path $env:USERPROFILE ".ssh\id_ed25519"

New-Item -ItemType Directory -Force -Path $Base | Out-Null

function SecureToPlain([SecureString]$Secure) {
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Secure)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    }
}

if (!(Test-Path $SecretFile)) {
    Write-Host "Primera configuracion de Discord."
    $DiscordToken = Read-Host "Discord token" -AsSecureString

    [pscustomobject]@{
        DiscordToken   = $DiscordToken
        DiscordOwnerId = "1086360701632794666"
    } | Export-Clixml $SecretFile
}

Write-Host "[AuraX] Buscando Vast activa..."

$Instances = @(
    vastai show instances --raw |
    Out-String |
    ConvertFrom-Json
)

if ($InstanceId -gt 0) {
    $Inst = $Instances |
        Where-Object { [int]$_.id -eq $InstanceId } |
        Select-Object -First 1
}
else {
    $Inst = $Instances |
        Where-Object {
            $_.actual_status -eq "running" -or
            $_.cur_state -eq "running"
        } |
        Sort-Object { [int]$_.id } -Descending |
        Select-Object -First 1
}

if (!$Inst) {
    throw "No encontre ninguna instancia Vast.ai activa."
}

$IP = $Inst.public_ipaddr
if (!$IP) { $IP = $Inst.public_ip }

if (!$IP) {
    throw "No pude obtener la IP publica."
}

$PortInfo = $Inst.ports.'22/tcp'

if (!$PortInfo) {
    throw "No pude obtener el puerto SSH directo."
}

$Port = [int]$PortInfo[0].HostPort

Write-Host "[AuraX] Instancia: $($Inst.id)"
Write-Host "[AuraX] SSH: root@$IP`:$Port"

$Secrets = Import-Clixml $SecretFile
$Token = SecureToPlain $Secrets.DiscordToken

$NgrokToken = $null
if ($Secrets.PSObject.Properties.Name -contains "NgrokToken") {
    if ($Secrets.NgrokToken) {
        $NgrokToken = SecureToPlain $Secrets.NgrokToken
    }
}

$TmpSecrets = Join-Path $env:TEMP "aurax-secrets.env"

try {

    $EscapedToken = $Token.Replace("'", "'\''")

    $Content = @"
export DISCORD_TOKEN='$EscapedToken'
export DISCORD_OWNER_ID='1086360701632794666'
"@

    if ($NgrokToken) {
        $EscapedNgrokToken = $NgrokToken.Replace("'", "'\''")
        $Content += "`nexport NGROK_AUTHTOKEN='$EscapedNgrokToken'`n"
    }

    [IO.File]::WriteAllText(
        $TmpSecrets,
        $Content,
        (New-Object Text.UTF8Encoding($false))
    )

    Write-Host "[AuraX] Sincronizando servidor..."

    ssh `
        -i $SshKey `
        -p $Port `
        -o StrictHostKeyChecking=accept-new `
        "root@$IP" `
        "mkdir -p /workspace; if [ ! -d /workspace/AuraX/.git ]; then git clone -b discord-only https://github.com/Juanitooo22/AuraX.git /workspace/AuraX; else git -C /workspace/AuraX fetch origin discord-only || true; git -C /workspace/AuraX checkout discord-only || true; git -C /workspace/AuraX pull --ff-only origin discord-only || true; fi"

    scp `
        -i $SshKey `
        -P $Port `
        $TmpSecrets `
        "root@$IP`:/workspace/secrets.env"

    Write-Host "[AuraX] Arrancando servicios..."

    ssh `
        -i $SshKey `
        -p $Port `
        "root@$IP" `
        "chmod 600 /workspace/secrets.env; if [ -x /workspace/AuraX/start_all.sh ] && ollama list 2>/dev/null | grep -q luau-coder; then /workspace/AuraX/start_all.sh; else chmod +x /workspace/AuraX/setup_full.sh; bash /workspace/AuraX/setup_full.sh; fi"

    Write-Host "[AuraX] Abriendo tunel Ollama..."

    # Mata tuneles anteriores que estén ocupando 11435
    Get-NetTCPConnection -LocalPort 11435 -ErrorAction SilentlyContinue |
        ForEach-Object {
            Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
        }

    $TunnelArgs = "-N -i `"$SshKey`" -L 11435:127.0.0.1:11434 -p $Port -o StrictHostKeyChecking=accept-new -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -o IdentitiesOnly=yes root@$IP"

    $Tunnel = Start-Process `
        -FilePath "ssh.exe" `
        -ArgumentList $TunnelArgs `
        -WindowStyle Minimized `
        -PassThru

    $TunnelOK = $false

    for ($i = 0; $i -lt 20; $i++) {

        Start-Sleep -Seconds 1

        try {
            $tcp = New-Object System.Net.Sockets.TcpClient
            $tcp.Connect("127.0.0.1", 11435)
            $tcp.Close()

            $TunnelOK = $true
            break
        }
        catch {}
    }

    if (!$TunnelOK) {

        if ($Tunnel.HasExited) {
            throw "El tunel SSH fallo. Codigo: $($Tunnel.ExitCode)"
        }

        throw "No se pudo abrir localhost:11435."
    }

    Write-Host "[AuraX] Tunel Ollama: OK"

    $Models = Invoke-RestMethod `
        -Uri "http://127.0.0.1:11435/api/tags" `
        -TimeoutSec 10

    Write-Host "[AuraX] Ollama responde correctamente."
Write-Host "[AuraX] Abriendo VS Code..."
    Start-Process code

    Write-Host ""
    Write-Host "=============================="
    Write-Host "       AURAX CONECTADO"
    Write-Host "=============================="
    Write-Host "Ollama:    http://localhost:11435"
    Write-Host "MCP Roblox: http://127.0.0.1:7842"
    Write-Host "Vast:      $IP`:$Port"
    Write-Host "=============================="
}
finally {

    $Token = $null`n    $NgrokToken = $null

    try {
        [System.IO.File]::Delete([string]$TmpSecrets)
    }
    catch {
        # No bloquear AuraX por un fallo de limpieza temporal
    }
}



