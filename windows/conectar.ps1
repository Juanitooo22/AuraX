param([int]$InstanceId = 0)

$ErrorActionPreference = "Stop"

$Base = Join-Path $env:USERPROFILE "Desktop\AuraX-Local"
$SecretFile = Join-Path $Base "secrets.clixml"
$SshKey = Join-Path $env:USERPROFILE ".ssh\id_ed25519"
$McpDir = Join-Path $env:USERPROFILE "Desktop\MCPBridge"
$McpServer = Join-Path $McpDir "mcp-server\index.js"

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
    Write-Host "Primera vez: guarda el token de Discord localmente."
    $DiscordToken = Read-Host "Discord token" -AsSecureString

    [pscustomobject]@{
        DiscordToken = $DiscordToken
        DiscordOwnerId = "1086360701632794666"
    } | Export-Clixml $SecretFile
}

$Secrets = Import-Clixml $SecretFile
$Token = SecureToPlain $Secrets.DiscordToken

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
    throw "No hay instancia Vast.ai activa."
}

$IP = $Inst.public_ipaddr

if (!$IP) {
    $IP = $Inst.public_ip
}

$Port = [int]$Inst.ports.'22/tcp'[0].HostPort

Write-Host "Vast: $($Inst.id)"
Write-Host "SSH: root@$IP`:$Port"

$TmpSecrets = Join-Path $env:TEMP "aurax-secrets.env"

$EscapedToken = $Token.Replace("'", "'\''")

$Content = @"
export DISCORD_TOKEN='$EscapedToken'
export DISCORD_OWNER_ID='1086360701632794666'
"@

[IO.File]::WriteAllText(
    $TmpSecrets,
    $Content,
    (New-Object Text.UTF8Encoding($false))
)

try {

    ssh `
      -i $SshKey `
      -p $Port `
      -o StrictHostKeyChecking=accept-new `
      "root@$IP" `
      "mkdir -p /workspace; if [ ! -d /workspace/AuraX/.git ]; then git clone -b discord-only https://github.com/Juanitooo22/AuraX.git /workspace/AuraX; else git -C /workspace/AuraX fetch origin discord-only; git -C /workspace/AuraX checkout discord-only; git -C /workspace/AuraX pull --ff-only origin discord-only; fi"

    scp `
      -i $SshKey `
      -P $Port `
      $TmpSecrets `
      "root@$IP`:/workspace/secrets.env"

    ssh `
      -i $SshKey `
      -p $Port `
      "root@$IP" `
      "chmod 600 /workspace/secrets.env; chmod +x /workspace/AuraX/setup_full.sh; bash /workspace/AuraX/setup_full.sh"

    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "ssh -N -i `"$SshKey`" -L 11435:127.0.0.1:11434 -p $Port root@$IP"
    )

    if (Test-Path $McpServer) {

        Start-Process powershell `
          -WorkingDirectory (Split-Path $McpServer) `
          -ArgumentList @(
            "-NoExit",
            "-Command",
            "node index.js"
          )
    }

    Start-Process code

    Write-Host ""
    Write-Host "============================="
    Write-Host " AURAX WINDOWS LISTO"
    Write-Host "============================="
    Write-Host "Ollama: http://localhost:11435"
    Write-Host "MCPBridge Roblox: 127.0.0.1:7842"
}
finally {

    $Token = $null

    if (Test-Path $TmpSecrets) {
        Remove-Item $TmpSecrets -Force
    }
}
