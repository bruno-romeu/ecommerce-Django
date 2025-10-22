import requests
from decouple import config

def calcular_frete_melhor_envio(cep_origem, cep_destino, id, peso, altura, largura, comprimento, value, quantity):
            url = "https://www.melhorenvio.com.br/api/v2/me/shipment/calculate"
            headers = {
                'Authorization': config("FRETE_API_KEY"),
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                "User-Agent": "suporte.balm@gmail.com"
            }

            data = {
                'from': {'postal_code': cep_origem},
                'to': {'postal_code': cep_destino},
                'products':[
                    {
                        'id': id,
                        'weight': peso,
                        'width': largura,
                        'height': altura,
                        'length': comprimento,
                        #Valor do produto que será utilizado para o cálculo do seguro do frete
                        'insurance_value': value,
                        'quantity': quantity
                    }
                ],
                'services': '1,2,3,8,13',
            }

            response = requests.post(url, json=data, headers=headers)
            if response.status_code==200:
                return response.json()
            else:
                raise Exception(f'Erro na API Melhor Envio: {response.status_code} {response.text}')