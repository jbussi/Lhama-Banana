#!/bin/sh

# Verificar se estamos em modo desenvolvimento
if [ "$NODE_ENV" = "development" ]; then
  echo "🔧 Modo desenvolvimento: iniciando com hot reload..."
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
  npm run start
fi


