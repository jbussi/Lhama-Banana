# 📦 Criação de Contatos de Transportadoras no Bling

## ✅ O que foi criado:

### 1. Serviço de Contatos (`bling_contact_service.py`)
- Função `create_contact_in_bling()`: Cria contatos no Bling usando API v3
- Função `find_contact_in_bling()`: Busca contatos existentes por CNPJ
- Suporte completo para todos os campos da API do Bling

### 2. Dados das Transportadoras (`dados_transportadoras.json`)
Arquivo JSON com dados das seguintes transportadoras:

1. **Correios** ✅
   - CNPJ: 34.028.316/0001-03
   - Endereço: Brasília/DF
   - Dados completos

2. **Jadlog** ✅
   - CNPJ: 04.263.361/0001-88
   - Endereço: Mogi das Cruzes/SP
   - Dados completos

3. **Loggi** ⚠️
   - CNPJ: Não encontrado (precisa confirmar)
   - Endereço: São Paulo/SP (parcial)
   - **ATENÇÃO:** CNPJ e endereço completo precisam ser confirmados

4. **Azul Cargo Express** ✅
   - CNPJ: 15.479.373/0001-64
   - Endereço: Pato Branco/PR
   - Dados completos

5. **LATAM Cargo Brasil** ⚠️
   - CNPJ: Não encontrado (precisa confirmar)
   - Endereço: São Paulo/SP (parcial)
   - **ATENÇÃO:** CNPJ e endereço completo precisam ser confirmados

6. **Buslog** ✅
   - CNPJ: 12.437.084/0001-04
   - Endereço: Rio de Janeiro/RJ
   - Dados completos

7. **JeT Express** ✅
   - CNPJ: 03.900.533/0001-18
   - Endereço: Rio Claro/SP
   - Dados completos

### 3. Script de Criação (`criar_transportadoras_bling.py`)
Script Python que:
- Lê `dados_transportadoras.json`
- Verifica se contato já existe (por CNPJ)
- Cria contatos no Bling
- Gera relatório de resultados

## 🚀 Como executar:

```bash
# Dentro do container Flask
docker exec lhama_banana_flask python criar_transportadoras_bling.py
```

Ou, se preferir executar localmente:

```bash
python criar_transportadoras_bling.py
```

## ⚠️ Dados que precisam ser confirmados:

### Loggi:
- [ ] CNPJ oficial
- [ ] Endereço completo (rua, número, bairro, CEP)
- [ ] Inscrição Estadual (IE)
- [ ] Email fiscal oficial

### LATAM Cargo Brasil:
- [ ] CNPJ oficial
- [ ] Endereço completo (rua, número, bairro, CEP)
- [ ] Inscrição Estadual (IE)
- [ ] Email fiscal oficial

## 📝 Como complementar os dados:

1. Edite o arquivo `dados_transportadoras.json`
2. Preencha os campos vazios para Loggi e LATAM Cargo
3. Confirme os demais dados se necessário
4. Execute o script novamente

## 🔍 Campos importantes na API do Bling:

- `nome`: Nome completo/razão social
- `codigo`: Código interno (usado para identificar)
- `numeroDocumento`: CNPJ (sem formatação)
- `tipo`: "J" para jurídica, "F" para física
- `situacao`: "A" para ativo
- `ie`: Inscrição Estadual
- `endereco.geral`: Endereço completo
- `emailNotaFiscal`: Email para receber documentos fiscais

## 💡 Próximos passos:

Após criar os contatos no Bling:
1. Os IDs dos contatos serão salvos em `resultados_transportadoras.json`
2. Use esses IDs para preencher automaticamente os dados das transportadoras nas NF-e
3. Integre com o serviço de emissão de NFC-e (`bling_nfe_service.py`)

---

**Status:** ✅ Pronto para executar (após confirmar dados de Loggi e LATAM Cargo)
