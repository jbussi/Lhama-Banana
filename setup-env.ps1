# Script PowerShell para criar arquivo .env a partir do env.example

if (Test-Path .env) {
    $response = Read-Host "⚠️  Arquivo .env já existe. Deseja sobrescrever? (s/N)"
    if ($response -ne "s" -and $response -ne "S") {
        Write-Host "Operação cancelada."
        exit 0
    }
}

Copy-Item env.example .env
Write-Host "✅ Arquivo .env criado com sucesso!"
Write-Host "📝 Edite o arquivo .env com suas configurações se necessário."

