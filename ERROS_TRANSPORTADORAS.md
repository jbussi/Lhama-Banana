# ❌ Erros ao Criar Transportadoras no Bling

## 📋 Resumo dos Erros

Todas as 7 transportadoras falharam ao serem criadas. Principais problemas:

### 1. **IE (Inscrição Estadual) obrigatória** ⚠️
- **Erro:** "Para contribuintes do ICMS é obrigatória a informação da IE"
- **Afetadas:** Todas as transportadoras
- **Problema:** O Bling está rejeitando `ie: "ISENTO"` e `indicadorIe: 1`
- **Solução:** 
  - Verificar valores corretos para `indicadorIe`:
    - `1` = Contribuinte ICMS (exige IE)
    - `2` = Contribuinte isento de Inscrição no cadastro de Contribuintes
    - `9` = Não Contribuinte
  - Para transportadoras isentas, usar `indicadorIe: 2` ou `9` ao invés de `1`
  - OU buscar a IE real de cada transportadora

### 2. **CNPJ inválido** (Jadlog)
- **Erro:** "O campo CNPJ é inválido"
- **CNPJ informado:** 04263361000188
- **Solução:** Verificar se o CNPJ está correto (pode estar com formato errado ou dígito inválido)

### 3. **Telefone inválido** (LATAM Cargo, Buslog)
- **Erro:** "É necessário preencher corretamente o campo Telefone"
- **Formato atual:** "0300 115 9999" ou "0800-345-1001"
- **Solução:** O Bling pode exigir formato específico. Tentar:
  - Com DDD e sem formatação: "61132136000"
  - Com DDD e parênteses: "(61) 3213-6000"
  - Verificar na documentação do Bling qual formato é esperado

## 🔧 O que precisa ser corrigido:

### No arquivo `dados_transportadoras.json`:

1. **Para todas as transportadoras:**
   - Ajustar `indicadorIe` conforme situação real:
     - Se **isenta**: usar `2` ou `9`
     - Se **contribuinte**: buscar IE real e usar `1`
   - Remover `ie: "ISENTO"` ou substituir pela IE real

2. **Para Jadlog:**
   - Verificar CNPJ correto
   - Validar dígitos verificadores

3. **Para LATAM Cargo e Buslog:**
   - Ajustar formato do telefone
   - Usar formato numérico: `"telefone": "61132136000"` (sem espaços/hífens)
   - OU usar formato padrão: `"telefone": "(61) 3213-6000"`

4. **Para Loggi e LATAM Cargo:**
   - Preencher CNPJ quando encontrar
   - Preencher IE quando encontrar ou ajustar `indicadorIe`

## 📝 Valores possíveis para `indicadorIe`:

Segundo documentação fiscal:
- `1` = Contribuinte ICMS (exige IE válida)
- `2` = Contribuinte isento de Inscrição no cadastro de Contribuintes
- `9` = Não Contribuinte (quando for o caso)

## ✅ Próximos passos:

1. Buscar IE real de cada transportadora (se forem contribuintes)
2. Verificar se são isentas e usar `indicadorIe: 2` ou `9`
3. Validar CNPJs
4. Ajustar formato de telefones
5. Executar o script novamente após correções

## 🔍 Como descobrir IE de transportadoras:

- Consultar sites oficiais das transportadoras
- Consultar Receita Federal (CNPJ + IE)
- Verificar contratos/documentos das transportadoras
- Contatar suporte das transportadoras
