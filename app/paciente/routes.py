# app/paciente/routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import db, Trabalhador
from app.clinicas.models import Clinica, Especialidade, Consulta
from datetime import datetime
from functools import wraps

paciente_bp = Blueprint('paciente', __name__)

# Decorador de Segurança leve para o Paciente
def paciente_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'paciente_id' not in session:
            return redirect(url_for('paciente.login'))
        return f(*args, **kwargs)
    return decorated_function

@paciente_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Mantemos a formatação da máscara porque é assim que está guardado no banco
        cpf = request.form.get('cpf')
        data_nasc_str = request.form.get('data_nascimento')
        
        paciente = Trabalhador.query.filter_by(cpf=cpf).first()
        
        # Validação dupla: CPF existe e a data de nascimento bate certo?
        if paciente and str(paciente.data_nascimento) == data_nasc_str:
            if paciente.status != 'Ativo':
                flash('O seu plano encontra-se inativo. Por favor, contacte o RH da sua empresa.', 'danger')
                return redirect(url_for('paciente.login'))
            
            # Login com sucesso! Grava na memória super rápida do navegador
            session['paciente_id'] = paciente.id
            return redirect(url_for('paciente.dashboard'))
        else:
            flash('CPF ou Data de Nascimento incorretos.', 'danger')
            
    return render_template('paciente/login.html')

@paciente_bp.route('/')
@paciente_required
def dashboard():
    paciente = Trabalhador.query.get(session['paciente_id'])
    
    # Histórico de Consultas
    minhas_consultas = Consulta.query.filter_by(trabalhador_id=paciente.id).order_by(Consulta.data_solicitacao.desc()).all()
    
    # Dados para o Modal de Solicitação
    especialidades = Especialidade.query.order_by(Especialidade.nome).all()
    clinicas = Clinica.query.filter_by(status='Ativa').order_by(Clinica.razao_social).all()
    
    return render_template('paciente/dashboard.html', 
                           paciente=paciente, 
                           consultas=minhas_consultas, 
                           especialidades=especialidades, 
                           clinicas=clinicas)

@paciente_bp.route('/agendar', methods=['POST'])
@paciente_required
def agendar():
    especialidade_id = request.form.get('especialidade_id')
    clinica_id = request.form.get('clinica_id')
    
    if not especialidade_id or not clinica_id:
        flash('Por favor, selecione a clínica e a especialidade.', 'danger')
        return redirect(url_for('paciente.dashboard'))
        
    nova_consulta = Consulta(
        trabalhador_id=session['paciente_id'],
        clinica_id=clinica_id,
        especialidade_id=especialidade_id,
        status='Pendente' # Vai apitar no painel da clínica!
    )
    db.session.add(nova_consulta)
    db.session.commit()
    
    flash('Pedido enviado! A clínica confirmará o horário exato em breve.', 'success')
    return redirect(url_for('paciente.dashboard'))

@paciente_bp.route('/logout')
def logout():
    session.pop('paciente_id', None) # Apaga a memória
    return redirect(url_for('paciente.login'))