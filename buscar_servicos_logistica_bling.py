"""
Script para buscar serviços de logística do Bling
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'Lhama-Banana')))

from app import create_app
from blueprints.services.bling_api_service import make_bling_api_request
import json

def buscar_servicos_logistica(tipo_integracao=None, pagina=1, limite=100):
    """
    Busca serviços de logística do Bling
    
    Args:
        tipo_integracao: Tipo de integração (ex: 'MelhorEnvio', 'Correios', etc.)
        pagina: Número da página
        limite: Quantidade de registros por página
    """
    app = create_app()
    
    with app.app_context():
        try:
            # Construir URL com parâmetros
            url = '/logisticas/servicos'
            params = {
                'pagina': pagina,
                'limite': limite
            }
            
            if tipo_integracao:
                params['tipoIntegracao'] = tipo_integracao
            
            print("=" * 80)
            print(f"🔍 Buscando serviços de logística do Bling")
            print("=" * 80)
            if tipo_integracao:
                print(f"Tipo de integração: {tipo_integracao}")
            print(f"Página: {pagina}, Limite: {limite}")
            print()
            
            # Fazer requisição
            response = make_bling_api_request('GET', url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                servicos = data.get('data', [])
                
                print(f"✅ Encontrados {len(servicos)} serviços de logística")
                print()
                
                if servicos:
                    print("📦 Serviços encontrados:")
                    print("-" * 80)
                    
                    for i, servico in enumerate(servicos, 1):
                        print(f"\n{i}. ID: {servico.get('id')}")
                        print(f"   Descrição: {servico.get('descricao')}")
                        print(f"   Código: {servico.get('codigo')}")
                        print(f"   Ativo: {servico.get('ativo')}")
                        print(f"   Frete Item: R$ {servico.get('freteItem', 0):.2f}")
                        print(f"   Estimativa Entrega: {servico.get('estimativaEntrega')} dias")
                        print(f"   ID Código Serviço: {servico.get('idCodigoServico')}")
                        
                        logistica = servico.get('logistica', {})
                        if logistica:
                            print(f"   Logística ID: {logistica.get('id')}")
                        
                        transportador = servico.get('transportador', {})
                        if transportador:
                            print(f"   Transportador ID: {transportador.get('id')}")
                        
                        aliases = servico.get('aliases', [])
                        if aliases:
                            print(f"   Aliases: {', '.join(aliases)}")
                    
                    print()
                    print("-" * 80)
                    print(f"\n📄 Resposta completa (JSON):")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                else:
                    print("⚠️ Nenhum serviço encontrado")
                
                return servicos
            else:
                print(f"❌ Erro ao buscar serviços: {response.status_code}")
                print(f"Resposta: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
            return None


def buscar_todos_servicos_melhor_envio():
    """Busca todos os serviços do Melhor Envio"""
    print("\n" + "=" * 80)
    print("🚚 Buscando serviços do MELHOR ENVIO")
    print("=" * 80)
    
    servicos = buscar_servicos_logistica(tipo_integracao='MelhorEnvio', pagina=1, limite=100)
    
    if servicos:
        print(f"\n✅ Total de serviços Melhor Envio encontrados: {len(servicos)}")
        
        # Agrupar por código/descrição
        print("\n📋 Resumo dos serviços:")
        servicos_unicos = {}
        for servico in servicos:
            codigo = servico.get('codigo', 'SEM_CODIGO')
            descricao = servico.get('descricao', 'SEM_DESCRICAO')
            key = f"{codigo} - {descricao}"
            
            if key not in servicos_unicos:
                servicos_unicos[key] = {
                    'ids': [],
                    'ativo': servico.get('ativo'),
                    'frete_item': servico.get('freteItem'),
                    'estimativa': servico.get('estimativaEntrega')
                }
            
            servicos_unicos[key]['ids'].append(servico.get('id'))
        
        for key, info in servicos_unicos.items():
            print(f"\n  • {key}")
            print(f"    IDs: {', '.join(map(str, info['ids']))}")
            print(f"    Ativo: {info['ativo']}")
            if info['frete_item']:
                print(f"    Frete Item: R$ {info['frete_item']:.2f}")
            if info['estimativa']:
                print(f"    Estimativa: {info['estimativa']} dias")
    
    return servicos


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Buscar serviços de logística do Bling')
    parser.add_argument('--tipo', type=str, help='Tipo de integração (ex: MelhorEnvio, Correios)')
    parser.add_argument('--pagina', type=int, default=1, help='Número da página')
    parser.add_argument('--limite', type=int, default=100, help='Limite de registros')
    parser.add_argument('--melhor-envio', action='store_true', help='Buscar apenas Melhor Envio')
    
    args = parser.parse_args()
    
    if args.melhor_envio:
        buscar_todos_servicos_melhor_envio()
    else:
        buscar_servicos_logistica(
            tipo_integracao=args.tipo,
            pagina=args.pagina,
            limite=args.limite
        )
