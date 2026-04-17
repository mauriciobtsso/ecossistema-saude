# app/__init__.py
from flask import Flask, redirect, url_for
from flask_login import LoginManager
from .models import db, Usuario # Importe o db diretamente do models

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///saas_saude.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'uma-chave-muito-segura-pode-mudar-depois'

    db.init_app(app)
    
    # Configuração do Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login' # Define a rota de login
    login_manager.login_message = "Acesso restrito. Por favor, faça login."
    login_manager.login_message_category = "warning"

    # Loader de usuário: diz ao Flask-Login como achar o usuário no banco
    from .models import Usuario
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # Importação dos Blueprints
    from .admin.routes import admin_bp
    from .cliente.routes import cliente_bp
    from .auth import auth_bp # Precisamos registrar o auth!
    from .site.routes import site_bp

    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(cliente_bp, url_prefix='/portal')
    app.register_blueprint(auth_bp) # Auth geralmente não tem prefixo
    app.register_blueprint(site_bp)

    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    return app