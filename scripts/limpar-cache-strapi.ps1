# =====================================================
# Script PowerShell para limpar cache do Strapi
# =====================================================
# Este script limpa o cache do Strapi para remover
# registros órfãos que aparecem no admin mas não existem no banco
# =====================================================

Write-Host "🧹 Limpando cache do Strapi..." -ForegroundColor Cyan

# Parar o Strapi
Write-Host "⏸️  Parando o Strapi..." -ForegroundColor Yellow
docker compose stop strapi

# Limpar cache do Strapi
Write-Host "🗑️  Removendo cache..." -ForegroundColor Yellow
docker compose exec strapi sh -c "rm -rf .cache .tmp dist build" 2>$null

# Limpar cache do volume (se existir)
Write-Host "🗑️  Limpando cache do volume..." -ForegroundColor Yellow
docker compose run --rm strapi sh -c "rm -rf .cache .tmp dist build" 2>$null

# Reiniciar o Strapi
Write-Host "▶️  Reiniciando o Strapi..." -ForegroundColor Yellow
docker compose up -d strapi

Write-Host "✅ Cache limpo! O Strapi será reconstruído na próxima inicialização." -ForegroundColor Green
Write-Host "⏳ Aguarde alguns minutos para o Strapi reconstruir o índice..." -ForegroundColor Yellow
