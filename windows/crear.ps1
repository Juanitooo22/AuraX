param(
    [Parameter(Mandatory=$true)]
    [int]$OfferId,

    [int]$DiskGB = 32
)

$ErrorActionPreference = "Stop"

Write-Host "Creando nueva instancia AuraX..."

vastai create instance $OfferId `
    --image "vastai/linux-desktop:cuda-12.9-ubuntu24.04" `
    --disk $DiskGB `
    --ssh

if ($LASTEXITCODE -ne 0) {
    throw "Error creando la instancia."
}

Write-Host ""
Write-Host "Instancia creada."
Write-Host "Cuando aparezca running ejecuta:"
Write-Host ".\conectar.ps1"
