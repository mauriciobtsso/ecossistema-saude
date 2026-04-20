# app/__init__.py
import os
from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from .models import db, Usuario

login_manager = LoginManager()
mail = Mail()

def create_app():
    app = Flask(__name__)
    
    # 1. Configuração Dinâmica do Banco de Dados (PostgreSQL no Render ou SQLite local)
    uri = os.getenv("DATABASE_URL")
    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
        
    app.config['SQLALCHEMY_DATABASE_URI'] = uri or 'sqlite:///saas_saude.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- A MÁGICA CONTRA A QUEDA DE CONEXÃO DO NEON AQUI ---
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,  # Testa a conexão antes de usar (evita o erro 'server closed')
        "pool_recycle": 300,    # Força a reciclagem da conexão a cada 5 minutos
    }
    # -------------------------------------------------------

    # 2. Chave secreta dinâmica
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", 'uma-chave-muito-segura-pode-mudar-depois')

    # 3. CONFIGURAÇÕES DO FLASK-MAIL (Lendo do .env)
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

    # 4. INICIALIZAÇÃO DAS EXTENSÕES (Rigorosamente UMA única vez)
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    
    # 5. Configuração do Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Acesso restrito. Por favor, faça login."
    login_manager.login_message_category = "warning"

    # Loader de usuário
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # 6. Importação e Registro dos Blueprints
    from .admin.routes import admin_bp
    from .cliente.routes import cliente_bp
    from .auth import auth_bp
    from .site.routes import site_bp
    from .clinicas.routes import clinicas_bp
    from .clinica_portal.routes import clinica_portal_bp
    from .paciente.routes import paciente_bp

    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(cliente_bp, url_prefix='/portal')
    app.register_blueprint(auth_bp) 
    app.register_blueprint(site_bp)
    app.register_blueprint(clinicas_bp, url_prefix='/admin/clinicas')
    app.register_blueprint(clinica_portal_bp, url_prefix='/clinica')
    app.register_blueprint(paciente_bp, url_prefix='/meu-plano')

    # 7. Criação das Tabelas do Banco de Dados (Incluindo o novo módulo de Clínicas)
    with app.app_context():
        from app import models # Importa os modelos principais (Empresa, Trabalhador, etc.)
        from app.clinicas import models as clinicas_models # Importa os novos modelos (Clinica, Consulta)
        db.create_all()

    return app