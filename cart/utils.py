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
    '93810',
    '93815',
    '93820',
    '93830',
    '93700',

]

CIDADES_DISPONIVEIS_RETIRADA = [
    'SAPIRANGA',
]

def verificar_disponibilidade_retirada(cep_destino):
    """
    Verifica se o CEP informado começa com algum dos prefixos permitidos para retirada.
    """
    cep_limpo = cep_destino.replace('-', '').strip()

    try:
        # Consulta na BrasilAPI (rápida e moderna)
        response = requests.get(f"https://brasilapi.com.br/api/cep/v1/{cep_limpo}")

        if response.status_code == 200:
            dados = response.json()
            cidade = dados['city']

            if cidade in CIDADES_DISPONIVEIS_RETIRADA:
                return True, f"Retirada disponível para {cidade}!"
            else:
                return False
        else:
            return False, "CEP inválido ou não encontrado."

    except Exception as e:
        return False, "Erro ao consultar serviço de CEP."