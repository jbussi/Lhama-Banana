# Script PowerShell para criar o banco de dados do Metabase
# Execute este script quando o PostgreSQL estiver rodando

Write-Host "Verificando se o banco 'metabase' existe..." -ForegroundColor Cyan

# Verificar se o banco existe
$checkResult = docker compose exec -T postgres psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'metabase'" 2>&1

if ($checkResult -match "1") {
    Write-Host "✅ Banco de dados 'metabase' já existe." -ForegroundColor Green
} else {
    Write-Host "📦 Criando banco de dados 'metabase'..." -ForegroundColor Yellow
    docker compose exec -T postgres psql -U postgres -c "CREATE DATABASE metabase;" 2>&1 | Out-Null
    docker compose exec -T postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE metabase TO postgres;" 2>&1 | Out-Null
    Write-Host "✅ Banco de dados 'metabase' criado com sucesso!" -ForegroundColor Green
}

Write-Host "🔄 Reiniciando Metabase..." -ForegroundColor Cyan
docker compose restart metabase

Write-Host "✅ Concluído! Aguarde alguns segundos para o Metabase inicializar." -ForegroundColor Green


