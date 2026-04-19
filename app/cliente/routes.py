from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from ..models import db, Empresa, Trabalhador, Fatura
from datetime import datetime
from flask_login import login_required, current_user
from app.asaas import criar_cobranca # Importação do motor Asaas
from app.utils import enviar_email   # Importação do motor de E-mail

cliente_bp = Blueprint('cliente', __name__)

# Dashboard: Visão Geral da Empresa
@cliente_bp.route('/<string:slug>')
@login_required
def dashboard(slug):
    empresa = Empresa.query.filter_by(slug=slug).first_or_404()
    
    if current_user.role != 'admin' and current_user.empresa_id != empresa.id:
        abort(403) 
        
    trabalhadores = Trabalhador.query.filter_by(empresa_id=empresa.id).all()
    faturas = Fatura.query.filter_by(empresa_id=empresa.id).order_by(Fatura.data_geracao.desc()).limit(5).all()
    
    return render_template('cliente/dashboard.html', empresa=empresa, trabalhadores=trabalhadores, faturas=faturas)

# Listagem completa de funcionários do cliente
@cliente_bp.route('/<string:slug>/funcionarios')
@login_required
def listar_trabalhadores(slug):
    empresa = Empresa.query.filter_by(slug=slug).first_or_404()
    
    if current_user.role != 'admin' and current_user.empresa_id != empresa.id:
        abort(403) 
        
    trabalhadores = Trabalhador.query.filter_by(empresa_id=empresa.id).all()
    
    return render_template('cliente/trabalhadores.html', empresa=empresa, trabalhadores=trabalhadores)

# Novo Funcionário pelo Portal
@cliente_bp.route('/<string:slug>/trabalhador/novo', methods=['GET', 'POST'])
@login_required
def novo_trabalhador(slug):
    empresa = Empresa.query.filter_by(slug=slug).first_or_404()
    
    if current_user.role != 'admin' and current_user.empresa_id != empresa.id:
        abort(403)

    if request.method == 'POST':
        data_nasc_str = request.form.get('data_nascimento')
        data_nasc = datetime.strptime(data_nasc_str, '%Y-%m-%d').date() if data_nasc_str else None
        
        novo_t = Trabalhador(
            nome=request.form.get('nome'), 
            cpf=request.form.get('cpf'),
            data_nascimento=data_nasc,
            email=request.form.get('email'),
            telefone=request.form.get('telefone'),
            profissao=request.form.get('profissao'),
            filiacao=request.form.get('filiacao'),       
            cep=request.form.get('cep'),                                 
            logradouro=request.form.get('logradouro'),   
            numero=request.form.get('numero'),           
            complemento=request.form.get('complemento'), 
            bairro=request.form.get('bairro'),           
            cidade=request.form.get('cidade'),           
            estado=request.form.get('estado'),           
            empresa_id=empresa.id,
            status='Ativo'
        )
        db.session.add(novo_t)
        db.session.commit()
        return redirect(url_for('cliente.listar_trabalhadores', slug=empresa.slug))
    
    return render_template('admin/form_trabalhador.html', empresa_id=empresa.id, empresa=empresa, trabalhador=None, origem='cliente')

# Editar Funcionário
@cliente_bp.route('/trabalhador/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_trabalhador(id):
    trabalhador = Trabalhador.query.get_or_404(id)
    empresa_id = trabalhador.empresa_id
    empresa = Empresa.query.get(empresa_id)
    
    if current_user.role != 'admin' and current_user.empresa_id != empresa_id:
        abort(403)
    
    if request.method == 'POST':
        data_nasc_str = request.form.get('data_nascimento')
        trabalhador.data_nascimento = datetime.strptime(data_nasc_str, '%Y-%m-%d').date() if data_nasc_str else None
        trabalhador.nome = request.form.get('nome')
        trabalhador.cpf = request.form.get('cpf')
        trabalhador.email = request.form.get('email')
        trabalhador.telefone = request.form.get('telefone')
        trabalhador.profissao = request.form.get('profissao')
        trabalhador.filiacao = request.form.get('filiacao')       
        trabalhador.cep = request.form.get('cep')                                 
        trabalhador.logradouro = request.form.get('logradouro')   
        trabalhador.numero = request.form.get('numero')           
        trabalhador.complemento = request.form.get('complemento') 
        trabalhador.bairro = request.form.get('bairro')           
        trabalhador.cidade = request.form.get('cidade')           
        trabalhador.estado = request.form.get('estado')           
        
        db.session.commit()
        return redirect(url_for('cliente.listar_trabalhadores', slug=empresa.slug))
        
    return render_template('admin/form_trabalhador.html', 
                           trabalhador=trabalhador, 
                           empresa_id=empresa_id,
                           empresa=empresa,
                           origem='cliente')

# Visualizar Faturas do Cliente
@cliente_bp.route('/<string:slug>/faturas')
@login_required
def listar_faturas(slug):
    empresa = Empresa.query.filter_by(slug=slug).first_or_404()
    
    if current_user.role != 'admin' and current_user.empresa_id != empresa.id:
        abort(403) 
        
    faturas = Fatura.query.filter_by(empresa_id=empresa.id).order_by(Fatura.competencia.desc()).all()
    hoje = datetime.now()
    competencia_atual = hoje.strftime('%m/%Y')
    fatura_mes_gerada = any(f.competencia == competencia_atual for f in faturas)
    
    return render_template('cliente/faturas.html', 
                           empresa=empresa, 
                           faturas=faturas, 
                           competencia_atual=competencia_atual,
                           fatura_mes_gerada=fatura_mes_gerada)

# Cliente gerando a própria fatura (Agora com integração Asaas)
@cliente_bp.route('/<string:slug>/faturas/gerar', methods=['POST'])
@login_required
def gerar_fatura(slug):
    empresa = Empresa.query.filter_by(slug=slug).first_or_404()
    
    if current_user.role != 'admin' and current_user.empresa_id != empresa.id:
        abort(403)
        
    hoje = datetime.now()
    competencia_atual = hoje.strftime('%m/%Y')
    
    fatura_existente = Fatura.query.filter_by(empresa_id=empresa.id, competencia=competencia_atual).first()
    if fatura_existente:
        flash('A fatura deste mês já foi gerada.', 'warning')
        return redirect(url_for('cliente.listar_faturas', slug=empresa.slug))
        
    qtd_vidas = Trabalhador.query.filter_by(empresa_id=empresa.id, status='Ativo').count()
    
    if qtd_vidas == 0:
        flash('Não possui vidas ativas para faturar.', 'danger')
        return redirect(url_for('cliente.listar_faturas', slug=empresa.slug))
        
    valor_total = qtd_vidas * empresa.valor_por_vida
    
    try:
        vencimento = hoje.replace(day=empresa.dia_vencimento)
        if hoje > vencimento:
            if hoje.month == 12:
                vencimento = vencimento.replace(year=hoje.year + 1, month=1)
            else:
                vencimento = vencimento.replace(month=hoje.month + 1)
    except ValueError:
        vencimento = hoje.replace(day=28)
        
    nova_fatura = Fatura(
        competencia=competencia_atual,
        quantidade_vidas=qtd_vidas,
        valor_unitario=empresa.valor_por_vida,
        valor_total=valor_total,
        data_vencimento=vencimento.date(),
        status='Pendente',
        empresa_id=empresa.id
    )
    
    # --- INTEGRAÇÃO ASAAS ---
    gateway_id, boleto_url = criar_cobranca(empresa, nova_fatura)
    if gateway_id:
        nova_fatura.gateway_id = gateway_id
        nova_fatura.boleto_url = boleto_url
    # ------------------------
    
    db.session.add(nova_fatura)
    db.session.commit()

    # --- ENVIO DE E-MAIL ---
    if empresa.email:
        enviar_email(
            assunto=f"Fatura Gerada - {nova_fatura.competencia}",
            destinatario=empresa.email,
            template="emails/fatura_pronta.html",
            empresa=empresa,
            fatura=nova_fatura
        )
    # -----------------------
    
    flash('Fatura gerada com sucesso! O boleto já está disponível.', 'success')
    return redirect(url_for('cliente.listar_faturas', slug=empresa.slug))

@cliente_bp.route('/trabalhador/inativar/<int:id>', methods=['POST'])
@login_required
def inativar_trabalhador(id):
    t = Trabalhador.query.get_or_404(id)
    empresa = Empresa.query.get(t.empresa_id)
    if current_user.role != 'admin' and current_user.empresa_id != t.empresa_id:
        abort(403)
    t.status = 'Inativo'
    db.session.commit()
    return redirect(url_for('cliente.listar_trabalhadores', slug=empresa.slug))

@cliente_bp.route('/trabalhador/reativar/<int:id>', methods=['POST'])
@login_required
def reativar_trabalhador(id):
    t = Trabalhador.query.get_or_404(id)
    empresa = Empresa.query.get(t.empresa_id)
    if current_user.role != 'admin' and current_user.empresa_id != t.empresa_id:
        abort(403)
    t.status = 'Ativo'
    db.session.commit()
    return redirect(url_for('cliente.listar_trabalhadores', slug=empresa.slug))