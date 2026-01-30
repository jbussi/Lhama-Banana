# Script PowerShell para deploy no Docker Hub (Windows)
# Uso: .\scripts\deploy-to-dockerhub.ps1 -Version v1.0.0

param(
    [string]$Version = "latest",
    [switch]$SkipBuild = $false
)

# Verificar DOCKERHUB_USER
if (-not $env:DOCKERHUB_USER) {
    Write-Host "ERRO: DOCKERHUB_USER nao configurado" -ForegroundColor Red
    Write-Host ""
    Write-Host "Configure com:" -ForegroundColor Yellow
    Write-Host "  `$env:DOCKERHUB_USER = 'seu-usuario'"
    Write-Host ""
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Deploy para Docker Hub - Lhama Banana" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuracao:" -ForegroundColor Yellow
Write-Host "  Usuario: $env:DOCKERHUB_USER"
Write-Host "  Versao: $Version"
Write-Host ""

# 1. Build
if (-not $SkipBuild) {
    Write-Host "----------------------------------------" -ForegroundColor Green
    Write-Host "Passo 1: Construindo imagens..." -ForegroundColor Green
    Write-Host "----------------------------------------" -ForegroundColor Green
    
    docker compose build flask
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERRO ao construir Flask" -ForegroundColor Red
        exit 1
    }
    
    docker compose build strapi
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERRO ao construir Strapi" -ForegroundColor Red
        exit 1
    }
    
    docker compose build nginx
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERRO ao construir Nginx" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "Aplicando tags..." -ForegroundColor Green
    
    $registry = "docker.io/$env:DOCKERHUB_USER"
    
    docker tag lhama_banana_flask:latest "${registry}/lhama-banana-flask:$Version"
    docker tag lhama_banana_flask:latest "${registry}/lhama-banana-flask:latest"
    
    docker tag lhama_banana_strapi:latest "${registry}/lhama-banana-strapi:$Version"
    docker tag lhama_banana_strapi:latest "${registry}/lhama-banana-strapi:latest"
    
    docker tag lhama_banana_nginx:latest "${registry}/lhama-banana-nginx:$Version"
    docker tag lhama_banana_nginx:latest "${registry}/lhama-banana-nginx:latest"
    
    Write-Host "OK: Imagens construidas e tags aplicadas!" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "Pulando build (SkipBuild=true)" -ForegroundColor Yellow
    Write-Host ""
}

# 2. Verificar login
Write-Host "----------------------------------------" -ForegroundColor Green
Write-Host "Verificando autenticacao..." -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Green

$loginCheck = docker info 2>&1 | Select-String "Username"
if (-not $loginCheck) {
    Write-Host "ERRO: Nao autenticado no Docker Hub" -ForegroundColor Red
    Write-Host "Execute: docker login" -ForegroundColor Yellow
    exit 1
}

Write-Host "OK: Autenticado no Docker Hub" -ForegroundColor Green
Write-Host ""

# 3. Confirmação
Write-Host "----------------------------------------" -ForegroundColor Green
Write-Host "Pronto para fazer push para Docker Hub" -ForegroundColor Yellow
Write-Host "  Usuario: $env:DOCKERHUB_USER" -ForegroundColor Yellow
Write-Host "  Versao: $Version" -ForegroundColor Yellow
Write-Host ""
$confirm = Read-Host "Deseja continuar com o push? (y/N)"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "Push cancelado pelo usuario" -ForegroundColor Yellow
    exit 0
}

# 4. Push
Write-Host "----------------------------------------" -ForegroundColor Green
Write-Host "Passo 2: Fazendo push para Docker Hub..." -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Green

$registry = "docker.io/$env:DOCKERHUB_USER"

Write-Host "Fazendo push Flask ($Version)..." -ForegroundColor Yellow
docker push "${registry}/lhama-banana-flask:$Version"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO ao fazer push Flask" -ForegroundColor Red
    exit 1
}
docker push "${registry}/lhama-banana-flask:latest"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO ao fazer push Flask (latest)" -ForegroundColor Red
    exit 1
}

Write-Host "Fazendo push Strapi ($Version)..." -ForegroundColor Yellow
docker push "${registry}/lhama-banana-strapi:$Version"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO ao fazer push Strapi" -ForegroundColor Red
    exit 1
}
docker push "${registry}/lhama-banana-strapi:latest"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO ao fazer push Strapi (latest)" -ForegroundColor Red
    exit 1
}

Write-Host "Fazendo push Nginx ($Version)..." -ForegroundColor Yellow
docker push "${registry}/lhama-banana-nginx:$Version"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO ao fazer push Nginx" -ForegroundColor Red
    exit 1
}
docker push "${registry}/lhama-banana-nginx:latest"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO ao fazer push Nginx (latest)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "----------------------------------------" -ForegroundColor Green
Write-Host "OK: Deploy concluido com sucesso!" -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Green
Write-Host ""
Write-Host "Imagens publicadas:" -ForegroundColor Yellow
Write-Host "  - $env:DOCKERHUB_USER/lhama-banana-flask:$Version"
Write-Host "  - $env:DOCKERHUB_USER/lhama-banana-strapi:$Version"
Write-Host "  - $env:DOCKERHUB_USER/lhama-banana-nginx:$Version"
Write-Host ""
Write-Host "Links:" -ForegroundColor Yellow
$flaskUrl = "https://hub.docker.com/r/$env:DOCKERHUB_USER/lhama-banana-flask"
$strapiUrl = "https://hub.docker.com/r/$env:DOCKERHUB_USER/lhama-banana-strapi"
$nginxUrl = "https://hub.docker.com/r/$env:DOCKERHUB_USER/lhama-banana-nginx"
Write-Host "  - $flaskUrl"
Write-Host "  - $strapiUrl"
Write-Host "  - $nginxUrl"
Write-Host ""
