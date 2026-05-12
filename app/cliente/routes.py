from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from ..models import db, Empresa, Trabalhador, Fatura
from datetime import datetime
from flask_login import login_required, current_user
from app.asaas import criar_cobranca 
from app.utils import enviar_email   

cliente_bp = Blueprint('cliente', __name__)

def verificar_acesso(empresa):
    """
    Função auxiliar de segurança que permite acesso se:
    1. O utilizador for ADMIN.
    2. O utilizador for o dono da própria EMPRESA.
    3. O utilizador for o CONTADOR responsável pelo escritório que atende esta empresa.
    """
    if current_user.role == 'admin':
        return True
    if current_user.role == 'cliente' and current_user.empresa_id == empresa.id:
        return True
    if current_user.role == 'contador' and empresa.escritorio_id == current_user.escritorio_id:
        return True
    
    abort(403)

# Dashboard: Visão Geral da Empresa
@cliente_bp.route('/<string:slug>')
@login_required
def dashboard(slug):
    empresa = Empresa.query.filter_by(slug=slug).first_or_404()
    verificar_acesso(empresa) # Nova validação multinível
        
    trabalhadores = Trabalhador.query.filter_by(empresa_id=empresa.id).all()
    faturas = Fatura.query.filter_by(empresa_id=empresa.id).order_by(Fatura.data_geracao.desc()).limit(5).all()
    
    return render_template('cliente/dashboard.html', empresa=empresa, trabalhadores=trabalhadores, faturas=faturas)

# Listagem completa de funcionários do cliente
@cliente_bp.route('/<string:slug>/funcionarios')
@login_required
def listar_trabalhadores(slug):
    empresa = Empresa.query.filter_by(slug=slug).first_or_404()
    verificar_acesso(empresa)
        
    trabalhadores = Trabalhador.query.filter_by(empresa_id=empresa.id).all()
    
    return render_template('cliente/trabalhadores.html', empresa=empresa, trabalhadores=trabalhadores)

# Novo Funcionário pelo Portal
@cliente_bp.route('/<string:slug>/trabalhador/novo', methods=['GET', 'POST'])
@login_required
def novo_trabalhador(slug):
    empresa = Empresa.query.filter_by(slug=slug).first_or_404()
    verificar_acesso(empresa)

    if request.method == 'POST':
        data_nasc_str = request.form.get('data_nascimento')
        data_adm_str = request.form.get('data_admissao')
        
        # Reaproveita cadastro se o CPF já existir na base global
        cpf = request.form.get('cpf')
        t = Trabalhador.query.filter_by(cpf=cpf).first()
        
        if not t:
            t = Trabalhador(cpf=cpf)
            db.session.add(t)

        t.nome = request.form.get('nome')
        t.rg = request.form.get('rg')
        t.orgao_expedidor = request.form.get('orgao_expedidor')
        t.pis = request.form.get('pis')
        t.ctps = request.form.get('ctps')
        t.estado_civil = request.form.get('estado_civil')
        t.data_nascimento = datetime.strptime(data_nasc_str, '%Y-%m-%d').date() if data_nasc_str else None
        t.data_admissao = datetime.strptime(data_adm_str, '%Y-%m-%d').date() if data_adm_str else None
        t.email = request.form.get('email')
        t.telefone = request.form.get('telefone')
        t.profissao = request.form.get('profissao')
        t.filiacao = request.form.get('filiacao')
        t.cep = request.form.get('cep')
        t.logradouro = request.form.get('logradouro')
        t.numero = request.form.get('numero')
        t.complemento = request.form.get('complemento')
        t.bairro = request.form.get('bairro')
        t.cidade = request.form.get('cidade')
        t.estado = request.form.get('estado')
        t.empresa_id = empresa.id
        t.status = 'Ativo'
        
        db.session.commit()
        flash('Colaborador registrado com sucesso!', 'success')
        return redirect(url_for('cliente.listar_trabalhadores', slug=empresa.slug))
    
    return render_template('admin/form_trabalhador.html', empresa_id=empresa.id, empresa=empresa, trabalhador=None, origem='cliente')

# Editar Funcionário
@cliente_bp.route('/trabalhador/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_trabalhador(id):
    trabalhador = Trabalhador.query.get_or_404(id)
    empresa = Empresa.query.get(trabalhador.empresa_id)
    verificar_acesso(empresa)
    
    if request.method == 'POST':
        data_nasc_str = request.form.get('data_nascimento')
        data_adm_str = request.form.get('data_admissao')
        
        trabalhador.nome = request.form.get('nome')
        trabalhador.cpf = request.form.get('cpf')
        trabalhador.rg = request.form.get('rg')
        trabalhador.orgao_expedidor = request.form.get('orgao_expedidor')
        trabalhador.pis = request.form.get('pis')
        trabalhador.ctps = request.form.get('ctps')
        trabalhador.estado_civil = request.form.get('estado_civil')
        trabalhador.data_nascimento = datetime.strptime(data_nasc_str, '%Y-%m-%d').date() if data_nasc_str else None
        trabalhador.data_admissao = datetime.strptime(data_adm_str, '%Y-%m-%d').date() if data_adm_str else None
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
        flash('Dados atualizados!', 'success')
        return redirect(url_for('cliente.listar_trabalhadores', slug=empresa.slug))
        
    return render_template('admin/form_trabalhador.html', 
                           trabalhador=trabalhador, 
                           empresa_id=empresa.id,
                           empresa=empresa,
                           origem='cliente')

# Visualizar Faturas do Cliente
@cliente_bp.route('/<string:slug>/faturas')
@login_required
def listar_faturas(slug):
    empresa = Empresa.query.filter_by(slug=slug).first_or_404()
    verificar_acesso(empresa)
        
    faturas = Fatura.query.filter_by(empresa_id=empresa.id).order_by(Fatura.competencia.desc()).all()
    hoje = datetime.now()
    competencia_atual = hoje.strftime('%m/%Y')
    fatura_mes_gerada = any(f.competencia == competencia_atual for f in faturas)
    
    return render_template('cliente/faturas.html', 
                           empresa=empresa, 
                           faturas=faturas, 
                           competencia_atual=competencia_atual,
                           fatura_mes_gerada=fatura_mes_gerada)

# Cliente gerando a própria fatura
@cliente_bp.route('/<string:slug>/faturas/gerar', methods=['POST'])
@login_required
def gerar_fatura(slug):
    empresa = Empresa.query.filter_by(slug=slug).first_or_404()
    verificar_acesso(empresa)
        
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
    
    gateway_id, boleto_url = criar_cobranca(empresa, nova_fatura)
    if gateway_id:
        nova_fatura.gateway_id = gateway_id
        nova_fatura.boleto_url = boleto_url
    
    db.session.add(nova_fatura)
    db.session.commit()

    if empresa.email:
        enviar_email(
            assunto=f"Fatura Gerada - {nova_fatura.competencia}",
            destinatario=empresa.email,
            template="emails/fatura_pronta.html",
            empresa=empresa,
            fatura=nova_fatura
        )
    
    flash('Fatura gerada com sucesso! O boleto já está disponível.', 'success')
    return redirect(url_for('cliente.listar_faturas', slug=empresa.slug))

@cliente_bp.route('/trabalhador/inativar/<int:id>', methods=['POST'])
@login_required
def inativar_trabalhador(id):
    t = Trabalhador.query.get_or_404(id)
    empresa = Empresa.query.get(t.empresa_id)
    verificar_acesso(empresa)

    t.status = 'Inativo'
    # Captura data e motivo enviados via modal (se houver)
    data_desl = request.form.get('data_desligamento')
    t.data_desligamento = datetime.strptime(data_desl, '%Y-%m-%d').date() if data_desl else datetime.now().date()
    t.motivo_desligamento = request.form.get('motivo_desligamento') or 'Não informado'
    
    db.session.commit()
    flash(f'Trabalhador {t.nome} inativado.', 'warning')
    return redirect(url_for('cliente.listar_trabalhadores', slug=empresa.slug))

@cliente_bp.route('/trabalhador/reativar/<int:id>', methods=['POST'])
@login_required
def reativar_trabalhador(id):
    t = Trabalhador.query.get_or_404(id)
    empresa = Empresa.query.get(t.empresa_id)
    verificar_acesso(empresa)

    t.status = 'Ativo'
    t.data_desligamento = None
    t.motivo_desligamento = None
    db.session.commit()
    flash(f'Trabalhador {t.nome} reativado!', 'success')
    return redirect(url_for('cliente.listar_trabalhadores', slug=empresa.slug))