import requests
from decouple import config

def calcular_frete_melhor_envio(cep_origem, cep_destino, product_list):
            '''
            Função que conecta com a API do Melhor Envio para fazer a cotação do frete, com base nos produtos que estão no carrinho do cliente, e o cep de origem e destino informado.
            '''
            url = "https://sandbox.melhorenvio.com.br/api/v2/me/shipment/calculate"

            access_token = config("FRETE_API_KEY")
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                "User-Agent": "suporte.balm@gmail.com"
            }

            data = {
                'from': {'postal_code': cep_origem},
                'to': {'postal_code': cep_destino},
                'products': product_list,
                #transformar o 'services' para conseguir definir no admin no futuro
                'services': '1,2,3,8,13',
            }

            response = requests.post(url, json=data, headers=headers)
            if response.status_code==200:
                return response.json()
            else:
                raise Exception(f'Erro na API Melhor Envio: {response.status_code} {response.text}')
            

CEPS_DISPONIVEIS_RETIRADA = [
       '93800',
       '93700',

]

def verificar_disponibilidade_retirada(cep_destino):
    """
    Verifica se o CEP informado começa com algum dos prefixos permitidos para retirada.
    """
    cep_limpo = cep_destino.replace('-', '').strip()
    
    for prefixo in CEPS_DISPONIVEIS_RETIRADA:
        if cep_limpo.startswith(prefixo):
            return True
    return False