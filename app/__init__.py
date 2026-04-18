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

    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(cliente_bp, url_prefix='/portal')
    app.register_blueprint(auth_bp) 
    app.register_blueprint(site_bp)

    return app