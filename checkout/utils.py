import os
import requests
from decimal import Decimal
from datetime import datetime, timezone, timedelta
import logging
import re

logger = logging.getLogger(__name__)


def validar_cpf(cpf):
    """
    Valida um CPF (apenas dígitos verificadores, não verifica na Receita).
    Retorna True se válido, False caso contrário.
    """
    cpf = re.sub(r'\D',
                 '',
                 cpf)

    if len(cpf) != 11:
        return False

    if cpf == cpf[0] * 11:
        return False

    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto

    if int(cpf[9]) != digito1:
        return False

    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto

    if int(cpf[10]) != digito2:
        return False

    return True


def limpar_cpf(cpf):
    """
    Remove caracteres não numéricos do CPF.
    """
    if not cpf:
        return None
    return re.sub(r'\D',
                  '',
                  str(cpf))


def _refresh_melhor_envio_token(refresh_token):
    """
    Solicita um novo Access Token usando o Refresh Token.
    """
    token_url = "https://sandbox.melhorenvio.com.br/oauth/token"

    client_id = os.getenv('ME_CLIENT_ID')
    client_secret = os.getenv('ME_CLIENT_SECRET')
    refresh_token = os.getenv('FRETE_REFRESH_TOKEN')

    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id,
        'client_secret': client_secret,
    }

    logger.info("[TOKEN] Solicitando novo Access Token via Refresh Token.")

    try:
        response = requests.post(token_url,
                                 data=payload)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logger.error(f"[TOKEN]  Erro ao renovar token. Verifique CLIENT_ID/SECRET ou Refresh Token: {e.response.text}")
        raise Exception(f"Falha na renovação do token do Melhor Envio: {e.response.text}")

    data = response.json()

    new_access_token = data['access_token']
    new_refresh_token = data.get('refresh_token',
                                 refresh_token)

    os.environ['FRETE_ACCESS_TOKEN'] = new_access_token
    os.environ['FRETE_REFRESH_TOKEN'] = new_refresh_token

    logger.info("[TOKEN]  Access Token renovado e atualizado na memória da Task.")

    return new_access_token


def get_valid_melhor_envio_access_token():
    """
    Retorna o Access Token atual, renovando-o se necessário.
    """
    current_access_token = os.getenv("FRETE_ACCESS_TOKEN")

    try:
        current_refresh_token = os.getenv("FRETE_REFRESH_TOKEN")
    except Exception:
        logger.error("[TOKEN]  FRETE_REFRESH_TOKEN não configurado no .env.")
        raise Exception("Refresh Token não encontrado para renovação.")

    return _refresh_melhor_envio_token(current_refresh_token)


def obter_service_id_do_nome(service_name, from_postal_code, to_postal_code,
                             package, insurance_value, access_token):
    """
    Consulta os serviços disponíveis e retorna o ID do serviço que corresponde ao nome escolhido pelo cliente.
    Se não encontrar, retorna o serviço mais barato disponível.
    """
    base_url = "https://sandbox.melhorenvio.com.br/api/v2/me"

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'suporte.balm@gmail.com'
    }

    calc_url = f"{base_url}/shipment/calculate"

    payload = {
        "from": {"postal_code": from_postal_code},
        "to": {"postal_code": to_postal_code},
        "package": package,
        "options": {
            "insurance_value": insurance_value,
            "receipt": False,
            "own_hand": False
        }
    }

    logger.info(f"[SERVICE] Buscando ID do serviço '{service_name}'")

    try:
        response = requests.post(calc_url,
                                 json=payload,
                                 headers=headers)

        if response.status_code != 200:
            logger.error(f"[SERVICE] Erro ao consultar serviços: {response.text}")
            raise Exception(f"Erro ao consultar serviços disponíveis: {response.status_code} - {response.text}")

        services = response.json()

        available_services = [s for s in services if not s.get('error')]

        if not available_services:
            logger.error(f"[SERVICE]  Nenhum serviço disponível para esta rota")
            logger.error(f"[SERVICE] Serviços retornados: {services}")
            raise Exception("Nenhum serviço de entrega disponível para esta rota. Verifique CEPs e dimensões.")

        service_name_lower = service_name.lower() if service_name else ''

        for service in available_services:
            if service_name_lower in service['name'].lower():
                logger.info(f"[SERVICE] Serviço encontrado: {service['name']} (ID: {service['id']}) - R$ {service['price']}")
                return str(service['id'])

        logger.warning(f"[SERVICE] ️ Serviço '{service_name}' não encontrado. Usando o mais barato disponível.")
        available_services.sort(key=lambda x: float(x.get('price',
                                                          999999)))
        selected = available_services[0]
        logger.info(f"[SERVICE] Serviço selecionado (fallback): {selected['name']} (ID: {selected['id']}) - R$ {selected['price']}")

        return str(selected['id'])

    except requests.exceptions.RequestException as e:
        logger.error(f"[SERVICE]  Erro de conexão ao consultar serviços: {str(e)}")
        raise Exception(f"Erro de conexão com Melhor Envio: {str(e)}")


def gerar_etiqueta_melhor_envio(order):
    """
    Integra com a API do Melhor Envio para gerar etiqueta de envio.
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

    total_weight = 0
    max_height = 0
    max_width = 0
    max_length = 0

    for item in order.items.all():
        if item.product.size:
            size = item.product.size
            total_weight += (size.weight or 0.3) * item.quantity
            max_height = max(max_height,
                             size.height or 5)
            max_width = max(max_width,
                            size.width or 5)
            max_length = max(max_length,
                             size.length or 10)

    package = {
        'weight': max(total_weight,
                      0.3),
        'height': max(max_height,
                      2),
        'width': max(max_width,
                     11),
        'length': max(max_length,
                      16),
    }

    address = order.address

    from_postal_code = '93800192'
    from_data = {
        'name': 'Manuela Braun Santos',
        'phone': '51996065712',
        'email': 'bruno.rsilva2004@gmail.com',
        'document': '03932851030',
        'postal_code': from_postal_code,
        'address': 'Rua Chui',
        'number': '123',
        'district': 'Centro',
        'city': 'Sapiranga',
        'state_abbr': 'RS',
        'country_id': 'BR',
    }

    cpf_raw = None

    if order.client.cpf:
        cpf_raw = order.client.cpf
        logger.info(f"[SERVICE] CPF obtido do cliente: {cpf_raw}")
    elif hasattr(order,
                 'payment') and order.payment.payer_document:
        cpf_raw = order.payment.payer_document
        logger.info(f"[SERVICE] CPF obtido do pagamento: {cpf_raw}")

    cpf = limpar_cpf(cpf_raw)

    if not cpf or not validar_cpf(cpf):
        logger.error(f"[SERVICE] CPF inválido para pedido #{order.id}: '{cpf_raw}' (limpo: '{cpf}')")
        raise Exception(
            f"CPF inválido ou não encontrado para o pedido #{order.id}. "
            f"CPF fornecido: '{cpf_raw}'. Verifique o cadastro do cliente."
        )

    logger.info(f"[SERVICE] CPF validado: {cpf}")

    to_postal_code = address.zipcode.replace('-',
                                             '')
    to_data = {
        'name': f"{order.client.first_name} {order.client.last_name}".strip(),
        'phone': order.client.phone_number or '11999999999',
        'email': order.client.email,
        'document': cpf,
        'postal_code': to_postal_code,
        'address': address.street,
        'number': address.number,
        'complement': address.complement or '',
        'district': address.neighborhood,
        'city': address.city,
        'country_id': 'BR',
        'state_abbr': address.state,
    }

    # 5. OBTER SERVICE_ID DO SERVIÇO ESCOLHIDO PELO CLIENTE
    if not hasattr(order,
                   'shipping') or not order.shipping:
        raise Exception(f"Pedido #{order.id} não possui registro de Shipping associado")

    service_name = order.shipping.carrier
    logger.info(f"[SERVICE] Serviço escolhido pelo cliente: '{service_name}'")

    try:
        service_id = obter_service_id_do_nome(
            service_name=service_name,
            from_postal_code=from_postal_code,
            to_postal_code=to_postal_code,
            package=package,
            insurance_value=float(order.total),
            access_token=access_token
        )
    except Exception as e:
        logger.error(f"[SERVICE]  Erro ao obter service_id: {str(e)}")
        raise

    logger.info(f"[SERVICE] Service ID a ser usado: {service_id}")


    payload = {
        'service': service_id,
        'from': from_data,
        'to': to_data,
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
            'insurance_value': float(order.total),
            'receipt': False,
            'own_hand': False,
            'reverse': False,
            'non_commercial': True,
            'platform': 'Balm E-commerce',
        }
    }

    logger.info(f"[SERVICE] Payload montado: {payload}")

    try:

        logger.info(f"[SERVICE] Criando pedido de envio na API...")
        cart_url = f"{base_url}/cart"
        cart_response = requests.post(cart_url,
                                      json=payload,
                                      headers=headers)

        if cart_response.status_code != 201:
            logger.error(f"[SERVICE] Erro ao criar pedido: {cart_response.text}")
            raise Exception(f"Erro na API Melhor Envio (cart): {cart_response.status_code} - {cart_response.text}")

        cart_data = cart_response.json()
        melhor_envio_id = cart_data.get('id')
        logger.info(f"[SERVICE] Pedido criado: ID {melhor_envio_id}")

        # Checkout
        logger.info(f"[SERVICE] Finalizando compra...")
        checkout_url = f"{base_url}/shipment/checkout"
        checkout_payload = {'orders': [melhor_envio_id]}
        checkout_response = requests.post(checkout_url,
                                          json=checkout_payload,
                                          headers=headers)

        if checkout_response.status_code != 200:
            logger.error(f"[SERVICE] Erro ao finalizar: {checkout_response.text}")
            raise Exception(
                f"Erro na API Melhor Envio (checkout): {checkout_response.status_code} - {checkout_response.text}")

        # Gerar etiqueta
        logger.info(f"[SERVICE] Gerando etiqueta...")
        label_url = f"{base_url}/shipment/generate"
        label_payload = {'orders': [melhor_envio_id]}
        label_response = requests.post(label_url,
                                       json=label_payload,
                                       headers=headers)

        if label_response.status_code != 200:
            logger.error(f"[SERVICE] Erro ao gerar etiqueta: {label_response.text}")
            raise Exception(f"Erro na API Melhor Envio (label): {label_response.status_code} - {label_response.text}")

        # Obter URL de impressão
        print_url = f"{base_url}/shipment/print"
        print_payload = {'mode': 'private', 'orders': [melhor_envio_id]}
        print_response = requests.post(print_url,
                                       json=print_payload,
                                       headers=headers)

        if print_response.status_code != 200:
            logger.error(f"[SERVICE] Erro ao buscar URL: {print_response.text}")
            raise Exception(f"Erro na API Melhor Envio (print): {print_response.status_code} - {print_response.text}")

        print_data = print_response.json()
        label_url_pdf = print_data.get('url')
        tracking_code = cart_data.get('tracking') or f"ME{melhor_envio_id}"

        logger.info(f"[SERVICE] Etiqueta gerada com sucesso!")
        logger.info(f"[SERVICE] Tracking: {tracking_code}")
        logger.info(f"[SERVICE] URL: {label_url_pdf}")

        return {
            'tracking_code': tracking_code,
            'label_url': label_url_pdf,
            'melhor_envio_id': melhor_envio_id,
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"[SERVICE]  Erro de conexão com API: {str(e)}")
        raise Exception(f"Erro de conexão com Melhor Envio: {str(e)}")
    except Exception as e:
        logger.error(f"[SERVICE] Erro inesperado: {str(e)}")
        raise