# 🎨 Strapi Admin - Painel de Administração LhamaBanana

## 📋 Visão Geral

Painel administrativo customizado para gerenciar produtos, vendas, usuários, cupons e frete do e-commerce LhamaBanana.

## ⚙️ Configuração

- ✅ **Banco de Dados**: PostgreSQL (`sistema_usuarios`)
- ✅ **Porta**: 1337 (apenas localhost)
- ✅ **Autenticação**: Via proxy Flask (`/admin`)
- ✅ **Tema**: Cores da marca LhamaBanana (Turquesa `#40e0d0` e Amarelo `#FFE135`)

## 🎨 Customizações Aplicadas

### 1. **Cores da Marca**
- **Turquesa Principal**: `#40e0d0` - Aplicada em botões, links ativos, destaques
- **Turquesa Escuro**: `#36d1c4` - Hover e estados secundários
- **Amarelo Principal**: `#FFE135` - Ações secundárias e avisos
- **Amarelo Escuro**: `#ffd700` - Hover de elementos amarelos

### 2. **Dashboard Home Customizado**
- ✅ **Estatísticas em Tempo Real**:
  - Total de Vendas
  - Receita Total
  - Etiquetas de Frete
  - Produtos com Estoque Baixo (alerta visual)
- ✅ **Ações Rápidas**:
  - Gerenciar Estoque (acesso direto)
  - Criar Produto (acesso direto)
  - Gestão de Frete (acesso direto)
- ✅ **Links Rápidos**:
  - Ver Pedidos
  - Etiquetas de Frete
  - Produtos
  - Usuários
  - Cupons
  - Categorias

### 3. **Plugin de Gestão de Frete**
- ✅ Interface completa de gestão de frete
- ✅ Visualização de produtos do pedido
- ✅ Impressão de etiquetas
- ✅ Rastreamento de envios
- ✅ Localização: `src/plugins/frete-management/`

### 4. **Menu Limpo e Organizado**
- ✅ Plugins desnecessários desabilitados:
  - `users-permissions` (usamos Flask)
  - `i18n`
  - `documentation`
  - `cloud` (deploy)
  - `marketplace`
- ✅ Banners promocionais removidos via flags:
  - `FLAG_NPS: false` - Remove pesquisa de satisfação
  - `FLAG_PROMOTE_EE: false` - Remove promoções Enterprise
  - `FLAG_PROMOTE_TRIAL: false` - Remove promoções de trial
  - `FLAG_SHOW_TRIAL: false` - Remove avisos de trial

### 5. **Permissões Automáticas**
- ✅ Configuração automática de permissões para todos os Content Types
- ✅ Arquivo: `src/bootstrap/permissions.ts`
- ✅ Executa automaticamente no bootstrap do Strapi

## 🚀 Como Usar

### Acessar o Painel

1. **Via Proxy Flask** (Recomendado - com autenticação):
   - Faça login como admin: `http://localhost:5000/admin`
   - Acesse o Strapi: `http://localhost:5000/admin/strapi`

2. **Acesso Direto** (Desenvolvimento):
   - URL: `http://localhost:1337/admin`
   - Faça login com credenciais do Strapi

### Comandos

```bash
# Desenvolvimento (com hot reload)
docker compose restart strapi

# Ver logs
docker compose logs -f strapi

# Rebuild (se necessário)
docker compose build strapi
docker compose up -d strapi
```

## 📁 Estrutura de Arquivos

```
strapi-admin/
├── config/
│   ├── admin.ts              # Configurações do admin (flags, tema)
│   ├── plugins.ts            # Plugins habilitados/desabilitados
│   └── server.ts             # Configurações do servidor
├── src/
│   ├── admin/
│   │   ├── app.tsx           # Configuração principal (dashboard, menu)
│   │   ├── customizations.ts # Tema e cores da marca
│   │   └── components/
│   │       └── DashboardWidget.tsx  # Widget do dashboard home
│   ├── api/                  # Content Types (produtos, vendas, etc.)
│   ├── bootstrap/
│   │   └── permissions.ts    # Permissões automáticas
│   └── plugins/
│       └── frete-management/ # Plugin de gestão de frete
└── entrypoint.sh            # Script de inicialização (hot reload)
```

## 🔧 Modo Desenvolvimento

Para ativar hot reload, defina no `.env` ou `docker-compose.yml`:

```env
NODE_ENV=development
```

O Strapi irá:
- ✅ Recompilar automaticamente quando arquivos mudarem
- ✅ Recarregar o admin panel sem reiniciar o container
- ✅ Mostrar erros detalhados no console

## 📊 Content Types Principais

- **Produto**: Catálogo de produtos
- **Venda**: Pedidos e vendas
- **Usuario**: Usuários do sistema
- **Cupom**: Cupons de desconto
- **Categoria**: Categorias de produtos
- **EtiquetaFrete**: Etiquetas de frete geradas

## 🐛 Troubleshooting

### Widget não aparece no home:
1. Verifique os logs: `docker compose logs strapi`
2. Reinicie o Strapi: `docker compose restart strapi`
3. Limpe o cache do navegador

### Plugin de Frete não aparece:
1. Verifique se o plugin está registrado: `src/plugins/frete-management/admin/src/index.tsx`
2. Verifique os logs para erros
3. Tente acessar diretamente: `http://localhost:1337/admin/plugins/frete-management`

### Cores não aplicadas:
1. Verifique `src/admin/customizations.ts`
2. Limpe o cache do navegador
3. Reinicie o Strapi

### Banners ainda aparecem:
1. Verifique se as flags estão desabilitadas: `config/admin.ts`
2. Verifique se os plugins estão desabilitados: `config/plugins.ts`
3. Reinicie o Strapi

## 📚 Documentação Adicional

- `CONFIGURACAO_ADMIN.md` - Configuração detalhada do admin
- `CONTENT_TYPES.md` - Documentação dos Content Types
- `FIX_TAGS.md` - Correções de tags e categorias

## ⚠️ Notas Importantes

1. **Primeira vez**: O Strapi pode demorar um pouco para fazer o build inicial
2. **Permissões**: São configuradas automaticamente, mas podem ser ajustadas manualmente no painel
3. **Backup**: Sempre faça backup antes de atualizações importantes
4. **Produção**: Desabilite hot reload em produção (`NODE_ENV=production`)

## 🎯 Próximos Passos

- [ ] Adicionar mais widgets ao dashboard
- [ ] Configurar notificações customizadas
- [ ] Adicionar atalhos de teclado
- [ ] Melhorar visualização de relatórios

---

**Última atualização**: 2024
