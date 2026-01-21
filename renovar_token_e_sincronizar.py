#!/usr/bin/env python3
"""
Script para renovar token do Bling e sincronizar situações
Execute: python renovar_token_e_sincronizar.py
"""
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, current_app
from blueprints.services.db import get_db, init_db_pool
from blueprints.services.bling_api_service import refresh_bling_token, get_valid_access_token
from blueprints.services.bling_situacao_service import sync_bling_situacoes_to_db, get_all_bling_situacoes
import psycopg2.extras
import requests
import base64

# Criar app Flask mínimo
app = Flask(__name__)
app.config.from_object('config.Config')

# Inicializar pool de conexões
init_db_pool(app.config['DATABASE_CONFIG'])

def renovar_token_via_endpoint():
    """
    Tenta renovar o token do Bling via endpoint HTTP da API Flask
    """
    import time
    
    print("🔄 Tentando renovar token via endpoint da API...")
    
    # Tentar usar endpoint HTTP (requer autenticação admin)
    # Por enquanto, vamos usar a função direta mesmo
    # Mas vamos adicionar um delay maior entre tentativas
    
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        # Buscar refresh_token do banco
        cur.execute("""
            SELECT refresh_token, expires_at
            FROM bling_tokens
            WHERE id = 1
        """)
        
        token_data = cur.fetchone()
        
        if not token_data:
            print("❌ Nenhum token encontrado no banco. É necessário autorizar primeiro.")
            print("   Acesse: http://localhost:5000/api/bling/authorize")
            return False
        
        refresh_token = token_data.get('refresh_token')
        expires_at = token_data.get('expires_at')
        
        if not refresh_token:
            print("❌ Refresh token não encontrado. É necessário autorizar novamente.")
            print("   Acesse: http://localhost:5000/api/bling/authorize")
            return False
        
        print(f"🔄 Token atual expira em: {expires_at}")
        print("🔄 Aguardando 10 segundos antes de tentar (para evitar rate limiting)...")
        time.sleep(10)
        print("🔄 Tentando renovar token usando refresh_token...")
        
        # Renovar token
        BLING_TOKEN_URL = "https://www.bling.com.br/Api/v3/oauth/token"
        client_id = app.config['BLING_CLIENT_ID']
        client_secret = app.config['BLING_CLIENT_SECRET']
        
        credentials = f"{client_id}:{client_secret}"
        credentials_b64 = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'Authorization': f'Basic {credentials_b64}'
        }
        
        response = requests.post(
            BLING_TOKEN_URL,
            data=data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            new_tokens = response.json()
            
            # Atualizar tokens no banco
            new_expires_at = datetime.now() + timedelta(seconds=new_tokens.get('expires_in', 3600))
            cur.execute("""
                UPDATE bling_tokens
                SET access_token = %s,
                    refresh_token = %s,
                    expires_at = %s,
                    updated_at = NOW()
                WHERE id = 1
            """, (
                new_tokens['access_token'],
                new_tokens.get('refresh_token', refresh_token),
                new_expires_at
            ))
            
            conn.commit()
            print(f"✅ Token renovado com sucesso!")
            print(f"   Novo token expira em: {new_expires_at}")
            return True
        elif response.status_code == 429:
            print(f"\n⚠️  Rate limiting detectado (HTTP 429)")
            print(f"   O Bling bloqueou temporariamente o IP devido a muitas tentativas.")
            print(f"\n💡 SOLUÇÕES:")
            print(f"   1. Aguarde 10-15 minutos antes de tentar novamente")
            print(f"   2. OU renove manualmente via navegador:")
            print(f"      - Acesse: http://localhost:5000/api/bling/authorize")
            print(f"      - Autorize o acesso")
            print(f"      - Execute este script novamente")
            return False
        else:
            print(f"❌ Erro ao renovar token: HTTP {response.status_code}")
            
            try:
                error_data = response.json()
                error_type = error_data.get('error', {}).get('type', '')
                error_msg = error_data.get('error', {}).get('message', '')
                
                if error_type == 'invalid_grant':
                    print(f"\n⚠️  Refresh token inválido ou expirado.")
                    print(f"   É necessário autorizar novamente:")
                    print(f"   Acesse: http://localhost:5000/api/bling/authorize")
                else:
                    print(f"   Erro: {error_type} - {error_msg}")
            except:
                # Resposta não é JSON
                if response.status_code == 429:
                    print(f"   Rate limiting - aguarde alguns minutos")
                else:
                    print(f"   Resposta: {response.text[:200]}")
            
            return False
            
    except Exception as e:
        print(f"❌ Erro ao renovar token: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        cur.close()


def renovar_token_manual():
    """Alias para compatibilidade"""
    return renovar_token_via_endpoint()


with app.app_context():
    print("=" * 80)
    print("🔄 Renovando Token Bling e Sincronizando Situações")
    print("=" * 80)
    
    # Passo 1: Verificar se token está válido primeiro
    print("\n📝 PASSO 1: Verificando token atual...")
    try:
        token = get_valid_access_token()
        print("✅ Token válido encontrado - pulando renovação")
        token_valido = True
    except Exception as e:
        print(f"⚠️  Token inválido ou expirado: {e}")
        token_valido = False
    
    # Passo 2: Tentar renovar apenas se necessário
    if not token_valido:
        print("\n📝 PASSO 2: Tentando renovar token do Bling...")
        token_renovado = renovar_token_manual()
        
        if not token_renovado:
            print("\n⚠️  Não foi possível renovar automaticamente.")
            print("   Tentando continuar mesmo assim (token pode ter sido renovado manualmente)...")
        
        # Tentar obter token novamente após tentativa de renovação
        try:
            token = get_valid_access_token()
            print("✅ Token válido obtido após tentativa de renovação")
            token_valido = True
        except Exception as e:
            print(f"❌ Erro: Token ainda inválido após tentativa de renovação: {e}")
            print("   Se você autorizou manualmente, o token pode estar atualizado.")
            print("   Continuando com sincronização...")
    
    # Passo 3: Verificar token válido antes de continuar
    print("\n📝 PASSO 3: Verificando token válido antes de sincronizar...")
    try:
        token = get_valid_access_token()
        print("✅ Token válido confirmado")
    except Exception as e:
        print(f"⚠️  Aviso: Erro ao obter token válido: {e}")
        print("   Continuando mesmo assim - pode funcionar se token foi renovado manualmente")
    
    # Passo 4: Buscar situações do Bling
    print("\n📝 PASSO 4: Buscando situações do Bling via API...")
    situacoes_bling = get_all_bling_situacoes()
    
    if not situacoes_bling:
        print("⚠️  Nenhuma situação encontrada via busca automática.")
        print("   Isso pode ser normal se a API não permitir listagem.")
        print("   Vamos tentar sincronizar mesmo assim...")
    else:
        print(f"✅ Encontradas {len(situacoes_bling)} situações no Bling")
        for sit in situacoes_bling[:5]:  # Mostrar primeiras 5
            print(f"   - ID {sit.get('id')}: {sit.get('nome')}")
        if len(situacoes_bling) > 5:
            print(f"   ... e mais {len(situacoes_bling) - 5}")
    
    # Passo 5: Sincronizar para o banco
    print("\n📝 PASSO 5: Sincronizando situações para o banco de dados...")
    result = sync_bling_situacoes_to_db()
    
    if result.get('success'):
        print(f"✅ Sincronização concluída!")
        print(f"   Total: {result.get('total')}")
        print(f"   Sincronizadas: {result.get('sincronizadas')}")
        print(f"   Atualizadas: {result.get('atualizadas')}")
    else:
        print(f"⚠️  Sincronização parcial ou com erros:")
        print(f"   {result.get('error', 'Erro desconhecido')}")
    
    # Passo 6: Listar situações no banco
    print("\n📝 PASSO 6: Situações no banco de dados:")
    print("-" * 80)
    
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
            SELECT bling_situacao_id, nome, cor, status_site, ativo
            FROM bling_situacoes
            ORDER BY bling_situacao_id
        """)
        
        situacoes = cur.fetchall()
        
        print(f"{'ID':<10} {'Nome':<35} {'Status Site':<25} {'Cor'}")
        print("-" * 80)
        
        for situacao in situacoes:
            id_str = str(situacao['bling_situacao_id'])
            nome = situacao['nome'][:35]
            status = situacao['status_site'] or "(sem mapeamento)"
            cor = situacao['cor'] or "-"
            
            # Marcar IDs temporários
            if situacao['bling_situacao_id'] > 100000 or situacao['bling_situacao_id'] < 0:
                id_str = f"{id_str} (temp)"
            
            print(f"{id_str:<10} {nome:<35} {status:<25} {cor}")
        
        print("-" * 80)
        
        # Verificar IDs temporários
        cur.execute("""
            SELECT COUNT(*) as total
            FROM bling_situacoes
            WHERE bling_situacao_id > 100000 OR bling_situacao_id < 0
        """)
        
        temp_count = cur.fetchone()['total']
        
        if temp_count > 0:
            print(f"\n⚠️  Ainda existem {temp_count} situações com IDs temporários.")
            print("   Execute: python update_situacoes_ids.py para tentar atualizar")
        else:
            print("\n✅ Todas as situações têm IDs reais do Bling!")
        
    finally:
        cur.close()
    
    print("\n" + "=" * 80)
    print("✅ Processo concluído!")
    print("=" * 80)
    print("\n💡 Próximos passos:")
    print("   1. Se ainda houver IDs temporários, execute:")
    print("      python update_situacoes_ids.py")
    print("   2. Mapear situações para status do site usando:")
    print("      POST /api/bling/situacoes/<id>/map")
    print("      Body: {\"status_site\": \"em_processamento\"}")
    print("   3. Testar webhook quando pedido mudar de situação no Bling")
