# Script PowerShell para corrigir todos os problemas
# Cria banco metabase e reinicia servicos

Write-Host "Iniciando correcoes..." -ForegroundColor Cyan

# 1. Verificar se PostgreSQL esta rodando
Write-Host "Verificando PostgreSQL..." -ForegroundColor Yellow
$pgRunning = docker compose ps postgres --format "{{.State}}" 2>&1
if ($pgRunning -notmatch "running") {
    Write-Host "PostgreSQL nao esta rodando. Subindo..." -ForegroundColor Yellow
    docker compose up -d postgres
    Write-Host "Aguardando PostgreSQL inicializar..." -ForegroundColor Cyan
    Start-Sleep -Seconds 15
    # Aguardar ate estar saudavel
    $maxRetries = 30
    $retry = 0
    while ($retry -lt $maxRetries) {
        $health = docker compose exec -T postgres pg_isready -U postgres 2>&1
        if ($health -match "accepting connections") {
            break
        }
        Start-Sleep -Seconds 1
        $retry++
    }
}

# 2. Criar banco metabase
Write-Host "Verificando banco 'metabase'..." -ForegroundColor Yellow
$checkResult = docker compose exec -T postgres psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'metabase';" 2>&1
$checkResult = $checkResult.Trim()

if ($checkResult -eq "1") {
    Write-Host "Banco 'metabase' ja existe." -ForegroundColor Green
} else {
    Write-Host "Criando banco 'metabase'..." -ForegroundColor Yellow
    $createResult = docker compose exec -T postgres psql -U postgres -c "CREATE DATABASE metabase;" 2>&1
    if ($LASTEXITCODE -eq 0) {
        docker compose exec -T postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE metabase TO postgres;" 2>&1 | Out-Null
        Write-Host "Banco 'metabase' criado!" -ForegroundColor Green
    } else {
        if ($createResult -match "already exists") {
            Write-Host "Banco 'metabase' ja existe (criado em outra execucao)." -ForegroundColor Green
        } else {
            Write-Host "Erro ao criar banco: $createResult" -ForegroundColor Red
        }
    }
}

# 3. Reiniciar Metabase
Write-Host "Reiniciando Metabase..." -ForegroundColor Yellow
docker compose restart metabase 2>&1 | Out-Null

Write-Host ""
Write-Host "Correcoes aplicadas!" -ForegroundColor Green
Write-Host "Aguarde ~90 segundos para o Metabase inicializar." -ForegroundColor Cyan
Write-Host "Acesse: http://localhost:5000/analytics" -ForegroundColor Cyan

