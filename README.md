\# 🏥 Ecossistema Saúde - SaaS B2B



Uma plataforma SaaS completa para gestão de benefícios de saúde corporativa. O sistema permite que o RH das empresas faça a gestão autônoma de vidas ativas, faturamento inteligente com integração bancária e conformidade com a LGPD.



\## 🚀 Funcionalidades

\- \*\*Portal Admin:\*\* Gestão de clientes, planos e visão geral de faturamento.

\- \*\*Portal do Cliente:\*\* Inclusão/Inativação de funcionários e emissão de boletos via slug (`/portal/nome-da-empresa`).

\- \*\*Automação Financeira:\*\* Motor de faturamento e robô de varredura de vencimentos.

\- \*\*Vitrine Digital:\*\* Site institucional integrado para compliance com Gateways de Pagamento (Asaas/Cora).



\## 🛠️ Tecnologias Utilizadas

\- \*\*Backend:\*\* Python, Flask, Flask-SQLAlchemy, Flask-Login

\- \*\*Frontend:\*\* HTML5, Bootstrap 5, Vanilla JS

\- \*\*APIs:\*\* ViaCEP, BrasilAPI (CNPJ)



\## ⚙️ Como rodar o projeto localmente

1\. Clone este repositório: `git clone https://github.com/SEU-USUARIO/ecossistema-saude.git`

2\. Crie um ambiente virtual: `python -m venv venv`

3\. Ative o ambiente: `venv\\Scripts\\activate` (Windows)

4\. Instale as dependências: `pip install -r requirements.txt`

5\. Popule o banco de dados para testes: `python seed\_db.py`

6\. Inicie o servidor: `python run.py`

