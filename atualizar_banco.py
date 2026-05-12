import os
from dotenv import load_dotenv
load_dotenv()
from app import create_app
from app.models import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        # Primeiro, usamos o recurso mágico do SQLAlchemy de ler as classes Models e criar as que faltam
        # (Isso vai criar a tabela 'escritorios' automaticamente)
        db.create_all()
        
        # Agora, inserimos as chaves estrangeiras manualmente na Empresa e no Usuario
        db.session.execute(text("ALTER TABLE empresas ADD COLUMN escritorio_id INTEGER;"))
        db.session.execute(text("ALTER TABLE empresas ADD CONSTRAINT fk_empresa_escritorio FOREIGN KEY (escritorio_id) REFERENCES escritorios (id);"))
        
        db.session.execute(text("ALTER TABLE usuarios ADD COLUMN escritorio_id INTEGER;"))
        db.session.execute(text("ALTER TABLE usuarios ADD CONSTRAINT fk_usuario_escritorio FOREIGN KEY (escritorio_id) REFERENCES escritorios (id);"))
        
        db.session.commit()
        print("✅ SUCESSO: O banco de dados foi atualizado para a FASE 2 (Escritórios)!")
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERRO: {e}")