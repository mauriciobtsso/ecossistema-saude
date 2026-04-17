# app/__init__.py
import os
from flask import Flask
from flask_login import LoginManager
from .models import db, Usuario

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # 1. Configuração Dinâmica do Banco de Dados (PostgreSQL no Render ou SQLite local)
    uri = os.getenv("DATABASE_URL")
    if uri and uri.startswith("postgres://"):
        # O Render usa 'postgres://' internamente, mas o SQLAlchemy exige 'postgresql://'
        uri = uri.replace("postgres://", "postgresql://", 1)
        
    app.config['SQLALCHEMY_DATABASE_URI'] = uri or 'sqlite:///saas_saude.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 2. Chave secreta dinâmica (Puxa do Render, ou usa a local se não existir)
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", 'uma-chave-muito-segura-pode-mudar-depois')

    db.init_app(app)
    
    # Configuração do Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login' # Define a rota de login
    login_manager.login_message = "Acesso restrito. Por favor, faça login."
    login_manager.login_message_category = "warning"

    # Loader de usuário: diz ao Flask-Login como achar o usuário no banco
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # Importação dos Blueprints
    from .admin.routes import admin_bp
    from .cliente.routes import cliente_bp
    from .auth import auth_bp
    from .site.routes import site_bp

    # Registro dos Blueprints
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(cliente_bp, url_prefix='/portal')
    app.register_blueprint(auth_bp) 
    app.register_blueprint(site_bp) # Agora o site_bp é quem manda na rota raiz '/'

    return app