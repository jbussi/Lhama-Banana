import requests
import json
from flask import current_app
from typing import Dict, List, Optional

class ShippingService:
    """Serviço para cálculo de frete usando APIs de transporte"""
    
    def __init__(self):
        self.correios_api_url = "https://viacep.com.br/ws/{cep}/json/"
        self.melhor_envio_api_url = "https://melhorenvio.com.br/api/v2/me/shipment/calculate"
        # Configurações serão carregadas dinamicamente quando necessário
        self._melhor_envio_token = None
        self._cep_origem = None
    
    def _get_config(self):
        """Carrega configurações do Melhor Envio dinamicamente"""
        try:
            if self._melhor_envio_token is None:
                self._melhor_envio_token = current_app.config.get('MELHOR_ENVIO_TOKEN', '')
            if self._cep_origem is None:
                self._cep_origem = current_app.config.get('MELHOR_ENVIO_CEP_ORIGEM', '')
            return self._melhor_envio_token, self._cep_origem
        except RuntimeError:
            # current_app não disponível fora do contexto
            return '', ''
        
    def calculate_shipping(self, cep_destino: str, peso_total: float, 
                          valor_total: float, dimensoes: Dict) -> List[Dict]:
        """
        Calcula opções de frete para um CEP de destino
        
        Args:
            cep_destino: CEP de destino (apenas números)
            peso_total: Peso total em kg
            valor_total: Valor total dos produtos
            dimensoes: Dicionário com altura, largura, comprimento em cm
            
        Returns:
            Lista de opções de frete com valores e prazos
        """
        try:
            # Primeiro, validar o CEP
            if not self._validate_cep(cep_destino):
                return []
                
            # Buscar informações do CEP
            cep_info = self._get_cep_info(cep_destino)
            if not cep_info:
                return []
                
            # Tentar usar Melhor Envio se token estiver configurado
            melhor_envio_token, cep_origem = self._get_config()
            if melhor_envio_token and cep_origem:
                melhor_envio_options = self._calculate_melhor_envio(
                    cep_destino, peso_total, valor_total, dimensoes
                )
                if melhor_envio_options:
                    # Adicionar opção de frete grátis se aplicável
                    if valor_total >= 150.00:
                        free_shipping = {
                            'name': 'Frete Grátis',
                            'service': 'free',
                            'price': 0.00,
                            'delivery_time': '5-7 dias úteis',
                            'delivery_time_days': 6,
                            'description': 'Frete grátis para compras acima de R$ 150,00'
                        }
                        melhor_envio_options.append(free_shipping)
                    return melhor_envio_options
            
            # Fallback para cálculo simulado se Melhor Envio não estiver configurado
            shipping_options = []
            
            # Opção 1: PAC (Correios)
            pac_option = self._calculate_pac(cep_destino, peso_total, valor_total, dimensoes)
            if pac_option:
                shipping_options.append(pac_option)
                
            # Opção 2: SEDEX (Correios)
            sedex_option = self._calculate_sedex(cep_destino, peso_total, valor_total, dimensoes)
            if sedex_option:
                shipping_options.append(sedex_option)
                
            # Opção 3: Frete Grátis (se valor >= R$ 150)
            if valor_total >= 150.00:
                free_shipping = {
                    'name': 'Frete Grátis',
                    'service': 'free',
                    'price': 0.00,
                    'delivery_time': '5-7 dias úteis',
                    'delivery_time_days': 6,
                    'description': 'Frete grátis para compras acima de R$ 150,00'
                }
                shipping_options.append(free_shipping)
                
            return shipping_options
            
        except Exception as e:
            current_app.logger.error(f"Erro ao calcular frete: {e}")
            return []
    
    def _validate_cep(self, cep: str) -> bool:
        """Valida formato do CEP"""
        cep_clean = cep.replace('-', '').replace(' ', '')
        return len(cep_clean) == 8 and cep_clean.isdigit()
    
    def _get_cep_info(self, cep: str) -> Optional[Dict]:
        """Busca informações do CEP via ViaCEP"""
        try:
            cep_clean = cep.replace('-', '').replace(' ', '')
            response = requests.get(self.correios_api_url.format(cep=cep_clean), timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'erro' not in data:
                    return data
            return None
            
        except Exception as e:
            current_app.logger.error(f"Erro ao buscar CEP {cep}: {e}")
            return None
    
    def _calculate_pac(self, cep: str, peso: float, valor: float, dimensoes: Dict) -> Optional[Dict]:
        """Calcula frete PAC (simulado - em produção usar API real dos Correios)"""
        try:
            # Valores simulados baseados em tabelas dos Correios
            # Em produção, usar a API real dos Correios ou Melhor Envio
            
            base_price = 15.50  # Preço base PAC
            weight_factor = peso * 2.50  # R$ 2,50 por kg
            distance_factor = self._get_distance_factor(cep)
            
            total_price = base_price + weight_factor + distance_factor
            
            # Calcular prazo baseado na distância
            delivery_days = self._calculate_delivery_days(cep, 'pac')
            
            return {
                'name': 'PAC',
                'service': 'pac',
                'price': round(total_price, 2),
                'delivery_time': f'{delivery_days}-{delivery_days + 2} dias úteis',
                'delivery_time_days': delivery_days,
                'description': 'Entrega econômica pelos Correios'
            }
            
        except Exception as e:
            current_app.logger.error(f"Erro ao calcular PAC: {e}")
            return None
    
    def _calculate_sedex(self, cep: str, peso: float, valor: float, dimensoes: Dict) -> Optional[Dict]:
        """Calcula frete SEDEX (simulado - em produção usar API real dos Correios)"""
        try:
            # Valores simulados baseados em tabelas dos Correios
            base_price = 25.90  # Preço base SEDEX
            weight_factor = peso * 3.20  # R$ 3,20 por kg
            distance_factor = self._get_distance_factor(cep)
            
            total_price = base_price + weight_factor + distance_factor
            
            # Calcular prazo baseado na distância
            delivery_days = self._calculate_delivery_days(cep, 'sedex')
            
            return {
                'name': 'SEDEX',
                'service': 'sedex',
                'price': round(total_price, 2),
                'delivery_time': f'{delivery_days}-{delivery_days + 1} dias úteis',
                'delivery_time_days': delivery_days,
                'description': 'Entrega expressa pelos Correios'
            }
            
        except Exception as e:
            current_app.logger.error(f"Erro ao calcular SEDEX: {e}")
            return None
    
    def _get_distance_factor(self, cep: str) -> float:
        """Calcula fator de distância baseado no CEP (simulado)"""
        # Em produção, usar uma tabela real de distâncias ou API
        cep_prefix = cep[:3]
        
        # Regiões metropolitanas (menor custo)
        if cep_prefix in ['010', '020', '030', '040', '050', '060', '070', '080', '090']:  # SP
            return 0.0
        elif cep_prefix in ['200', '210', '220', '230', '240', '250']:  # RJ
            return 2.0
        elif cep_prefix in ['300', '310', '320', '330', '340', '350']:  # MG
            return 3.0
            
        # Regiões mais distantes (maior custo)
        elif cep_prefix in ['400', '500', '600', '700', '800', '900']:
            return 8.0
        else:
            return 5.0  # Custo médio
    
    def _calculate_delivery_days(self, cep: str, service: str) -> int:
        """Calcula prazo de entrega baseado no CEP e serviço"""
        cep_prefix = cep[:3]
        
        # Regiões metropolitanas (menor prazo)
        if cep_prefix in ['010', '020', '030', '040', '050', '060', '070', '080', '090']:  # SP
            return 2 if service == 'sedex' else 4
        elif cep_prefix in ['200', '210', '220', '230', '240', '250']:  # RJ
            return 3 if service == 'sedex' else 5
        elif cep_prefix in ['300', '310', '320', '330', '340', '350']:  # MG
            return 4 if service == 'sedex' else 6
            
        # Regiões mais distantes (maior prazo)
        elif cep_prefix in ['400', '500', '600', '700', '800', '900']:
            return 6 if service == 'sedex' else 10
        else:
            return 5 if service == 'sedex' else 8  # Prazo médio
    
    def _calculate_melhor_envio(self, cep_destino: str, peso_total: float, 
                                valor_total: float, dimensoes: Dict) -> List[Dict]:
        """
        Calcula frete usando a API do Melhor Envio
        
        Args:
            cep_destino: CEP de destino (apenas números)
            peso_total: Peso total em kg
            valor_total: Valor total dos produtos
            dimensoes: Dicionário com altura, largura, comprimento em cm
            
        Returns:
            Lista de opções de frete do Melhor Envio
        """
        try:
            melhor_envio_token, cep_origem = self._get_config()
            
            # Limpar CEP (remover traço e espaços)
            cep_origem_clean = cep_origem.replace('-', '').replace(' ', '')
            cep_destino_clean = cep_destino.replace('-', '').replace(' ', '')
            
            if len(cep_origem_clean) != 8 or len(cep_destino_clean) != 8:
                current_app.logger.warning(f"CEPs inválidos: origem={cep_origem_clean}, destino={cep_destino_clean}")
                return []
            
            # Preparar payload para a API do Melhor Envio
            payload = {
                "from": {
                    "postal_code": cep_origem_clean
                },
                "to": {
                    "postal_code": cep_destino_clean
                },
                "products": [
                    {
                        "id": "1",
                        "width": int(dimensoes.get('largura', 20)),
                        "height": int(dimensoes.get('altura', 10)),
                        "length": int(dimensoes.get('comprimento', 30)),
                        "weight": float(peso_total),  # em kg - converter Decimal para float
                        "insurance_value": float(valor_total),  # Converter Decimal para float
                        "quantity": 1
                    }
                ],
                "services": "1,2,3,4,17"  # IDs dos serviços: Correios PAC, Correios SEDEX, Jadlog, Azul, etc.
            }
            
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {melhor_envio_token}",
                "User-Agent": "LhamaBanana Ecommerce (contato@lhamabanana.com)"
            }
            
            current_app.logger.info(f"Calculando frete Melhor Envio: {cep_origem_clean} -> {cep_destino_clean}")
            
            response = requests.post(
                self.melhor_envio_api_url,
                json=payload,
                headers=headers,
                timeout=15
            )
            
            if response.status_code != 200:
                current_app.logger.error(f"Erro na API Melhor Envio: {response.status_code} - {response.text}")
                return []
            
            data = response.json()
            
            # Processar resposta do Melhor Envio
            shipping_options = []
            
            if isinstance(data, list):
                for option in data:
                    # Mapear nomes dos serviços
                    service_names = {
                        '1': 'PAC',
                        '2': 'SEDEX',
                        '3': 'Jadlog',
                        '4': 'Azul Cargo',
                        '17': 'Correios PAC Mini'
                    }
                    
                    service_name = service_names.get(str(option.get('id')), option.get('name', 'Frete'))
                    price = option.get('price', 0)
                    delivery_time = option.get('delivery_time', 0)
                    
                    if price and delivery_time:
                        shipping_options.append({
                            'name': service_name,
                            'service': option.get('id'),
                            'service_name': option.get('name', ''),
                            'price': float(price),
                            'delivery_time': f'{delivery_time} dias úteis',
                            'delivery_time_days': int(delivery_time),
                            'description': option.get('company', {}).get('name', '') or f'Entrega via {service_name}'
                        })
            
            # Ordenar por preço (mais barato primeiro)
            shipping_options.sort(key=lambda x: x['price'])
            
            current_app.logger.info(f"Melhor Envio retornou {len(shipping_options)} opções de frete")
            
            return shipping_options
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Erro de conexão com Melhor Envio: {e}")
            return []
        except Exception as e:
            current_app.logger.error(f"Erro ao calcular frete Melhor Envio: {e}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            return []

# Instância global do serviço
shipping_service = ShippingService()
