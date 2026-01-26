# 📝 Guia Completo do Strapi - LhamaBanana

## 🎯 Visão Geral

O sistema LhamaBanana usa **Strapi** como painel administrativo para gerenciar produtos, vendas, usuários, cupons e conteúdo do site. Todos os conteúdos são sincronizados automaticamente com o PostgreSQL quando você salva no Strapi.

## ⚙️ Configuração

- ✅ **Banco de Dados**: PostgreSQL (`sistema_usuarios`)
- ✅ **Porta**: 1337 (apenas localhost)
- ✅ **Autenticação**: Via proxy Flask (`/admin`)
- ✅ **Tema**: Cores da marca LhamaBanana (Turquesa `#40e0d0` e Amarelo `#FFE135`)

## 🎨 Customizações Aplicadas

### 1. Cores da Marca
- **Turquesa Principal**: `#40e0d0` - Aplicada em botões, links ativos, destaques
- **Turquesa Escuro**: `#36d1c4` - Hover e estados secundários
- **Amarelo Principal**: `#FFE135` - Ações secundárias e avisos
- **Amarelo Escuro**: `#ffd700` - Hover de elementos amarelos

### 2. Dashboard Home Customizado
- ✅ **Estatísticas em Tempo Real**: Total de Vendas, Receita Total, Etiquetas de Frete, Produtos com Estoque Baixo
- ✅ **Ações Rápidas**: Gerenciar Estoque, Criar Produto, Gestão de Frete
- ✅ **Links Rápidos**: Ver Pedidos, Etiquetas de Frete, Produtos, Usuários, Cupons, Categorias

### 3. Plugin de Gestão de Frete
- ✅ Interface completa de gestão de frete
- ✅ Visualização de produtos do pedido
- ✅ Impressão de etiquetas
- ✅ Rastreamento de envios
- ✅ Localização: `src/plugins/frete-management/`

### 4. Hot Reload e Auto-reload
- **Modo development**: usa `npm run develop` com hot reload
- **Modo production**: usa `npm run start` após build
- Configuração: `config/server.ts` com `watchAdminFiles` habilitado em desenvolvimento

### 5. Permissões Automáticas
- Role `strapi-super-admin` com acesso total
- Permissões configuradas automaticamente no bootstrap
- Plugin `frete-management` com permissão de leitura

## 📦 Content Types Criados

### Gestão de Produtos
- **Categoria** (`categoria`) - Categorias de produtos e estampas
- **Tecido** (`tecido`) - Tipos de tecidos disponíveis
- **Tamanho** (`tamanho`) - Tamanhos disponíveis
- **Estampa** (`estampa`) - Estampas disponíveis
- **Nome do Produto** (`nome-produto`) - Nomes e descrições base
- **Produto** (`produto`) - Variações com estoque
- **Imagem do Produto** (`imagem-produto`) - Imagens dos produtos

### Gestão de Vendas
- **Venda** (`venda`) - Pedidos e vendas
- **Item de Venda** (`item-venda`) - Itens de cada pedido
- **Pagamento** (`pagamento`) - Informações de pagamento
- **Cupom** (`cupom`) - Cupons de desconto

### Gestão de Conteúdo
- **Conteúdo Home** (Single Type) - Conteúdo da página inicial
- **Conteúdo Sobre** (Single Type) - Página sobre
- **Conteúdo Contato** (Single Type) - Página de contato
- **Política de Envio** (Single Type) - Política de envio
- **Política de Privacidade** (Single Type) - Política de privacidade
- **Informações da Empresa** (Single Type) - Informações da empresa

## 🔄 Como Funciona a Sincronização

O sistema LhamaBanana usa **Single Types** no Strapi para gerenciar o conteúdo das páginas principais. Todos os conteúdos são sincronizados automaticamente com o PostgreSQL quando você salva no Strapi.

## 🔄 Como Funciona a Sincronização

1. **Você edita no Strapi Admin** → Preenche os campos
2. **Ao salvar** → Lifecycle hooks são acionados (`afterCreate`, `afterUpdate`)
3. **Sincronização automática** → O serviço `strapi-sync-service.ts` atualiza o PostgreSQL
4. **Site atualizado** → O Flask lê os dados do PostgreSQL e exibe no site

---

## 🎨 GUIA RÁPIDO: Carrosséis com Fotos e Subtítulos

### Passo a Passo Completo

#### 1️⃣ **Criar um Carrossel com Itens Customizados**

**Passo 1:** Fazer upload das imagens
- Acesse **Media Library** no Strapi (menu lateral esquerdo)
- Faça upload de todas as imagens que você quer usar (fotos de crianças usando, conforto, etc.)
- Para cada imagem, copie a **URL completa**

**Passo 2:** Criar a estrutura do carrossel
- Vá para **Content Manager → Single Types → Conteúdo Home**
- Clique no campo `carrosseis`
- Crie um carrossel com a estrutura completa:

```json
[
  {
    "nome": "Destaques",
    "slug": "destaques",
    "subtitulo": "Os produtos mais queridos pelos nossos clientes",
    "ordem": 1,
    "ativo": true,
    "itens": [
      {
        "imagem": "https://seu-strapi.com/uploads/crianca-usando-produto1.jpg",
        "titulo": "Noites Tranquilas",
        "subtitulo": "Conforto que toda criança merece",
        "link": "/produto/1",
        "ordem": 1,
        "ativo": true
      },
      {
        "imagem": "https://seu-strapi.com/uploads/familia-feliz.jpg",
        "titulo": "Momentos em Família",
        "subtitulo": "Criando memórias especiais juntos",
        "link": "/produto/5",
        "ordem": 2,
        "ativo": true
      }
    ]
  }
]
```

**Passo 3:** Adicionar mais itens
Para adicionar mais itens ao carrossel, basta adicionar mais objetos no array `itens`:

```json
{
  "nome": "Destaques",
  "slug": "destaques",
  "itens": [
    {
      "imagem": "https://exemplo.com/foto1.jpg",
      "titulo": "Título do Item 1",
      "subtitulo": "Subtítulo do Item 1",
      "link": "/produto/1",
      "ordem": 1,
      "ativo": true
    },
    {
      "imagem": "https://exemplo.com/foto2.jpg",
      "titulo": "Título do Item 2",
      "subtitulo": "Subtítulo do Item 2",
      "link": "/produto/5",
      "ordem": 2,
      "ativo": true
    },
    {
      "imagem": "https://exemplo.com/foto3.jpg",
      "titulo": "Título do Item 3",
      "subtitulo": "Subtítulo do Item 3",
      "link": "/produto/12",
      "ordem": 3,
      "ativo": true
    }
  ]
}
```

#### 2️⃣ **Personalizar Cada Item do Carrossel**

Cada item do carrossel é totalmente customizável com foto, título e subtítulo próprios:

**Campos disponíveis para cada item:**
- `imagem` (string, **obrigatório**) - URL da foto customizada
- `titulo` (string, **obrigatório**) - Título do item
- `subtitulo` (string, opcional) - Descrição/legenda do item
- `link` (string, opcional) - Link para produto ou página específica (se não informado, todas as caixas levam para a loja `/produtos/`)
- `ordem` (integer, opcional) - Ordem de exibição dentro do carrossel
- `ativo` (boolean, opcional) - Se aparece no site (padrão: `true`)

**⚠️ Importante sobre links:**
- **Todas as caixas são clicáveis** - mesmo sem definir `link`, elas levam para a loja
- Se definir `link`, o item leva para esse link específico
- Se não definir `link`, o item leva automaticamente para `/produtos/` (loja)

**Exemplo de item focado em experiência:**
```json
{
  "imagem": "https://exemplo.com/crianca-dormindo.jpg",
  "titulo": "Noites de Sono Perfeitas",
  "subtitulo": "Conforto que transforma o descanso da sua família",
  "link": "/produto/1",
  "ordem": 1,
  "ativo": true
}
```

**Dicas para criar itens impactantes:**
- ✅ Use fotos de crianças/famílias usando os produtos
- ✅ Foque em emoções e experiências (conforto, felicidade, momentos em família)
- ✅ Títulos curtos e impactantes (2-4 palavras)
- ✅ Subtítulos que transmitam benefícios emocionais
- ✅ **Não inclua preços** - o foco é na experiência

#### 3️⃣ **Links dos Itens**

**Todas as caixas do carrossel são clicáveis e levam para a loja por padrão.**

Se quiser que um item específico leve para um produto ou página diferente:

```json
{
  "imagem": "https://exemplo.com/foto.jpg",
  "titulo": "Noites Tranquilas",
  "subtitulo": "Conforto que toda criança merece",
  "link": "/produto/1",  // Link específico (opcional)
  "ativo": true
}
```

**Comportamento:**
- Se `link` estiver definido: o item leva para esse link específico
- Se `link` não estiver definido: o item leva para a loja (`/produtos/`)

**Formato do link:**
- Para produto: `/produto/{id}` ou `/produtos/{id}`
- Para página: `/sobre`, `/contato`, etc.
- Se não informar: usa automaticamente `/produtos/` (loja)

#### 4️⃣ **Criar Múltiplos Carrosséis**

Você pode criar vários carrosséis diferentes, cada um com seus próprios itens customizados:

```json
[
  {
    "nome": "Destaques",
    "slug": "destaques",
    "subtitulo": "Os produtos mais queridos",
    "ordem": 1,
    "ativo": true,
    "itens": [
      {
        "imagem": "https://exemplo.com/foto1.jpg",
        "titulo": "Noites Tranquilas",
        "subtitulo": "Conforto que transforma",
        "link": "/produto/1",
        "ordem": 1,
        "ativo": true
      },
      {
        "imagem": "https://exemplo.com/foto2.jpg",
        "titulo": "Momentos em Família",
        "subtitulo": "Criando memórias especiais",
        "link": "/produto/5",
        "ordem": 2,
        "ativo": true
      }
    ]
  },
  {
    "nome": "Coleção Inverno",
    "slug": "inverno",
    "subtitulo": "Aqueça-se com estilo",
    "ordem": 2,
    "ativo": true,
    "itens": [
      {
        "imagem": "https://exemplo.com/inverno1.jpg",
        "titulo": "Aqueça-se no Inverno",
        "subtitulo": "Conforto para os dias frios",
        "link": "/produto/18",
        "ordem": 1,
        "ativo": true
      }
    ]
  }
]
```

#### 5️⃣ **Exemplo Completo: Carrossel com Múltiplos Itens**

```json
[
  {
    "nome": "Destaques",
    "slug": "destaques",
    "subtitulo": "Os produtos mais queridos pelos nossos clientes",
    "ordem": 1,
    "ativo": true,
    "itens": [
      {
        "imagem": "https://exemplo.com/crianca-dormindo.jpg",
        "titulo": "Noites de Sono Perfeitas",
        "subtitulo": "Conforto que transforma o descanso da sua família",
        "link": "/produto/1",
        "ordem": 1,
        "ativo": true
      },
      {
        "imagem": "https://exemplo.com/familia-feliz.jpg",
        "titulo": "Momentos em Família",
        "subtitulo": "Criando memórias especiais juntos",
        "link": "/produto/5",
        "ordem": 2,
        "ativo": true
      },
      {
        "imagem": "https://exemplo.com/conforto-qualidade.jpg",
        "titulo": "Qualidade Premium",
        "subtitulo": "Feito com carinho para sua família",
        "link": "/produto/12",
        "ordem": 3,
        "ativo": true
      },
      {
        "imagem": "https://exemplo.com/crianca-brincando.jpg",
        "titulo": "Liberdade para Brincar",
        "subtitulo": "Produtos que acompanham cada momento",
        "link": "/produto/18",
        "ordem": 4,
        "ativo": true
      }
    ]
  },
  {
    "nome": "Coleção Inverno",
    "slug": "inverno",
    "subtitulo": "Aqueça-se com estilo",
    "ordem": 2,
    "ativo": true,
    "itens": [
      {
        "imagem": "https://exemplo.com/inverno-crianca.jpg",
        "titulo": "Aqueça-se no Inverno",
        "subtitulo": "Conforto e estilo para os dias frios",
        "link": "/produto/18",
        "ordem": 1,
        "ativo": true
      },
      {
        "imagem": "https://exemplo.com/casaco-quentinho.jpg",
        "titulo": "Casacos Acolhedores",
        "subtitulo": "Proteção e conforto em um só produto",
        "link": "/produto/22",
        "ordem": 2,
        "ativo": true
      }
    ]
  }
]
```

**💡 Dicas:**
- Use fotos reais de crianças/famílias usando os produtos
- Foque em emoções e experiências, não em preços
- Títulos curtos e impactantes (2-4 palavras)
- Subtítulos que transmitam benefícios emocionais
- Adicione links para produtos relacionados quando fizer sentido

#### 6️⃣ **Upload e Organização de Imagens**

**Como fazer upload das imagens:**
1. Acesse **Media Library** no Strapi
2. Clique em **"Upload new asset"** ou arraste as imagens
3. Aguarde o upload completar
4. Clique em cada imagem para ver os detalhes
5. Copie a **URL completa** da imagem

**Dicas para escolher imagens:**
- Use fotos de alta qualidade
- Foque em mostrar crianças/famílias usando os produtos
- Mostre momentos de conforto, felicidade, descanso
- Evite imagens muito comerciais - prefira lifestyle
- Tamanho recomendado: 800x1000px ou similar (proporção vertical)

**Organização:**
- Dê nomes descritivos aos arquivos antes de fazer upload
- Exemplo: `crianca-dormindo-conforto.jpg`, `familia-feliz-momento.jpg`
- Isso facilita encontrar as imagens depois

#### 6️⃣ **Salvar e Verificar**

1. Clique em **"Save"** no Strapi
2. Verifique os logs (deve aparecer: `[SYNC] Conteudo Home atualizado`)
3. Acesse o site e verifique se o carrossel aparece corretamente

---

## 🏠 1. CONTEÚDO HOME

**Localização:** Content Manager → Single Types → **Conteúdo Home**

### Campos Disponíveis:

#### 📌 Hero Section
- **`hero_titulo`** (string) - Título principal da seção hero
  - Exemplo: `"Noites tranquilas, sorrisos garantidos!"`
  
- **`hero_subtitulo`** (text) - Subtítulo/descrição da hero
  - Exemplo: `"Somos uma marca feita por famílias, para famílias..."`

- **`hero_imagem`** (media) - Imagem da hero (upload de arquivo)
  - Aceita apenas imagens
  - Faça upload clicando no campo

- **`hero_texto_botao`** (string) - Texto do botão CTA
  - Padrão: `"Comprar Agora"`

#### 🎠 Carrosséis (JSON) - Totalmente Customizáveis
Campo do tipo **JSON** que aceita um array de objetos. Cada carrossel contém itens totalmente customizáveis com foto, título e subtítulo próprios.

**Estrutura completa:**

```json
[
  {
    "nome": "Destaques",
    "slug": "destaques",
    "subtitulo": "Os produtos mais queridos pelos nossos clientes",
    "ordem": 1,
    "ativo": true,
    "itens": [
      {
        "imagem": "https://exemplo.com/crianca-usando-produto1.jpg",
        "titulo": "Noites Tranquilas",
        "subtitulo": "Conforto que toda criança merece",
        "link": "/produto/1",
        "ordem": 1,
        "ativo": true
      },
      {
        "imagem": "https://exemplo.com/familia-feliz.jpg",
        "titulo": "Momentos em Família",
        "subtitulo": "Criando memórias especiais juntos",
        "link": "/produto/5",
        "ordem": 2,
        "ativo": true
      },
      {
        "imagem": "https://exemplo.com/conforto-qualidade.jpg",
        "titulo": "Qualidade Premium",
        "subtitulo": "Feito com carinho para sua família",
        "link": "/produto/12",
        "ordem": 3,
        "ativo": true
      }
    ]
  },
  {
    "nome": "Coleção Inverno",
    "slug": "inverno",
    "subtitulo": "Aqueça-se com estilo",
    "ordem": 2,
    "ativo": true,
    "itens": [
      {
        "imagem": "https://exemplo.com/inverno-crianca.jpg",
        "titulo": "Aqueça-se no Inverno",
        "subtitulo": "Conforto e estilo para os dias frios",
        "link": "/produto/18",
        "ordem": 1,
        "ativo": true
      }
    ]
  }
]
```

**Campos do carrossel:**
- `nome` (string, **obrigatório**) - Nome do carrossel (exibido como botão de filtro)
- `slug` (string, **obrigatório**) - Identificador único (usado para criar o ID do carrossel)
- `subtitulo` (string, opcional) - Subtítulo/descrição curta do carrossel
- `ordem` (integer, opcional) - Ordem de exibição dos botões (menor número aparece primeiro)
- `ativo` (boolean, **obrigatório**) - Se `true`, o carrossel aparece no site
- `itens` (array, **obrigatório**) - Array de itens customizados do carrossel

**Campos de cada item do carrossel:**
- `imagem` (string, **obrigatório**) - URL da imagem do item (foto customizada)
- `titulo` (string, **obrigatório**) - Título do item
- `subtitulo` (string, opcional) - Subtítulo/descrição do item
- `link` (string, opcional) - Link para o produto ou página (ex: `/produto/1`)
- `ordem` (integer, opcional) - Ordem de exibição dentro do carrossel
- `ativo` (boolean, opcional) - Se `true`, o item aparece (padrão: `true`)

**⚠️ Importante:**
- **Não há preços** - O foco é em mostrar experiências, conforto, crianças usando
- Cada item pode ter sua própria foto, título e subtítulo
- Os itens aparecem na ordem definida pelo campo `ordem`
- Se um item tiver `link`, ele se torna clicável

**Como adicionar fotos/imagens:**
1. **Imagem de banner do carrossel:**
   - Faça upload da imagem no Strapi (Media Library)
   - Copie a URL da imagem
   - Cole no campo `imagem` do JSON
   - Exemplo: `"imagem": "https://seu-strapi.com/uploads/imagem_carrossel.jpg"`

2. **Fotos dos produtos:**
   - As fotos dos produtos vêm automaticamente dos produtos cadastrados
   - Cada produto tem suas próprias imagens (campo `imagens` no produto)
   - Não é necessário adicionar fotos manualmente no carrossel

**Como escolher subtítulo:**
- Adicione o campo `subtitulo` no JSON do carrossel
- Exemplo: `"subtitulo": "Os produtos mais queridos pelos nossos clientes"`
- O subtítulo aparece abaixo do nome do carrossel (se implementado no frontend)

**Como os itens aparecem no carrossel:**
- Cada item é **totalmente customizável** com sua própria foto, título e subtítulo
- Os itens aparecem na ordem definida pelo campo `ordem` de cada item
- Apenas itens com `ativo: true` são exibidos
- **Todas as caixas são clicáveis** - levam para a loja por padrão ou para o link específico se definido
- **Não há preços** - o foco é em mostrar experiências, conforto, momentos especiais
- O `slug` do carrossel é usado para criar o ID no HTML (`carrossel-{slug}`)

**Como preencher no Strapi:**
1. Clique no campo `carrosseis`
2. Cole o JSON acima ou edite diretamente no editor JSON
3. Para adicionar imagem:
   - Faça upload no Media Library do Strapi
   - Copie a URL completa
   - Cole no campo `imagem` do JSON
4. Certifique-se de que o JSON está válido (sem erros de sintaxe)
5. Use `ordem` para controlar a sequência dos botões de filtro

#### 💬 Depoimentos (JSON)
Campo do tipo **JSON** que aceita um array de depoimentos. Estrutura:

```json
[
  {
    "texto": "A LhamaBanana transformou as noites da minha família. A qualidade dos produtos é incrível e o atendimento é excepcional!",
    "nome": "Ana Silva",
    "subtitulo": "Mãe e Cliente desde 2022",
    "ordem": 1,
    "ativo": true
  },
  {
    "texto": "Produtos de excelente qualidade! Recomendo para todas as famílias.",
    "nome": "Carlos Santos",
    "subtitulo": "Pai e Cliente desde 2021",
    "ordem": 2,
    "ativo": true
  }
]
```

**Campos de cada depoimento:**
- `texto` (string) - Texto do depoimento
- `nome` (string) - Nome do cliente
- `subtitulo` (string, opcional) - Subtítulo/cargo do cliente
- `ordem` (integer) - Ordem de exibição (menor número aparece primeiro)
- `ativo` (boolean) - Se `true`, o depoimento aparece no site

**Importante:** Apenas depoimentos com `ativo: true` são exibidos, e são ordenados pelo campo `ordem`.

#### 📊 Estatísticas
- **`estatisticas_clientes`** (integer) - Número de clientes satisfeitos
  - Padrão: `5000`
  - Exibido como: `"+5000 Clientes Satisfeitos"`

- **`estatisticas_pecas`** (integer) - Número de peças vendidas
  - Padrão: `10000`
  - Exibido como: `"+10000 Peças Vendidas"`

- **`estatisticas_anos`** (integer) - Anos de mercado
  - Padrão: `5`
  - Exibido como: `"+5 Anos de Mercado"`

#### ⚙️ Controle
- **`ativo`** (boolean) - Se `true`, o conteúdo aparece no site
  - Padrão: `true`

---

## 📖 2. CONTEÚDO SOBRE

**Localização:** Content Manager → Single Types → **Conteúdo Sobre**

### Campos Disponíveis:

#### 📚 História
- **`historia_titulo`** (string) - Título da seção história
  - Padrão: `"Nossa História"`
  
- **`historia_conteudo`** (richtext) - Conteúdo da história
  - Editor de texto rico (WYSIWYG)
  - Suporta formatação (negrito, itálico, listas, etc.)

#### 💎 Valores
- **`valores_titulo`** (string) - Título da seção valores
  - Padrão: `"Nossos Valores"`

- **`valores_conteudo`** (JSON) - Array de valores da empresa
  - Estrutura:
  ```json
  [
    {
      "titulo": "Qualidade Premium",
      "descricao": "Usamos apenas os melhores tecidos e materiais para garantir conforto e durabilidade.",
      "icone": "fas fa-star"
    },
    {
      "titulo": "Compromisso Familiar",
      "descricao": "Criamos produtos pensados especialmente para o bem-estar das famílias.",
      "icone": "fas fa-heart"
    },
    {
      "titulo": "Sustentabilidade",
      "descricao": "Nosso compromisso com o meio ambiente e práticas sustentáveis.",
      "icone": "fas fa-leaf"
    }
  ]
  ```

**Campos de cada valor:**
- `titulo` (string) - Título do valor
- `descricao` (string) - Descrição do valor
- `icone` (string) - Classe do ícone Font Awesome (ex: `"fas fa-star"`)

#### 👥 Equipe
- **`equipe_titulo`** (string) - Título da seção equipe
  - Padrão: `"Nossa Equipe"`

- **`equipe`** (JSON) - Array de membros da equipe
  - Estrutura:
  ```json
  [
    {
      "nome": "João Silva",
      "cargo": "CEO e Fundador",
      "descricao": "Apaixonado por criar produtos que fazem a diferença na vida das famílias.",
      "foto": "https://exemplo.com/foto.jpg",
      "ordem": 1,
      "ativo": true
    },
    {
      "nome": "Maria Santos",
      "cargo": "Diretora de Produtos",
      "descricao": "Especialista em design e qualidade.",
      "foto": "https://exemplo.com/foto2.jpg",
      "ordem": 2,
      "ativo": true
    }
  ]
  ```

**Campos de cada membro:**
- `nome` (string) - Nome do membro
- `cargo` (string) - Cargo/função
- `descricao` (string) - Descrição/biografia
- `foto` (string) - URL da foto (opcional)
- `ordem` (integer) - Ordem de exibição
- `ativo` (boolean) - Se aparece no site

#### ⚙️ Controle
- **`ativo`** (boolean) - Se `true`, o conteúdo aparece no site

---

## 📧 3. CONTEÚDO CONTATO

**Localização:** Content Manager → Single Types → **Conteúdo Contato**

### Campos Disponíveis:

#### 📝 Informações Gerais
- **`titulo`** (string) - Título da página
  - Padrão: `"Entre em Contato"`

- **`texto_principal`** (richtext) - Texto principal da página
  - Editor de texto rico
  - Pode incluir formatação e links

#### 📞 Informações de Contato (JSON)
Campo **`informacoes_contato`** (JSON) - Array de informações de contato:

```json
[
  {
    "tipo": "email",
    "icone": "fas fa-envelope",
    "titulo": "E-mail",
    "valor": "contato@lhamabanana.com.br",
    "link": "mailto:contato@lhamabanana.com.br"
  },
  {
    "tipo": "telefone",
    "icone": "fas fa-phone",
    "titulo": "Telefone",
    "valor": "(11) 1234-5678",
    "link": "tel:+551112345678"
  },
  {
    "tipo": "whatsapp",
    "icone": "fab fa-whatsapp",
    "titulo": "WhatsApp",
    "valor": "(11) 98765-4321",
    "link": "https://wa.me/5511987654321"
  },
  {
    "tipo": "endereco",
    "icone": "fas fa-map-marker-alt",
    "titulo": "Endereço",
    "valor": "Rua Exemplo, 123 - São Paulo, SP",
    "link": ""
  }
]
```

**Campos de cada informação:**
- `tipo` (string) - Tipo de contato (email, telefone, whatsapp, endereco, etc.)
- `icone` (string) - Classe do ícone Font Awesome
- `titulo` (string) - Título da informação
- `valor` (string) - Valor/texto da informação
- `link` (string) - Link clicável (opcional)

#### 🌐 Redes Sociais (JSON)
Campo **`redes_sociais`** (JSON) - Objeto com links das redes sociais:

```json
{
  "whatsapp": "https://wa.me/5511987654321",
  "instagram": "https://instagram.com/lhamabanana",
  "facebook": "https://facebook.com/lhamabanana",
  "pinterest": "https://pinterest.com/lhamabanana",
  "youtube": "https://youtube.com/@lhamabanana",
  "tiktok": "https://tiktok.com/@lhamabanana"
}
```

**Campos:**
- Cada chave é o nome da rede social
- O valor é a URL completa do perfil
- Deixe vazio (`""`) se não tiver a rede social

#### 📋 Formulário
- **`form_titulo`** (string) - Título do formulário de contato
  - Padrão: `"Envie sua Mensagem"`

- **`form_texto`** (text) - Texto descritivo do formulário
  - Exemplo: `"Preencha o formulário abaixo e entraremos em contato em breve."`

#### ⚙️ Controle
- **`ativo`** (boolean) - Se `true`, o conteúdo aparece no site

---

## 🏢 4. INFORMAÇÕES DA EMPRESA

**Localização:** Content Manager → Single Types → **Informações da Empresa**

### Campos Disponíveis:

#### 📞 Contato
- **`email`** (email) - Email de contato
- **`telefone`** (string) - Telefone
- **`whatsapp`** (string) - WhatsApp
- **`horario_atendimento`** (text) - Horário de atendimento
  - Exemplo: `"Segunda a Sexta: 9h às 18h\nSábado: 9h às 12h"`

#### 💎 Valores (JSON)
Campo **`valores`** (JSON) - Array de valores (mesma estrutura do Conteúdo Sobre):

```json
[
  {
    "titulo": "Qualidade",
    "descricao": "Produtos de alta qualidade",
    "icone": "fas fa-star"
  }
]
```

#### 🌐 Redes Sociais (JSON)
Campo **`redes_sociais`** (JSON) - Mesma estrutura do Conteúdo Contato

#### ⚙️ Controle
- **`ativo`** (boolean) - Se `true`, as informações aparecem no site

---

## 🎨 Como Adicionar Fotos e Configurar Carrosséis

### Adicionando Imagens aos Carrosséis

#### 1. **Imagem de Banner do Carrossel**
Para adicionar uma imagem de banner ao carrossel:

1. **No Strapi:**
   - Acesse **Media Library** (menu lateral)
   - Clique em **"Upload new asset"**
   - Selecione a imagem desejada
   - Após o upload, clique na imagem para ver os detalhes
   - Copie a **URL completa** da imagem

2. **No Conteúdo Home:**
   - Vá para o campo `carrosseis`
   - Adicione o campo `imagem` no JSON do carrossel:
   ```json
   {
     "nome": "Destaques",
     "slug": "destaques",
     "imagem": "https://seu-strapi.com/uploads/banner-destaques.jpg",
     "ativo": true
   }
   ```

#### 2. **Fotos dos Produtos**
As fotos dos produtos são gerenciadas diretamente nos produtos:

1. **No Strapi:**
   - Acesse **Content Manager → Collection Types → Produto**
   - Selecione ou crie um produto
   - No campo `imagens`, faça upload das fotos
   - A primeira imagem (menor `ordem`) será usada como imagem principal

2. **Os produtos aparecem automaticamente nos carrosséis** baseado nos filtros:
   - Se o carrossel tem `categoria_id`, mostra produtos dessa categoria
   - Se `filtro_destaque: true`, mostra apenas produtos em destaque
   - As imagens dos produtos são buscadas automaticamente

### Escolhendo Subtítulo

O subtítulo aparece abaixo do nome do carrossel (se implementado no frontend):

```json
{
  "nome": "Destaques",
  "slug": "destaques",
  "subtitulo": "Os produtos mais queridos pelos nossos clientes",
  "ativo": true
}
```

**Dicas para subtítulos:**
- Seja conciso (1-2 linhas)
- Use linguagem atrativa
- Destaque o diferencial do carrossel

### Ordenando os Carrosséis e Itens

**Ordenar os carrosséis:**
Use o campo `ordem` no carrossel para controlar a sequência dos botões de filtro:

```json
[
  {
    "nome": "Destaques",
    "slug": "destaques",
    "ordem": 1,  // Aparece primeiro
    "ativo": true,
    "itens": [...]
  },
  {
    "nome": "Coleção Inverno",
    "slug": "inverno",
    "ordem": 2,  // Aparece segundo
    "ativo": true,
    "itens": [...]
  }
]
```

**Ordenar os itens dentro do carrossel:**
Use o campo `ordem` em cada item para controlar a sequência de exibição:

```json
{
  "nome": "Destaques",
  "itens": [
    {
      "imagem": "https://exemplo.com/foto1.jpg",
      "titulo": "Item 1",
      "ordem": 1,  // Aparece primeiro
      "ativo": true
    },
    {
      "imagem": "https://exemplo.com/foto2.jpg",
      "titulo": "Item 2",
      "ordem": 2,  // Aparece segundo
      "ativo": true
    }
  ]
}
```

**Regra:** Menor número = aparece primeiro (tanto para carrosséis quanto para itens)

```json
[
  {
    "nome": "Destaques",
    "slug": "destaques",
    "ordem": 1,  // Aparece primeiro
    "ativo": true
  },
  {
    "nome": "Mais Vendidos",
    "slug": "vendidos",
    "ordem": 2,  // Aparece segundo
    "ativo": true
  }
]
```

**Regra:** Menor número = aparece primeiro

## ✅ Dicas Importantes

### 1. **Validação de JSON**
- Sempre valide o JSON antes de salvar
- Use um validador online se necessário: https://jsonlint.com/
- Certifique-se de usar aspas duplas (`"`) e não aspas simples (`'`)

### 2. **Campos Rich Text**
- Campos `richtext` suportam formatação completa
- Use o editor visual do Strapi para formatar
- O conteúdo é convertido para HTML no banco

### 3. **Imagens**
- Para campos de mídia, faça upload diretamente no Strapi
- A URL é processada automaticamente
- Aceita apenas imagens (JPG, PNG, GIF, etc.)

### 4. **Sincronização Automática**
- Ao salvar no Strapi, a sincronização acontece automaticamente
- Verifique os logs do Strapi para confirmar:
  ```bash
  docker-compose logs strapi | grep SYNC
  ```

### 5. **Ativo/Inativo**
- Use o campo `ativo` para mostrar/ocultar conteúdo
- Se `ativo = false`, o conteúdo não aparece no site

### 6. **Ordem de Exibição**
- Para arrays (depoimentos, valores, equipe), use o campo `ordem`
- Menor número = aparece primeiro
- Depoimentos são ordenados automaticamente por `ordem`

---

## 🔍 Verificando se Funcionou

### 1. **Logs do Strapi**
Após salvar, você deve ver:
```
[SYNC] Conteudo Home atualizado no PostgreSQL (ID: 1)
```

### 2. **Banco de Dados**
Verifique diretamente no PostgreSQL:
```sql
SELECT * FROM conteudo_home WHERE ativo = TRUE;
SELECT * FROM conteudo_sobre WHERE ativo = TRUE;
SELECT * FROM conteudo_contato WHERE ativo = TRUE;
```

### 3. **Site**
- Acesse a página correspondente no site
- O conteúdo atualizado deve aparecer automaticamente
- Se não aparecer, verifique se `ativo = true`

---

## 🚨 Troubleshooting

### JSON inválido
**Erro:** `SyntaxError: Unexpected token`
**Solução:** Valide o JSON em https://jsonlint.com/

### Conteúdo não aparece no site
**Possíveis causas:**
1. Campo `ativo = false` → Mude para `true`
2. Erro na sincronização → Verifique logs do Strapi
3. Cache do navegador → Limpe o cache (Ctrl+F5)

### Imagem não aparece
**Possíveis causas:**
1. URL inválida → Verifique se a imagem foi enviada corretamente
2. Permissões → Verifique se o Strapi tem acesso ao arquivo

### Sincronização não funciona
**Solução:**
1. Verifique se o PostgreSQL está rodando
2. Verifique as variáveis de ambiente do Strapi
3. Reinicie o container do Strapi:
   ```bash
   docker-compose restart strapi
   ```

---

## 📚 Estruturas JSON Completas

### Carrosséis (Home) - Estrutura Customizável Completa
```json
[
  {
    "nome": "Destaques",
    "slug": "destaques",
    "subtitulo": "Os produtos mais queridos pelos nossos clientes",
    "ordem": 1,
    "ativo": true,
    "itens": [
      {
        "imagem": "https://exemplo.com/crianca-dormindo.jpg",
        "titulo": "Noites de Sono Perfeitas",
        "subtitulo": "Conforto que transforma o descanso da sua família",
        "link": "/produto/1",
        "ordem": 1,
        "ativo": true
      },
      {
        "imagem": "https://exemplo.com/familia-feliz.jpg",
        "titulo": "Momentos em Família",
        "subtitulo": "Criando memórias especiais juntos",
        "link": "/produto/5",
        "ordem": 2,
        "ativo": true
      },
      {
        "imagem": "https://exemplo.com/conforto-qualidade.jpg",
        "titulo": "Qualidade Premium",
        "subtitulo": "Feito com carinho para sua família",
        "link": "/produto/12",
        "ordem": 3,
        "ativo": true
      },
      {
        "imagem": "https://exemplo.com/crianca-brincando.jpg",
        "titulo": "Liberdade para Brincar",
        "subtitulo": "Produtos que acompanham cada momento",
        "link": "/produto/18",
        "ordem": 4,
        "ativo": true
      }
    ]
  },
  {
    "nome": "Coleção Inverno",
    "slug": "inverno",
    "subtitulo": "Aqueça-se com estilo",
    "ordem": 2,
    "ativo": true,
    "itens": [
      {
        "imagem": "https://exemplo.com/inverno-crianca.jpg",
        "titulo": "Aqueça-se no Inverno",
        "subtitulo": "Conforto e estilo para os dias frios",
        "link": "/produto/18",
        "ordem": 1,
        "ativo": true
      },
      {
        "imagem": "https://exemplo.com/casaco-quentinho.jpg",
        "titulo": "Casacos Acolhedores",
        "subtitulo": "Proteção e conforto em um só produto",
        "link": "/produto/22",
        "ordem": 2,
        "ativo": true
      }
    ]
  },
  {
    "nome": "Conforto e Bem-Estar",
    "slug": "conforto",
    "subtitulo": "Produtos pensados no seu conforto",
    "ordem": 3,
    "ativo": true,
    "itens": [
      {
        "imagem": "https://exemplo.com/descanso-perfeito.jpg",
        "titulo": "Descanso Perfeito",
        "subtitulo": "Cada noite uma nova experiência de conforto",
        "link": "/produto/25",
        "ordem": 1,
        "ativo": true
      },
      {
        "imagem": "https://exemplo.com/cuidado-familia.jpg",
        "titulo": "Cuidado com sua Família",
        "subtitulo": "Produtos que demonstram todo nosso carinho",
        "link": "/produto/28",
        "ordem": 2,
        "ativo": true
      }
    ]
  }
]
```

**Explicação dos campos do carrossel:**
- `nome`: Nome exibido no botão de filtro
- `slug`: Identificador único (sem espaços, minúsculas)
- `subtitulo`: Texto descritivo do carrossel (opcional)
- `ordem`: Ordem de exibição dos botões (1 = primeiro)
- `ativo`: Se true, o carrossel aparece no site
- `itens`: **Array de itens customizados** (obrigatório)

**Explicação dos campos de cada item:**
- `imagem`: URL da foto customizada (obrigatório)
- `titulo`: Título do item (obrigatório)
- `subtitulo`: Descrição/legenda do item (opcional)
- `link`: Link para produto ou página (opcional)
- `ordem`: Ordem de exibição dentro do carrossel (opcional)
- `ativo`: Se true, o item aparece (opcional, padrão: true)

**💡 Dicas:**
- **Foque em experiências**: Use fotos de crianças/famílias usando os produtos
- **Sem preços**: O foco é em mostrar conforto, bem-estar, momentos especiais
- **Títulos impactantes**: Curto e emocional (2-4 palavras)
- **Subtítulos descritivos**: Transmita benefícios emocionais
- **Links opcionais**: Adicione apenas se fizer sentido levar para um produto

### Depoimentos (Home)
```json
[
  {
    "texto": "A LhamaBanana transformou as noites da minha família. A qualidade dos produtos é incrível e o atendimento é excepcional!",
    "nome": "Ana Silva",
    "subtitulo": "Mãe e Cliente desde 2022",
    "ordem": 1,
    "ativo": true
  },
  {
    "texto": "Produtos de excelente qualidade! Recomendo para todas as famílias que buscam conforto e bem-estar.",
    "nome": "Carlos Santos",
    "subtitulo": "Pai e Cliente desde 2021",
    "ordem": 2,
    "ativo": true
  },
  {
    "texto": "Atendimento impecável e produtos que realmente fazem a diferença no dia a dia!",
    "nome": "Maria Oliveira",
    "subtitulo": "Cliente desde 2020",
    "ordem": 3,
    "ativo": true
  }
]
```

### Valores (Sobre/Empresa)
```json
[
  {
    "titulo": "Qualidade Premium",
    "descricao": "Usamos apenas os melhores tecidos e materiais para garantir conforto e durabilidade.",
    "icone": "fas fa-star"
  },
  {
    "titulo": "Compromisso Familiar",
    "descricao": "Criamos produtos pensados especialmente para o bem-estar das famílias.",
    "icone": "fas fa-heart"
  },
  {
    "titulo": "Sustentabilidade",
    "descricao": "Nosso compromisso com o meio ambiente e práticas sustentáveis.",
    "icone": "fas fa-leaf"
  }
]
```

### Equipe (Sobre)
```json
[
  {
    "nome": "João Silva",
    "cargo": "CEO e Fundador",
    "descricao": "Apaixonado por criar produtos que fazem a diferença na vida das famílias.",
    "foto": "https://exemplo.com/foto.jpg",
    "ordem": 1,
    "ativo": true
  },
  {
    "nome": "Maria Santos",
    "cargo": "Diretora de Produtos",
    "descricao": "Especialista em design e qualidade.",
    "foto": "https://exemplo.com/foto2.jpg",
    "ordem": 2,
    "ativo": true
  }
]
```

### Informações de Contato (Contato)
```json
[
  {
    "tipo": "email",
    "icone": "fas fa-envelope",
    "titulo": "E-mail",
    "valor": "contato@lhamabanana.com.br",
    "link": "mailto:contato@lhamabanana.com.br"
  },
  {
    "tipo": "telefone",
    "icone": "fas fa-phone",
    "titulo": "Telefone",
    "valor": "(11) 1234-5678",
    "link": "tel:+551112345678"
  },
  {
    "tipo": "whatsapp",
    "icone": "fab fa-whatsapp",
    "titulo": "WhatsApp",
    "valor": "(11) 98765-4321",
    "link": "https://wa.me/5511987654321"
  }
]
```

### Redes Sociais (Contato/Empresa)
```json
{
  "whatsapp": "https://wa.me/5511987654321",
  "instagram": "https://instagram.com/lhamabanana",
  "facebook": "https://facebook.com/lhamabanana",
  "pinterest": "https://pinterest.com/lhamabanana",
  "youtube": "https://youtube.com/@lhamabanana",
  "tiktok": "https://tiktok.com/@lhamabanana"
}
```

---

## 📞 Suporte

Se tiver dúvidas ou problemas:
1. Verifique os logs do Strapi
2. Valide os JSONs em https://jsonlint.com/
3. Verifique se o PostgreSQL está acessível
4. Reinicie os containers se necessário
