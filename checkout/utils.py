import requests
import os
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


def gerar_etiqueta_melhor_envio(order):
    """
    Integra com a API do Melhor Envio para gerar etiqueta de envio.
    
    Args:
        order: Instância do modelo Order
        
    Returns:
        dict: {
            'tracking_code': str,
            'label_url': str,
            'melhor_envio_id': str
        }
        
    Raises:
        Exception: Se a API falhar ou retornar erro
    """
    
    access_token = os.getenv("FRETE_API_KEY")
    base_url = "https://sandbox.melhorenvio.com.br/api/v2/me"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'suporte.balm@gmail.com'
    }
    
    logger.info(f"[SERVICE] Montando dados para pedido #{order.id}")
    
    products = []
    for item in order.items.all():
        product = item.product
        
        if not product.size:
            raise Exception(f"Produto '{product.name}' não tem tamanho configurado")
        
        products.append({
            'name': product.name,
            'quantity': item.quantity,
            'unitary_value': float(item.price),
        })
    
    # 2.2 Dimensões e peso do pacote (somando todos os itens)
    # Nota: Isso é uma simplificação. Idealmente você deve calcular o volume total
    total_weight = 0
    max_height = 0
    max_width = 0
    max_length = 0
    
    for item in order.items.all():
        if item.product.size:
            size = item.product.size
            total_weight += (size.weight or 0.3) * item.quantity  # Default 300g se não tiver peso
            max_height = max(max_height, size.height or 5)
            max_width = max(max_width, size.width or 5)
            max_length = max(max_length, size.length or 10)
    
    package = {
        'weight': max(total_weight, 0.3),  # Mínimo 300g
        'height': max(max_height, 2),      # Mínimo 2cm
        'width': max(max_width, 11),       # Mínimo 11cm
        'length': max(max_length, 16),     # Mínimo 16cm
    }
    
    address = order.address
    
    from_data = {
        'postal_code': '93800192',  # ajustar futuramente 
    }
    
    to_data = {
        'postal_code': address.zipcode.replace('-', ''),
        'address': address.street,
        'number': address.number,
        'complement': address.complement or '',
        'neighborhood': address.neighborhood,
        'city': address.city,
        'state': address.state,
    }
    
    # 3. Payload para criar o pedido de envio
    
    payload = {
        'service': order.shipping.carrier or '1',  # ID do serviço escolhido na cotação - verificar se está puxando corretamente
        'agency': None,  # Agência (se aplicável)
        'from': from_data,
        'to': to_data,
        'package': package,
        'products': products,
        'volumes': [
            {
                'height': package['height'],
                'width': package['width'],
                'length': package['length'],
                'weight': package['weight'],
            }
        ],
        'options': {
            'insurance_value': float(order.total),  # Valor do seguro 
            'receipt': False,  # Aviso de recebimento
            'own_hand': False,  # Mão própria
            'reverse': False,  # Envio reverso
            'non_commercial': True,  # Não comercial
            'invoice': {
                'key': f"ORDER-{order.id}",  # Chave da nota fiscal
            },
            'platform': 'Balm E-commerce',
        }
    }
    
    logger.info(f"[SERVICE] Payload montado: {payload}")
    
    try:
        logger.info(f"[SERVICE] Criando pedido de envio na API...")
        cart_url = f"{base_url}/cart"
        cart_response = requests.post(cart_url, json=payload, headers=headers)
        
        if cart_response.status_code != 201:
            logger.error(f"[SERVICE] Erro ao criar pedido: {cart_response.text}")
            raise Exception(f"Erro na API Melhor Envio (cart): {cart_response.status_code} - {cart_response.text}")
        
        cart_data = cart_response.json()
        melhor_envio_id = cart_data.get('id')
        logger.info(f"[SERVICE] Pedido criado: ID {melhor_envio_id}")
        
        logger.info(f"[SERVICE] Finalizando compra...")
        checkout_url = f"{base_url}/shipment/checkout"
        checkout_payload = {
            'orders': [melhor_envio_id]
        }
        checkout_response = requests.post(checkout_url, json=checkout_payload, headers=headers)
        
        if checkout_response.status_code != 200:
            logger.error(f"[SERVICE] Erro ao finalizar: {checkout_response.text}")
            raise Exception(f"Erro na API Melhor Envio (checkout): {checkout_response.status_code} - {checkout_response.text}")
        
        checkout_data = checkout_response.json()
        logger.info(f"[SERVICE] Compra finalizada: {checkout_data}")
        
        logger.info(f"[SERVICE] Gerando etiqueta...")
        label_url = f"{base_url}/shipment/generate"
        label_payload = {
            'orders': [melhor_envio_id]
        }
        label_response = requests.post(label_url, json=label_payload, headers=headers)
        
        if label_response.status_code != 200:
            logger.error(f"[SERVICE] Erro ao gerar etiqueta: {label_response.text}")
            raise Exception(f"Erro na API Melhor Envio (label): {label_response.status_code} - {label_response.text}")
        
        label_data = label_response.json()
        logger.info(f"[SERVICE] Etiqueta gerada: {label_data}")
        
        print_url = f"{base_url}/shipment/print"
        print_payload = {
            'mode': 'private',
            'orders': [melhor_envio_id]
        }
        print_response = requests.post(print_url, json=print_payload, headers=headers)
        
        if print_response.status_code != 200:
            logger.error(f"[SERVICE] Erro ao buscar URL: {print_response.text}")
            raise Exception(f"Erro na API Melhor Envio (print): {print_response.status_code} - {print_response.text}")
        
        print_data = print_response.json()
        label_url_pdf = print_data.get('url')
        
        tracking_code = cart_data.get('tracking') or f"ME{melhor_envio_id}"
        
        logger.info(f"[SERVICE] ✅ Etiqueta gerada com sucesso!")
        logger.info(f"[SERVICE] Tracking: {tracking_code}")
        logger.info(f"[SERVICE] URL: {label_url_pdf}")
        
        return {
            'tracking_code': tracking_code,
            'label_url': label_url_pdf,
            'melhor_envio_id': melhor_envio_id,
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"[SERVICE] ❌ Erro de conexão com API: {str(e)}")
        raise Exception(f"Erro de conexão com Melhor Envio: {str(e)}")
        
    except Exception as e:
        logger.error(f"[SERVICE] ❌ Erro inesperado: {str(e)}")
        raise