import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
from .models import Usuario

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        user = Usuario.query.filter_by(email=email).first()

        if user and user.check_senha(senha):
            login_user(user)
            
            # Redirecionamento Inteligente baseado no Nível de Acesso (Role)
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
                
            elif user.role == 'cliente':
                # Redireciona usando a URL amigável (slug) da empresa cliente
                return redirect(url_for('cliente.dashboard', slug=user.empresa.slug))
                
            elif user.role == 'clinica':
                # Redireciona para o futuro painel da Clínica
                return redirect(url_for('clinica_portal.dashboard'))
        
        flash('E-mail ou senha inválidos', 'danger')
    return render_template('login.html')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403) # Proíbe o acesso se não for admin
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

def clinica_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'clinica':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function