import requests
import json
from flask import current_app
from typing import Dict, List, Optional, Tuple
from .db import get_db

class LabelService:
    """Serviço para criação e gerenciamento de etiquetas de frete via Melhor Envio"""
    
    def __init__(self):
        self.api_base_url = "https://melhorenvio.com.br/api/v2/me"
        self._token = None
        self._cep_origem = None
    
    def _get_config(self) -> Tuple[str, str]:
        """Carrega configurações do Melhor Envio dinamicamente"""
        try:
            if self._token is None:
                self._token = current_app.config.get('MELHOR_ENVIO_TOKEN', '')
            if self._cep_origem is None:
                self._cep_origem = current_app.config.get('MELHOR_ENVIO_CEP_ORIGEM', '')
            return self._token, self._cep_origem
        except RuntimeError:
            return '', ''
    
    def _get_headers(self) -> Dict[str, str]:
        """Retorna headers para requisições à API do Melhor Envio"""
        token, _ = self._get_config()
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "LhamaBanana Ecommerce (contato@lhamabanana.com)"
        }
    
    def create_shipment(self, venda_id: int, order_data: Dict, shipping_option: Dict) -> Dict:
        """
        Cria um envio (shipment) no Melhor Envio
        
        Args:
            venda_id: ID da venda no banco de dados
            order_data: Dados do pedido (endereço, produtos, etc)
            shipping_option: Opção de frete selecionada
            
        Returns:
            Dados do envio criado no Melhor Envio
        """
        try:
            token, cep_origem = self._get_config()
            if not token or not cep_origem:
                raise ValueError("Token ou CEP de origem não configurados")
            
            # Preparar payload para criar envio
            payload = {
                "service": int(shipping_option.get('service', 1)),
                "from": {
                    "name": current_app.config.get('MELHOR_ENVIO_NOME_LOJA', 'LhamaBanana'),
                    "phone": current_app.config.get('MELHOR_ENVIO_TELEFONE_LOJA', ''),
                    "email": current_app.config.get('MELHOR_ENVIO_EMAIL_LOJA', 'contato@lhamabanana.com'),
                    "document": current_app.config.get('MELHOR_ENVIO_CNPJ_LOJA', ''),
                    "company_document": current_app.config.get('MELHOR_ENVIO_CNPJ_LOJA', ''),
                    "state_register": current_app.config.get('MELHOR_ENVIO_IE_LOJA', ''),
                    "address": current_app.config.get('MELHOR_ENVIO_ENDERECO_LOJA', ''),
                    "complement": current_app.config.get('MELHOR_ENVIO_COMPLEMENTO_LOJA', ''),
                    "number": current_app.config.get('MELHOR_ENVIO_NUMERO_LOJA', ''),
                    "district": current_app.config.get('MELHOR_ENVIO_BAIRRO_LOJA', ''),
                    "city": current_app.config.get('MELHOR_ENVIO_CIDADE_LOJA', ''),
                    "state_abbr": current_app.config.get('MELHOR_ENVIO_ESTADO_LOJA', ''),
                    "country_id": "BR",
                    "postal_code": cep_origem.replace('-', '').replace(' ', '')
                },
                "to": {
                    "name": order_data.get('nome_recebedor', ''),
                    "phone": order_data.get('telefone', ''),
                    "email": order_data.get('email', ''),
                    "document": order_data.get('cpf', ''),
                    "address": order_data.get('rua', ''),
                    "complement": order_data.get('complemento', ''),
                    "number": order_data.get('numero', ''),
                    "district": order_data.get('bairro', ''),
                    "city": order_data.get('cidade', ''),
                    "state_abbr": order_data.get('estado', ''),
                    "country_id": "BR",
                    "postal_code": order_data.get('cep', '').replace('-', '').replace(' ', '')
                },
                "products": order_data.get('produtos', []),
                "volumes": [
                    {
                        "height": shipping_option.get('dimensoes', {}).get('altura', 10),
                        "width": shipping_option.get('dimensoes', {}).get('largura', 20),
                        "length": shipping_option.get('dimensoes', {}).get('comprimento', 30),
                        "weight": shipping_option.get('peso_total', 1.0)
                    }
                ],
                "options": {
                    "insurance_value": order_data.get('valor_total', 0),
                    "receipt": False,
                    "own_hand": False,
                    "reverse": False,
                    "non_commercial": True,
                    "invoice": {
                        "key": ""
                    },
                    "platform": "LhamaBanana"
                }
            }
            
            current_app.logger.info(f"Criando envio no Melhor Envio para venda {venda_id}")
            
            response = requests.post(
                f"{self.api_base_url}/shipment",
                json=payload,
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code not in [200, 201]:
                error_text = response.text
                current_app.logger.error(f"Erro ao criar envio Melhor Envio: {response.status_code} - {error_text}")
                raise Exception(f"Erro na API Melhor Envio: {response.status_code} - {error_text}")
            
            data = response.json()
            current_app.logger.info(f"Envio criado com sucesso. ID: {data.get('id')}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Erro de conexão ao criar envio Melhor Envio: {e}")
            raise
        except Exception as e:
            current_app.logger.error(f"Erro ao criar envio Melhor Envio: {e}")
            raise
    
    def checkout_shipment(self, shipment_id: int) -> Dict:
        """
        Faz checkout (paga) do envio no Melhor Envio
        
        Args:
            shipment_id: ID do envio no Melhor Envio
            
        Returns:
            Dados do checkout realizado
        """
        try:
            current_app.logger.info(f"Fazendo checkout do envio {shipment_id} no Melhor Envio")
            
            response = requests.post(
                f"{self.api_base_url}/shipment/checkout",
                json={"orders": [shipment_id]},
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code != 200:
                error_text = response.text
                current_app.logger.error(f"Erro ao fazer checkout: {response.status_code} - {error_text}")
                raise Exception(f"Erro ao fazer checkout: {response.status_code}")
            
            data = response.json()
            current_app.logger.info(f"Checkout realizado com sucesso para envio {shipment_id}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Erro de conexão ao fazer checkout: {e}")
            raise
        except Exception as e:
            current_app.logger.error(f"Erro ao fazer checkout: {e}")
            raise
    
    def print_label(self, shipment_id: int) -> Dict:
        """
        Gera link para impressão da etiqueta
        
        Args:
            shipment_id: ID do envio no Melhor Envio
            
        Returns:
            Dados com URL para impressão da etiqueta
        """
        try:
            current_app.logger.info(f"Gerando link de impressão para envio {shipment_id}")
            
            response = requests.get(
                f"{self.api_base_url}/shipment/print",
                params={"orders[]": shipment_id},
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code != 200:
                error_text = response.text
                current_app.logger.error(f"Erro ao gerar link de impressão: {response.status_code} - {error_text}")
                raise Exception(f"Erro ao gerar link de impressão: {response.status_code}")
            
            data = response.json()
            return data
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Erro de conexão ao gerar link de impressão: {e}")
            raise
        except Exception as e:
            current_app.logger.error(f"Erro ao gerar link de impressão: {e}")
            raise
    
    def track_shipment(self, shipment_id: int) -> Dict:
        """
        Rastreia um envio no Melhor Envio
        
        Args:
            shipment_id: ID do envio no Melhor Envio
            
        Returns:
            Dados de rastreamento do envio
        """
        try:
            response = requests.get(
                f"{self.api_base_url}/shipment/{shipment_id}/tracking",
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code != 200:
                error_text = response.text
                current_app.logger.error(f"Erro ao rastrear envio: {response.status_code} - {error_text}")
                raise Exception(f"Erro ao rastrear envio: {response.status_code}")
            
            data = response.json()
            return data
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Erro de conexão ao rastrear envio: {e}")
            raise
        except Exception as e:
            current_app.logger.error(f"Erro ao rastrear envio: {e}")
            raise
    
    def cancel_shipment(self, shipment_id: int) -> Dict:
        """
        Cancela um envio no Melhor Envio
        
        Args:
            shipment_id: ID do envio no Melhor Envio
            
        Returns:
            Dados da cancelamento
        """
        try:
            current_app.logger.info(f"Cancelando envio {shipment_id}")
            
            response = requests.post(
                f"{self.api_base_url}/shipment/cancel",
                json={"id": shipment_id},
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code != 200:
                error_text = response.text
                current_app.logger.error(f"Erro ao cancelar envio: {response.status_code} - {error_text}")
                raise Exception(f"Erro ao cancelar envio: {response.status_code}")
            
            data = response.json()
            current_app.logger.info(f"Envio {shipment_id} cancelado com sucesso")
            
            return data
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Erro de conexão ao cancelar envio: {e}")
            raise
        except Exception as e:
            current_app.logger.error(f"Erro ao cancelar envio: {e}")
            raise

# Instância global do serviço
label_service = LabelService()

