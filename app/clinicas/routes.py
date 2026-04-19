# app/clinicas/routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import db
from app.clinicas.models import Clinica, Especialidade
from app.auth import admin_required

# Criamos um Blueprint específico para as Clínicas
clinicas_bp = Blueprint('clinicas', __name__)

# --- GESTÃO DE CLÍNICAS (Visão do Admin) ---

@clinicas_bp.route('/')
@admin_required
def listar_clinicas():
    search = request.args.get('search', '')
    query = Clinica.query
    
    if search:
        query = query.filter(
            (Clinica.razao_social.ilike(f'%{search}%')) | 
            (Clinica.cnpj.ilike(f'%{search}%'))
        )
        
    clinicas = query.order_by(Clinica.razao_social).all()
    return render_template('clinicas/listar_clinicas.html', clinicas=clinicas, search=search)

@clinicas_bp.route('/novo', methods=['GET', 'POST'])
@admin_required
def nova_clinica():
    if request.method == 'POST':
        nova = Clinica(
            razao_social=request.form.get('razao_social'),
            nome_fantasia=request.form.get('nome_fantasia'),
            cnpj=request.form.get('cnpj'),
            email=request.form.get('email'),
            telefone=request.form.get('telefone'),
            cep=request.form.get('cep'),
            logradouro=request.form.get('logradouro'),
            numero=request.form.get('numero'),
            bairro=request.form.get('bairro'),
            cidade=request.form.get('cidade'),
            estado=request.form.get('estado'),
            dia_fechamento=int(request.form.get('dia_fechamento', 5)),
            status='Ativa'
        )
        db.session.add(nova)
        db.session.commit()
        
        flash('Clínica cadastrada com sucesso!', 'success')
        return redirect(url_for('clinicas.listar_clinicas'))
        
    return render_template('clinicas/form_clinica.html', clinica=None)

@clinicas_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@admin_required
def editar_clinica(id):
    clinica = Clinica.query.get_or_404(id)
    
    if request.method == 'POST':
        clinica.razao_social = request.form.get('razao_social')
        clinica.nome_fantasia = request.form.get('nome_fantasia')
        clinica.cnpj = request.form.get('cnpj')
        clinica.email = request.form.get('email')
        clinica.telefone = request.form.get('telefone')
        clinica.cep = request.form.get('cep')
        clinica.logradouro = request.form.get('logradouro')
        clinica.numero = request.form.get('numero')
        clinica.bairro = request.form.get('bairro')
        clinica.cidade = request.form.get('cidade')
        clinica.estado = request.form.get('estado')
        clinica.dia_fechamento = int(request.form.get('dia_fechamento', 5))
        clinica.status = request.form.get('status')
        
        db.session.commit()
        flash('Dados da clínica atualizados com sucesso!', 'success')
        return redirect(url_for('clinicas.listar_clinicas'))
        
    return render_template('clinicas/form_clinica.html', clinica=clinica)

# --- GESTÃO DE ESPECIALIDADES (Visão do Admin) ---

@clinicas_bp.route('/especialidades', methods=['GET', 'POST'])
@admin_required
def listar_especialidades():
    if request.method == 'POST':
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        
        if nome:
            nova_esp = Especialidade(nome=nome, descricao=descricao)
            db.session.add(nova_esp)
            db.session.commit()
            flash('Especialidade adicionada com sucesso!', 'success')
            
        return redirect(url_for('clinicas.listar_especialidades'))
        
    especialidades = Especialidade.query.order_by(Especialidade.nome).all()
    return render_template('clinicas/especialidades.html', especialidades=especialidades)