import os
from dotenv import load_dotenv

# 1. Força o Python a ler o arquivo .env antes de fazer qualquer coisa
load_dotenv()

from app import create_app
from app.models import db
from sqlalchemy import text

# Apenas para termos certeza visual de que ele pegou o Neon:
banco_url = os.getenv("DATABASE_URL", "NENHUM_BANCO_ENCONTRADO")
print(f"Tentando conectar em: {banco_url[:20]}...")

app = create_app()

with app.app_context():
    try:
        # Comando SQL direto para adicionar a coluna (PostgreSQL)
        db.session.execute(text("ALTER TABLE usuarios ADD COLUMN clinica_id INTEGER;"))
        
        # Adiciona a regra de chave estrangeira
        db.session.execute(text("ALTER TABLE usuarios ADD CONSTRAINT fk_usuario_clinica FOREIGN KEY (clinica_id) REFERENCES clinicas (id);"))
        
        db.session.commit()
        print("✅ SUCESSO: A coluna 'clinica_id' foi adicionada à tabela usuarios no Neon!")
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERRO: {e}")