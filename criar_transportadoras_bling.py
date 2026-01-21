"""
Script para criar contatos de transportadoras no Bling
=======================================================
Lê os dados das transportadoras de dados_transportadoras.json e cria os contatos no Bling.
"""

import sys
import os
import json

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from blueprints.services.bling_contact_service import create_contact_in_bling, find_contact_in_bling

def main():
    # Criar app Flask
    app = create_app()
    
    with app.app_context():
        # Carregar dados das transportadoras
        transportadoras_file = os.path.join(os.path.dirname(__file__), 'dados_transportadoras.json')
        
        try:
            with open(transportadoras_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"❌ Arquivo não encontrado: {transportadoras_file}")
            return
        except json.JSONDecodeError as e:
            print(f"❌ Erro ao ler JSON: {e}")
            return
        
        transportadoras = data.get('transportadoras', [])
        
        print(f"📦 Encontradas {len(transportadoras)} transportadoras para criar no Bling\n")
        
        resultados = []
        
        for idx, transportadora in enumerate(transportadoras, 1):
            nome = transportadora.get('nome', 'Sem nome')
            cnpj = transportadora.get('numeroDocumento', '')
            codigo = transportadora.get('codigo', '')
            
            print(f"\n[{idx}/{len(transportadoras)}] Processando: {nome} ({codigo})")
            
            # Verificar se já existe
            if cnpj:
                contato_existente = find_contact_in_bling(cnpj)
                if contato_existente:
                    print(f"  ⚠️  Contato já existe no Bling (ID: {contato_existente.get('id')})")
                    resultados.append({
                        'nome': nome,
                        'codigo': codigo,
                        'cnpj': cnpj,
                        'status': 'ja_existe',
                        'contact_id': contato_existente.get('id')
                    })
                    continue
            
            # Criar contato
            print(f"  📤 Criando contato no Bling...")
            resultado = create_contact_in_bling(transportadora)
            
            if resultado.get('success'):
                contact_id = resultado.get('contact_id')
                print(f"  ✅ Contato criado com sucesso! ID: {contact_id}")
                resultados.append({
                    'nome': nome,
                    'codigo': codigo,
                    'cnpj': cnpj,
                    'status': 'criado',
                    'contact_id': contact_id
                })
            else:
                error = resultado.get('error', 'Erro desconhecido')
                print(f"  ❌ Erro ao criar contato: {error}")
                if resultado.get('details'):
                    print(f"     Detalhes: {resultado.get('details')}")
                resultados.append({
                    'nome': nome,
                    'codigo': codigo,
                    'cnpj': cnpj,
                    'status': 'erro',
                    'error': error
                })
        
        # Resumo final
        print("\n" + "="*60)
        print("📊 RESUMO FINAL")
        print("="*60)
        
        criados = [r for r in resultados if r['status'] == 'criado']
        ja_existem = [r for r in resultados if r['status'] == 'ja_existe']
        erros = [r for r in resultados if r['status'] == 'erro']
        
        print(f"\n✅ Criados: {len(criados)}")
        for r in criados:
            print(f"   - {r['nome']} (ID: {r['contact_id']})")
        
        print(f"\n⚠️  Já existiam: {len(ja_existem)}")
        for r in ja_existem:
            print(f"   - {r['nome']} (ID: {r['contact_id']})")
        
        print(f"\n❌ Erros: {len(erros)}")
        for r in erros:
            print(f"   - {r['nome']}: {r.get('error', 'Erro desconhecido')}")
        
        print("\n" + "="*60)
        
        # Salvar resultados em arquivo
        resultados_file = os.path.join(os.path.dirname(__file__), 'resultados_transportadoras.json')
        with open(resultados_file, 'w', encoding='utf-8') as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Resultados salvos em: {resultados_file}")

if __name__ == '__main__':
    main()
