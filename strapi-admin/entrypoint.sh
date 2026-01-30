#!/bin/sh
set -e

# PATCH: Desabilitar migrações automáticas
# O schema será pré-criado via SQL antes do Strapi iniciar
export AUTO_MIGRATE=false

echo "🚫 AUTO_MIGRATE desabilitado (schema pré-criado via SQL)"

# Verificar se estamos em modo desenvolvimento
if [ "$NODE_ENV" = "development" ]; then
  echo "🔧 Modo desenvolvimento: iniciando com hot reload..."
  # Em desenvolvimento, ainda permite hot reload mas sem migrações
  npm run develop
else
  # Verificar se o build do admin panel existe
  if [ ! -d "/app/node_modules/@strapi/admin/dist/server/server/build" ]; then
    echo "⚠️  Build do admin panel não encontrado. Fazendo build..."
    npm run build
  else
    echo "✅ Build do admin panel já existe. Pulando build."
  fi
  
  # Iniciar Strapi em produção
  # IMPORTANTE: Schema já deve estar criado via SQL antes deste ponto
  echo "🚀 Iniciando Strapi em produção (sem migrações automáticas)..."
  npm run start
fi


