# 📄 Implementação: Emissão de NFC-e quando Pedido muda para "Em andamento"

## ✅ O que foi implementado

### 1. Função de Emissão de NFC-e (`emit_nfce_consumidor`)

**Arquivo:** `blueprints/services/bling_nfe_service.py`

**Função:** `emit_nfce_consumidor(venda_id: int) -> Dict`

Esta função:
- Busca dados completos do pedido (cliente, itens, pagamento)
- Mapeia para o formato da API do Bling (`POST /nfe`)
- Emite NFC-e de consumidor (tipo 1)
- Salva informações da NFC-e no banco de dados
- Retorna resultado da emissão

**Formato da requisição:**
```json
{
  "tipo": 1,
  "dataOperacao": "2023-01-12 09:52:12",
  "contato": {
    "nome": "...",
    "tipoPessoa": "F",
    "numeroDocumento": "...",
    "email": "...",
    "telefone": "...",
    "endereco": {...}
  },
  "finalidade": 1,
  "itens": [...],
  "parcelas": [...],
  "desconto": 0,
  "despesas": 0,
  "observacoes": "..."
}
```

### 2. Webhook Atualizado para Detectar "Em andamento"

**Arquivo:** `blueprints/api/webhook.py`

**Modificações:**
- Detecta quando situação muda para "Em andamento" (por nome)
- Chama `emit_nfce_consumidor()` automaticamente
- Atualiza status do pedido para `nfe_aguardando_aprovacao` após emissão
- Trata erros e atualiza status para `erro_nfe_timeout` se falhar

**Fluxo:**
```
1. Webhook recebe atualização de pedido do Bling
   ↓
2. Verifica se situação mudou para "Em andamento"
   ↓
3. Se sim, verifica se NFC-e já foi emitida
   ↓
4. Se não, emite NFC-e via emit_nfce_consumidor()
   ↓
5. Atualiza status do pedido:
   - Sucesso → 'nfe_aguardando_aprovacao'
   - Erro → 'erro_nfe_timeout'
```

### 3. Mapeamento de Dados

**Dados mapeados:**
- ✅ Contato (nome, CPF/CNPJ, email, telefone, endereço)
- ✅ Itens (código, descrição, quantidade, valor)
- ✅ Parcelas (data, valor, forma de pagamento)
- ✅ Desconto
- ✅ Frete (como despesas)
- ✅ Observações

**Campos opcionais suportados:**
- IE (Inscrição Estadual) para PJ
- Endereço completo (rua, número, complemento, bairro, CEP, município, UF)
- Múltiplas parcelas com datas de vencimento

## 🔄 Fluxo Completo Implementado

```
1. Pedido criado no Bling com status "Em aberto"
   ↓
2. Admin aprova pedido manualmente no Bling
   ↓
3. Bling muda situação para "Em andamento"
   ↓
4. Bling envia webhook para backend
   ↓
5. Backend detecta mudança para "Em andamento"
   ↓
6. Backend emite NFC-e via API do Bling
   ↓
7. Backend atualiza status do pedido para 'nfe_aguardando_aprovacao'
   ↓
8. Aguardando aprovação da SEFAZ (próximo passo)
```

## 📋 Status do Pedido

**Novos status adicionados:**
- `nfe_aguardando_aprovacao` - NFC-e emitida, aguardando SEFAZ
- `erro_nfe_timeout` - Erro ao emitir NFC-e

## 🔍 Detecção de "Em andamento"

A detecção é feita por **nome da situação**:
```python
situacao_nome_lower = (situacao_bling_nome or '').lower()
is_em_andamento = 'em andamento' in situacao_nome_lower
```

**Nota:** Quando os IDs reais das situações forem descobertos, podemos melhorar a detecção usando o ID também.

## ⚠️ Validações Implementadas

1. **Dados fiscais:** Verifica se CPF/CNPJ está presente
2. **NFC-e já emitida:** Verifica se já existe antes de emitir novamente
3. **Tratamento de erros:** Salva erros e atualiza status apropriadamente
4. **Logs detalhados:** Registra todas as etapas do processo

## 📝 Próximos Passos

1. ✅ **Implementado:** Emissão de NFC-e quando muda para "Em andamento"
2. ⏳ **Pendente:** Webhook para aguardar aprovação da SEFAZ
3. ⏳ **Pendente:** Enviar NFC-e por email ao funcionário após aprovação
4. ⏳ **Pendente:** Decrementar estoque após aprovação
5. ⏳ **Pendente:** Emitir etiqueta Melhor Envio após aprovação

## 🧪 Como Testar

1. Criar um pedido no site
2. Sincronizar com Bling
3. Mudar situação do pedido para "Em andamento" no Bling
4. Verificar logs do backend para ver emissão da NFC-e
5. Verificar status do pedido no banco (deve estar `nfe_aguardando_aprovacao`)

## 📚 Referências

- API Bling: `POST /nfe` - Criar nota fiscal de consumidor
- Documentação: https://developer.bling.com.br/referencia/nfe
