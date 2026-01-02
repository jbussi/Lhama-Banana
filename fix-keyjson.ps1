# Script para corrigir problema do key.json
# Remove diretório key.json se existir dentro de Lhama-Banana

Write-Host "Verificando key.json..." -ForegroundColor Cyan

$keyJsonPath = Join-Path $PSScriptRoot "key.json"

if (Test-Path $keyJsonPath) {
    $item = Get-Item $keyJsonPath
    
    if ($item.PSIsContainer) {
        Write-Host "ATENCAO: Diretorio key.json encontrado. Removendo..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $keyJsonPath
        Write-Host "OK: Diretorio key.json removido!" -ForegroundColor Green
    } else {
        Write-Host "OK: key.json e um arquivo (correto)" -ForegroundColor Green
    }
} else {
    Write-Host "INFO: key.json nao encontrado em Lhama-Banana/ (isso e normal)" -ForegroundColor Blue
}

# Verificar se existe na raiz
$rootKeyJson = Join-Path (Split-Path $PSScriptRoot -Parent) "key.json"
if (Test-Path $rootKeyJson) {
    $rootItem = Get-Item $rootKeyJson
    if (-not $rootItem.PSIsContainer) {
        Write-Host "OK: Arquivo key.json encontrado na raiz do workspace" -ForegroundColor Green
    } else {
        Write-Host "ERRO: key.json na raiz tambem e um diretorio!" -ForegroundColor Red
    }
} else {
    Write-Host "ATENCAO: key.json nao encontrado na raiz do workspace" -ForegroundColor Yellow
    Write-Host "   Coloque o arquivo key.json na raiz do workspace (mesmo nivel de Lhama-Banana/)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Concluido!" -ForegroundColor Cyan
