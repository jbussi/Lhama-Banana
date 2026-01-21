# 📄 Ajustes na Emissão de NFC-e

## ✅ Alterações Implementadas

### 1. **Tipo de Saída: NFC-e**
- ✅ Configurado como `tipo: 1` (NFC-e - Nota Fiscal de Consumidor Eletrônica)
- ✅ Tipo correto para pessoa física

### 2. **Número e Série Automáticos**
- ✅ **NÃO** enviamos `numero` nem `serie` no payload
- ✅ Bling define automaticamente o número e série da nota
- ✅ Comentário adicionado no código: `# NÃO enviar número e série - deixar Bling definir automaticamente`

### 3. **Valor Total dos Produtos SEM Desconto**
- ✅ Itens usam `preco_venda_normal` (preço do produto sem desconto promocional)
- ✅ Se não houver `preco_venda_normal`, usa `preco_unitario` como fallback
- ✅ Valor total dos produtos calculado **antes** de aplicar desconto
- ✅ Log adicionado: `💰 Valor total dos produtos (sem desconto): R$ X.XX`

### 4. **Valor do Frete**
- ✅ Incluído no campo `transporte.frete`
- ✅ Valor obtido de `venda_data.get('valor_frete', 0)`
- ✅ Apenas incluído se `valor_frete > 0`

### 5. **Valor dos Descontos (Separado)**
- ✅ Desconto aplicado separadamente no campo `desconto`
- ✅ Valor obtido de `venda_data.get('valor_desconto', 0)`
- ✅ Apenas incluído se `valor_desconto > 0`
- ✅ Desconto **não** é aplicado nos itens, apenas no total da nota

### 6. **Total da Nota**
- ✅ Calculado corretamente: `valor_total_produtos - valor_desconto + valor_frete`
- ✅ Usado nas parcelas de pagamento
- ✅ Log detalhado dos valores:
  ```
  💰 Valores da NFC-e:
     Produtos (sem desconto): R$ X.XX
     Desconto: R$ X.XX
     Frete: R$ X.XX
     Total da nota: R$ X.XX
  ```

### 7. **Frete por Conta do Destinatário**
- ✅ Configurado como `fretePorConta: 0` (0 = Por conta do destinatário)
- ✅ Incluído na seção `transporte` do payload
- ✅ Apenas incluído se houver frete

### 8. **Serviço de Postagem**
- ✅ Sistema busca etiqueta de frete no banco de dados
- ✅ Extrai `servico_nome` ou `transportadora_nome` da etiqueta
- ✅ Incluído em `transporte.volumes[0].servico` se disponível
- ✅ Também adicionado nas observações da nota
- ✅ Log: `📦 Serviço de postagem encontrado: {servico_postagem}`

## 📋 Estrutura do Payload Final

```json
{
  "tipo": 1,
  "dataOperacao": "2026-01-21 14:30:00",
  "contato": {
    "nome": "...",
    "tipoPessoa": "F",
    "numeroDocumento": "...",
    "email": "...",
    "telefone": "...",
    "endereco": {...}
  },
  "finalidade": 1,
  "itens": [
    {
      "codigo": "...",
      "descricao": "...",
      "unidade": "UN",
      "quantidade": 1,
      "valor": 100.00,  // Preço SEM desconto
      "tipo": "P"
    }
  ],
  "parcelas": [
    {
      "data": "2026-01-21",
      "valor": 90.00,  // Total da nota (produtos - desconto + frete)
      "formaPagamento": {"id": 123}
    }
  ],
  "desconto": 10.00,  // Desconto separado
  "transporte": {
    "fretePorConta": 0,  // Por conta do destinatário
    "frete": 20.00,
    "volumes": [
      {
        "servico": "PAC"  // Serviço de postagem
      }
    ]
  },
  "observacoes": "Pedido originado do site LhamaBanana. Código: XXX | Serviço de postagem: PAC"
}
```

## 🔍 Valores Calculados

### Exemplo:
- **Produtos (sem desconto):** R$ 100,00
- **Desconto:** R$ 10,00
- **Frete:** R$ 20,00
- **Total da nota:** R$ 110,00 (100 - 10 + 20)

## 📝 Observações Importantes

1. **Número e Série:** Bling define automaticamente, não enviamos no payload
2. **Preço dos Itens:** Sempre usa preço normal do produto (sem desconto promocional)
3. **Desconto:** Aplicado apenas no total, não nos itens individuais
4. **Frete:** Sempre por conta do destinatário (`fretePorConta: 0`)
5. **Serviço de Postagem:** Buscado da etiqueta de frete se existir

## ✅ Testes Recomendados

1. Testar emissão com pedido sem desconto
2. Testar emissão com pedido com desconto
3. Testar emissão com frete
4. Testar emissão sem frete
5. Testar emissão com serviço de postagem
6. Testar emissão sem serviço de postagem
7. Verificar se número e série são definidos pelo Bling
8. Verificar se valores estão corretos na nota emitida

---

**Data:** 2026-01-21
**Status:** ✅ Implementado e pronto para testes
