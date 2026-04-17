# reset_db.py
from app import create_app, db
from app.models import Empresa, Trabalhador, Fatura

app = create_app()

with app.app_context():
    print("Removendo banco de dados antigo...")
    db.drop_all()
    print("Criando novas tabelas (Empresas, Trabalhadores, Faturas)...")
    db.create_all()
    print("Sucesso! Banco de Dados pronto para a nova estrutura modular.")