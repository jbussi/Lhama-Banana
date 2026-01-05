# Configuração do Painel Administrativo Strapi

Este documento descreve todas as customizações e melhorias implementadas no painel administrativo do LhamaBanana.

## 🎨 Melhorias Implementadas

### 1. ✅ Permissões por Role
- **Arquivo**: `src/bootstrap/permissions.ts`
- **Funcionalidade**: Configuração automática de permissões para todos os Content Types
- **Roles configuradas**:
  - `strapi-super-admin`: Acesso total a todos os Content Types
  - Permissões para: create, read, update, delete em todos os Content Types
  - Permissão especial para o plugin `frete-management`

### 2. 📦 Views Customizadas para Gestão de Frete
- **Plugin**: `src/plugins/frete-management/`
- **Funcionalidades**:
  - Visualização completa de todas as etiquetas de frete
  - Detalhes do pedido com produtos associados
  - Impressão de etiquetas
  - Rastreamento de envios
  - Status visual com badges coloridos
  - Interface limpa e intuitiva

**Componentes criados**:
- `admin/src/pages/App.tsx`: Página principal de gestão de frete
- `admin/src/components/Initializer.tsx`: Inicializador do plugin
- `admin/src/components/PluginIcon.tsx`: Ícone do plugin no menu

### 3. 🔄 Hot Reload e Auto-reload
- **Arquivo**: `entrypoint.sh`
- **Funcionalidade**: 
  - Em modo `development` (`NODE_ENV=development`): usa `npm run develop` com hot reload
  - Em modo `production`: usa `npm run start` após build
- **Configuração**: `config/server.ts` com `watchAdminFiles` habilitado em desenvolvimento

### 4. 🎨 Personalização Visual
- **Arquivo**: `src/admin/customizations.ts`
- **Melhorias**:
  - Tema customizado com cores do LhamaBanana
  - Tutoriais desabilitados
  - Notificações desnecessárias desabilitadas
  - Interface simplificada

### 5. 🧹 Interface Simplificada
- **Removido**:
  - Tutoriais automáticos
  - Notificações de releases
  - Opções não utilizadas
- **Mantido apenas**:
  - Content Types essenciais
  - Plugin de gestão de frete
  - Configurações necessárias

## 📁 Estrutura de Arquivos

```
strapi-admin/
├── src/
│   ├── admin/
│   │   ├── app.tsx              # Configuração principal do admin
│   │   └── customizations.ts    # Customizações visuais
│   ├── bootstrap/
│   │   └── permissions.ts       # Configuração de permissões
│   ├── plugins/
│   │   └── frete-management/    # Plugin de gestão de frete
│   │       ├── admin/
│   │       │   ├── src/
│   │       │   │   ├── index.tsx
│   │       │   │   ├── pages/
│   │       │   │   │   └── App.tsx
│   │       │   │   └── components/
│   │       │   │       ├── Initializer.tsx
│   │       │   │       └── PluginIcon.tsx
│   │       └── server/
│   │           └── src/
│   │               └── index.ts
│   └── index.ts                 # Bootstrap principal
├── config/
│   └── server.ts                 # Configuração do servidor
└── entrypoint.sh                # Script de entrada com hot reload
```

## 🚀 Como Usar

### 1. Modo Desenvolvimento (com Hot Reload)

No arquivo `.env` ou `docker-compose.yml`, defina:
```yaml
NODE_ENV: development
```

Ou no terminal:
```bash
export NODE_ENV=development
docker compose restart strapi
```

**Benefícios**:
- Hot reload automático
- Mudanças no código são refletidas imediatamente
- Melhor para desenvolvimento

### 2. Modo Produção

No arquivo `.env` ou `docker-compose.yml`, defina:
```yaml
NODE_ENV: production
```

**Benefícios**:
- Build otimizado
- Melhor performance
- Adequado para produção

### 3. Acessar Gestão de Frete

1. Acesse o painel admin: `http://localhost:1337/admin`
2. No menu lateral, clique em **"Gestão de Frete"**
3. Você verá:
   - Lista de todas as etiquetas de frete
   - Status de cada etiqueta
   - Ações: Ver detalhes, Imprimir etiqueta
4. Ao clicar em "Ver Detalhes":
   - Informações completas da etiqueta
   - Lista de produtos do pedido
   - Botões para imprimir e rastrear

## 🔐 Permissões

### Configuração Automática

As permissões são configuradas automaticamente no bootstrap do Strapi. O arquivo `src/bootstrap/permissions.ts` garante que:

1. O role `strapi-super-admin` tenha acesso total
2. Todas as ações (create, read, update, delete) estejam habilitadas
3. O plugin `frete-management` tenha permissão de leitura

### Verificar Permissões

1. Acesse: `http://localhost:1337/admin`
2. Vá em **Settings** → **Users & Permissions plugin** → **Roles**
3. Verifique se as permissões estão configuradas

### Configurar Novos Roles

Se precisar criar novos roles (ex: `moderator`, `editor`):

1. Crie o role no painel admin
2. Edite `src/bootstrap/permissions.ts` para adicionar permissões específicas
3. Reinicie o Strapi

## 🎨 Personalização Visual

### Alterar Cores do Tema

Edite `src/admin/customizations.ts`:

```typescript
theme: {
  light: {
    colors: {
      primary500: '#sua-cor-aqui',
      // ...
    },
  },
}
```

### Adicionar Logo

1. Coloque o logo em `public/uploads/logo.png`
2. Descomente em `src/admin/app.tsx`:
```typescript
menu: {
  logo: {
    src: '/uploads/logo.png',
    alt: 'LhamaBanana',
  },
}
```

## 🐛 Troubleshooting

### Hot Reload não funciona

1. Verifique se `NODE_ENV=development` está definido
2. Verifique os logs: `docker compose logs strapi`
3. Reinicie o container: `docker compose restart strapi`

### Plugin de Frete não aparece

1. Verifique se o build foi feito: `docker compose exec strapi npm run build`
2. Verifique os logs: `docker compose logs strapi`
3. Reinicie o Strapi: `docker compose restart strapi`

### Permissões não funcionam

1. Verifique os logs do bootstrap: `docker compose logs strapi | grep "Permissões"`
2. Verifique se o role existe no banco de dados
3. Configure manualmente no painel admin se necessário

## 📝 Próximos Passos (Opcional)

1. **Adicionar mais views customizadas**:
   - Dashboard com métricas
   - Relatórios de vendas
   - Gestão de estoque

2. **Criar roles adicionais**:
   - Editor: pode editar produtos, mas não deletar
   - Viewer: apenas leitura

3. **Adicionar validações customizadas**:
   - Validação de SKU único
   - Validação de estoque mínimo

4. **Criar hooks automáticos**:
   - Atualizar estoque ao criar venda
   - Enviar email ao mudar status do pedido

## ✅ Checklist de Verificação

- [x] Permissões configuradas automaticamente
- [x] Views customizadas para gestão de frete criadas
- [x] Hot reload configurado para desenvolvimento
- [x] Tema personalizado aplicado
- [x] Interface simplificada (tutoriais e notificações desabilitadas)
- [x] Plugin de frete registrado no menu
- [x] Documentação criada

## 🎉 Resultado Final

O painel administrativo agora está:
- ✅ **Organizado**: Interface limpa e intuitiva
- ✅ **Funcional**: Gestão completa de frete com visualização de produtos
- ✅ **Eficiente**: Hot reload em desenvolvimento
- ✅ **Seguro**: Permissões configuradas corretamente
- ✅ **Personalizado**: Visual alinhado com a marca




