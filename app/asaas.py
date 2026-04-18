import os
import requests

def get_headers():
    return {
        "accept": "application/json",
        "access_token": os.getenv("ASAAS_API_KEY")
    }

def get_base_url():
    # Puxa do .env, se não achar usa a URL de testes (sandbox)
    return os.getenv("ASAAS_API_URL", "https://sandbox.asaas.com/api/v3")

def obter_ou_criar_cliente(empresa):
    """Busca o cliente no Asaas pelo CNPJ. Se não existir, cria automaticamente."""
    url = f"{get_base_url()}/customers?cpfCnpj={empresa.cnpj}"
    response = requests.get(url, headers=get_headers())

    if response.status_code == 200:
        data = response.json()
        if data.get("data") and len(data["data"]) > 0:
            return data["data"][0]["id"] # Retorna o ID do cliente se já existir

    # Se não existe no Asaas, vamos criar
    url_create = f"{get_base_url()}/customers"
    payload = {
        "name": empresa.razao_social,
        "cpfCnpj": empresa.cnpj,
        "email": empresa.email,
        "phone": empresa.telefone,
        "mobilePhone": empresa.telefone,
        "postalCode": empresa.cep,
        "address": empresa.logradouro,
        "addressNumber": empresa.numero,
        "complement": empresa.complemento,
        "province": empresa.bairro,
        "city": empresa.cidade,
        "state": empresa.estado
    }
    # Remove campos vazios para não dar erro na API
    payload = {k: v for k, v in payload.items() if v}

    resp_create = requests.post(url_create, json=payload, headers=get_headers())
    if resp_create.status_code == 200:
        return resp_create.json()["id"]

    print("Erro ao criar cliente no Asaas:", resp_create.text)
    return None

def criar_cobranca(empresa, fatura):
    """Gera a cobrança (Boleto/Pix) no Asaas para uma fatura do nosso sistema."""
    customer_id = obter_ou_criar_cliente(empresa)
    if not customer_id:
        return None, None

    url = f"{get_base_url()}/payments"
    payload = {
        "customer": customer_id,
        "billingType": "UNDEFINED", # "UNDEFINED" permite que o cliente escolha entre PIX ou Boleto na tela do Asaas
        "dueDate": fatura.data_vencimento.strftime("%Y-%m-%d"),
        "value": float(fatura.valor_total),
        "description": f"SindiMedic Saúde - Competência {fatura.competencia} ({fatura.quantidade_vidas} vidas)",
        "postalService": False
    }

    response = requests.post(url, json=payload, headers=get_headers())

    if response.status_code == 200:
        data = response.json()
        # Retorna o ID da cobrança (gateway_id) e o Link oficial (invoiceUrl)
        return data["id"], data["invoiceUrl"]

    print("Erro ao gerar cobrança no Asaas:", response.text)
    return None, None