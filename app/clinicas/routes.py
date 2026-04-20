# app/clinicas/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import db
from app.clinicas.models import Clinica, Especialidade
from app.auth import admin_required

clinicas_bp = Blueprint('clinicas', __name__)

# --- GESTÃO DE CLÍNICAS ---

@clinicas_bp.route('/')
@admin_required
def listar_clinicas():
    search = request.args.get('search', '')
    especialidade_id = request.args.get('especialidade_id', type=int)
    
    query = Clinica.query
    
    # Filtro por texto (Nome ou CNPJ)
    if search:
        query = query.filter((Clinica.razao_social.ilike(f'%{search}%')) | (Clinica.cnpj.ilike(f'%{search}%')))
        
    # Filtro Inteligente por Especialidade
    if especialidade_id:
        query = query.filter(Clinica.especialidades_oferecidas.any(id=especialidade_id))
        
    clinicas = query.order_by(Clinica.razao_social).all()
    todas_especialidades = Especialidade.query.order_by(Especialidade.nome).all()
    
    return render_template('clinicas/listar_clinicas.html', clinicas=clinicas, search=search, 
                           especialidades=todas_especialidades, especialidade_filtro=especialidade_id)

@clinicas_bp.route('/novo', methods=['GET', 'POST'])
@admin_required
def nova_clinica():
    todas_especialidades = Especialidade.query.order_by(Especialidade.nome).all()
    
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
        
        # Salvando as especialidades selecionadas
        esp_ids = request.form.getlist('especialidades')
        if esp_ids:
            nova.especialidades_oferecidas = Especialidade.query.filter(Especialidade.id.in_(esp_ids)).all()
            
        db.session.add(nova)
        db.session.commit()
        flash('Clínica cadastrada com sucesso!', 'success')
        return redirect(url_for('clinicas.listar_clinicas'))
        
    return render_template('clinicas/form_clinica.html', clinica=None, todas_especialidades=todas_especialidades)

@clinicas_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@admin_required
def editar_clinica(id):
    clinica = Clinica.query.get_or_404(id)
    todas_especialidades = Especialidade.query.order_by(Especialidade.nome).all()
    
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
        
        # Atualizando as especialidades
        esp_ids = request.form.getlist('especialidades')
        clinica.especialidades_oferecidas = Especialidade.query.filter(Especialidade.id.in_(esp_ids)).all()
        
        db.session.commit()
        flash('Dados da clínica atualizados com sucesso!', 'success')
        return redirect(url_for('clinicas.listar_clinicas'))
        
    return render_template('clinicas/form_clinica.html', clinica=clinica, todas_especialidades=todas_especialidades)

@clinicas_bp.route('/visualizar/<int:id>')
@admin_required
def visualizar_clinica(id):
    clinica = Clinica.query.get_or_404(id)
    return render_template('clinicas/visualizar_clinica.html', clinica=clinica)

@clinicas_bp.route('/excluir/<int:id>', methods=['POST'])
@admin_required
def excluir_clinica(id):
    clinica = Clinica.query.get_or_404(id)
    try:
        db.session.delete(clinica)
        db.session.commit()
        flash('Clínica excluída com sucesso!', 'success')
    except:
        db.session.rollback()
        flash('Não é possível excluir esta clínica pois ela possui registros vinculados.', 'danger')
    return redirect(url_for('clinicas.listar_clinicas'))

# --- GESTÃO DE ESPECIALIDADES ---

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

@clinicas_bp.route('/especialidades/editar/<int:id>', methods=['POST'])
@admin_required
def editar_especialidade(id):
    esp = Especialidade.query.get_or_404(id)
    esp.nome = request.form.get('nome')
    esp.descricao = request.form.get('descricao')
    db.session.commit()
    flash('Especialidade atualizada!', 'success')
    return redirect(url_for('clinicas.listar_especialidades'))

@clinicas_bp.route('/especialidades/excluir/<int:id>', methods=['POST'])
@admin_required
def excluir_especialidade(id):
    esp = Especialidade.query.get_or_404(id)
    try:
        db.session.delete(esp)
        db.session.commit()
        flash('Especialidade excluída.', 'success')
    except:
        db.session.rollback()
        flash('Erro: Existem clínicas vinculadas a esta especialidade!', 'danger')
    return redirect(url_for('clinicas.listar_especialidades'))