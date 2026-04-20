# app/clinica_portal/routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import db, Trabalhador
from app.clinicas.models import Consulta, Clinica
from app.auth import clinica_required
from datetime import datetime

clinica_portal_bp = Blueprint('clinica_portal', __name__)

@clinica_portal_bp.route('/')
@login_required
@clinica_required
def dashboard():
    clinica_id = current_user.clinica_id
    clinica = Clinica.query.get(clinica_id)
    
    # Estatísticas
    pendentes = Consulta.query.filter_by(clinica_id=clinica_id, status='Pendente').count()
    hoje = Consulta.query.filter_by(clinica_id=clinica_id, status='Confirmada').filter(db.func.date(Consulta.data_agendada) == datetime.now().date()).count()
    
    # Nova Lógica: Pacientes que já chegaram e estão sentados na sala de espera
    fila_espera = Consulta.query.filter_by(clinica_id=clinica_id, status='Aguardando Atendimento')\
        .filter(db.func.date(Consulta.data_agendada) == datetime.now().date())\
        .order_by(Consulta.data_agendada.asc()).all()

    # Pacientes com horário marcado que ainda não chegaram
    proximas_consultas = Consulta.query.filter_by(clinica_id=clinica_id, status='Confirmada')\
        .filter(Consulta.data_agendada >= datetime.now())\
        .order_by(Consulta.data_agendada.asc()).limit(5).all()

    # Passamos as especialidades da clínica para o Modal do Balcão
    especialidades = clinica.especialidades_oferecidas.all()

    return render_template('clinica_portal/dashboard.html', 
                           clinica=clinica, 
                           pendentes=pendentes, 
                           hoje=hoje, 
                           fila_espera=fila_espera,
                           proximas=proximas_consultas,
                           especialidades=especialidades)

# --- ROTAS DO ATENDIMENTO E FILA ---

@clinica_portal_bp.route('/api/buscar_paciente/<cpf>')
@login_required
@clinica_required
def buscar_paciente(cpf):
    """Rota invisível (API) acessada pelo JavaScript para encontrar o paciente rápido"""
    paciente = Trabalhador.query.filter_by(cpf=cpf).first()
    
    if not paciente:
        return jsonify({'status': 'erro', 'mensagem': 'CPF não encontrado na base do SindiMedic.'}), 404
        
    if paciente.status != 'Ativo':
        return jsonify({'status': 'erro', 'mensagem': 'Trabalhador encontra-se INATIVO no momento.'}), 403
        
    return jsonify({
        'status': 'sucesso',
        'id': paciente.id,
        'nome': paciente.nome,
        'empresa': paciente.empresa.razao_social
    })

@clinica_portal_bp.route('/atendimento_balcao', methods=['POST'])
@login_required
@clinica_required
def atendimento_balcao():
    paciente_id = request.form.get('paciente_id')
    especialidade_id = request.form.get('especialidade_id')
    
    if not paciente_id or not especialidade_id:
        flash('Erro: Dados incompletos para o atendimento.', 'danger')
        return redirect(url_for('clinica_portal.dashboard'))
        
    # O paciente entra na FILA DE ESPERA (A rececionista apenas organizou a fila)
    nova_consulta = Consulta(
        trabalhador_id=paciente_id,
        clinica_id=current_user.clinica_id,
        especialidade_id=especialidade_id,
        data_solicitacao=datetime.now(),
        data_agendada=datetime.now(),
        status='Aguardando Atendimento'
    )
    
    db.session.add(nova_consulta)
    db.session.commit()
    
    flash('Paciente adicionado à fila de espera com sucesso!', 'success')
    return redirect(url_for('clinica_portal.dashboard'))

@clinica_portal_bp.route('/finalizar/<int:id>', methods=['POST'])
@login_required
@clinica_required
def finalizar_consulta(id):
    """Rota chamada quando o médico atende o paciente e a rececionista dá baixa"""
    consulta = Consulta.query.get_or_404(id)
    
    if consulta.clinica_id != current_user.clinica_id:
        return "Acesso negado", 403
        
    consulta.status = 'Realizada'
    db.session.commit()
    
    flash(f'Atendimento de {consulta.paciente.nome} finalizado. Valor contabilizado para repasse!', 'success')
    return redirect(url_for('clinica_portal.dashboard'))

# --- ROTAS DA AGENDA TRADICIONAL ---

@clinica_portal_bp.route('/agenda')
@login_required
@clinica_required
def agenda():
    status_filtro = request.args.get('status', 'Confirmada')
    consultas = Consulta.query.filter_by(clinica_id=current_user.clinica_id, status=status_filtro)\
        .order_by(Consulta.data_agendada.desc()).all()
        
    # Passamos as especialidades para a clínica poder criar um agendamento novo
    clinica = Clinica.query.get(current_user.clinica_id)
    especialidades = clinica.especialidades_oferecidas.all()
    
    return render_template('clinica_portal/agenda.html', consultas=consultas, status_atual=status_filtro, especialidades=especialidades)

@clinica_portal_bp.route('/novo_agendamento', methods=['POST'])
@login_required
@clinica_required
def novo_agendamento():
    """Cria um agendamento manual feito pela própria clínica (ex: por telefone)"""
    paciente_id = request.form.get('paciente_id')
    especialidade_id = request.form.get('especialidade_id')
    data_str = request.form.get('data_agendada')
    
    if not paciente_id or not especialidade_id or not data_str:
        flash('Erro: Dados incompletos para o agendamento.', 'danger')
        return redirect(url_for('clinica_portal.agenda'))
        
    # Como a clínica que marcou, já entra como "Confirmada" com data e hora
    nova_consulta = Consulta(
        trabalhador_id=paciente_id,
        clinica_id=current_user.clinica_id,
        especialidade_id=especialidade_id,
        data_solicitacao=datetime.now(),
        data_agendada=datetime.strptime(data_str, '%Y-%m-%dT%H:%M'),
        status='Confirmada'
    )
    
    db.session.add(nova_consulta)
    db.session.commit()
    
    flash('Consulta agendada com sucesso!', 'success')
    # Redireciona para a aba de Confirmadas para a rececionista já ver o resultado
    return redirect(url_for('clinica_portal.agenda', status='Confirmada'))

@clinica_portal_bp.route('/confirmar/<int:id>', methods=['POST'])
@login_required
@clinica_required
def confirmar_consulta(id):
    consulta = Consulta.query.get_or_404(id)
    if consulta.clinica_id != current_user.clinica_id:
        return "Acesso negado", 403
    
    data_str = request.form.get('data_agendada')
    if data_str:
        consulta.data_agendada = datetime.strptime(data_str, '%Y-%m-%dT%H:%M')
        consulta.status = 'Confirmada'
        db.session.commit()
        flash('Consulta confirmada e agendada!', 'success')
    
    return redirect(url_for('clinica_portal.dashboard'))

@clinica_portal_bp.route('/chegou/<int:id>', methods=['POST'])
@login_required
@clinica_required
def paciente_chegou(id):
    consulta = Consulta.query.get_or_404(id)
    if consulta.clinica_id != current_user.clinica_id:
        return "Acesso negado", 403
        
    consulta.status = 'Aguardando Atendimento'
    db.session.commit()
    flash(f'Paciente {consulta.paciente.nome} adicionado à fila de espera!', 'success')
    return redirect(url_for('clinica_portal.dashboard'))