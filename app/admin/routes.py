from flask import Blueprint, render_template, request, redirect, url_for, abort, flash
from ..models import db, Empresa, Trabalhador, Fatura, Usuario, gerar_slug
from datetime import datetime
from sqlalchemy import func
from ..auth import admin_required
from flask_login import login_required, current_user
from app.utils import enviar_email
from app.asaas import criar_cobranca

# Definindo o Blueprint do Admin
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@admin_required
def dashboard():
    total_empresas = Empresa.query.count()
    total_vidas = Trabalhador.query.filter_by(status='Ativo').count()
    
    receita_mensal = db.session.query(
        func.sum(Empresa.valor_por_vida)
    ).join(Trabalhador).filter(Trabalhador.status == 'Ativo').scalar() or 0
    
    ativas = Empresa.query.filter_by(status='Ativa').count()
    suspensas = Empresa.query.filter_by(status='Suspensa').count()
    ultimas_faturas = Fatura.query.order_by(Fatura.data_geracao.desc()).limit(5).all()

    return render_template('admin/dashboard.html', 
                           total_empresas=total_empresas,
                           total_vidas=total_vidas,
                           receita_mensal=receita_mensal,
                           ativas=ativas,
                           suspensas=suspensas,
                           ultimas_faturas=ultimas_faturas)

# --- GESTÃO DE EMPRESAS ---

@admin_bp.route('/empresas')
@admin_required
def listar_empresas():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    query = Empresa.query
    if search:
        query = query.filter((Empresa.razao_social.like(f'%{search}%')) | (Empresa.cnpj.like(f'%{search}%')))
    if status_filter:
        query = query.filter(Empresa.status == status_filter)
    pagination = query.order_by(Empresa.razao_social).paginate(page=page, per_page=10, error_out=False)
    return render_template('admin/empresas.html', pagination=pagination, search=search, status_filter=status_filter)

@admin_bp.route('/empresas/novo', methods=['GET', 'POST'])
@admin_required
def cadastrar_empresa():
    if request.method == 'POST':
        valor_limpo = request.form.get('valor_por_vida', '50,00').replace('.', '').replace(',', '.')
        
        nova = Empresa(
            razao_social=request.form.get('razao_social'),
            nome_fantasia=request.form.get('nome_fantasia'),
            cnpj=request.form.get('cnpj'),
            email=request.form.get('email'),
            telefone=request.form.get('telefone'),
            responsavel=request.form.get('responsavel'),
            cep=request.form.get('cep'),
            logradouro=request.form.get('logradouro'),
            numero=request.form.get('numero'),
            complemento=request.form.get('complemento'),
            bairro=request.form.get('bairro'),
            cidade=request.form.get('cidade'),
            estado=request.form.get('estado'),
            valor_por_vida=float(valor_limpo),
            dia_vencimento=int(request.form.get('dia_vencimento', 10))
        )
        # Geração automática do Slug
        nova.slug = gerar_slug(nova.nome_fantasia or nova.razao_social)
        
        db.session.add(nova)
        db.session.commit()
        return redirect(url_for('admin.listar_empresas'))
    return render_template('admin/form_empresa.html', empresa=None)

@admin_bp.route('/empresas/editar/<int:id>', methods=['GET', 'POST'])
@admin_required
def editar_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    if request.method == 'POST':
        valor_limpo = request.form.get('valor_por_vida', '50,00').replace('.', '').replace(',', '.')
        empresa.razao_social = request.form.get('razao_social')
        empresa.nome_fantasia = request.form.get('nome_fantasia')
        empresa.cnpj = request.form.get('cnpj')
        empresa.email = request.form.get('email')
        empresa.telefone = request.form.get('telefone')
        empresa.responsavel = request.form.get('responsavel')
        empresa.cep = request.form.get('cep')
        empresa.logradouro = request.form.get('logradouro')
        empresa.numero = request.form.get('numero')
        empresa.complemento = request.form.get('complemento')
        empresa.bairro = request.form.get('bairro')
        empresa.cidade = request.form.get('cidade')
        empresa.estado = request.form.get('estado')
        empresa.valor_por_vida = float(valor_limpo)
        empresa.dia_vencimento = int(request.form.get('dia_vencimento'))
        
        # Atualiza o slug caso o nome mude
        empresa.slug = gerar_slug(empresa.nome_fantasia or empresa.razao_social)
        
        db.session.commit()
        return redirect(url_for('admin.listar_empresas'))
    return render_template('admin/form_empresa.html', empresa=empresa)

@admin_bp.route('/empresas/excluir/<int:id>', methods=['POST'])
@admin_required
def excluir_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    db.session.delete(empresa)
    db.session.commit()
    return redirect(url_for('admin.listar_empresas'))

@admin_bp.route('/empresas/visualizar/<int:id>')
@admin_required
def visualizar_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    trabalhadores = Trabalhador.query.filter_by(empresa_id=id).all()
    vidas_ativas = len([t for t in trabalhadores if t.status == 'Ativo'])
    faturamento_previsto = vidas_ativas * empresa.valor_por_vida
    return render_template('admin/detalhe_empresa.html', 
                           empresa=empresa, trabalhadores=trabalhadores,
                           vidas_ativas=vidas_ativas, faturamento_previsto=faturamento_previsto)

# --- GESTÃO DE TRABALHADORES (ADMIN) ---

@admin_bp.route('/trabalhadores')
@admin_required
def listar_trabalhadores():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    query = Trabalhador.query
    if search:
        query = query.filter(Trabalhador.nome.like(f'%{search}%') | Trabalhador.cpf.like(f'%{search}%'))
    pagination = query.order_by(Trabalhador.nome).paginate(page=page, per_page=15)
    return render_template('admin/trabalhadores.html', pagination=pagination, search=search)

@admin_bp.route('/trabalhadores/novo', methods=['GET', 'POST'])
@admin_required
def cadastrar_trabalhador():
    empresas = Empresa.query.all()
    if request.method == 'POST':
        data_nasc_str = request.form.get('data_nascimento')
        data_nasc = datetime.strptime(data_nasc_str, '%Y-%m-%d').date() if data_nasc_str else None
        novo_t = Trabalhador(
            nome=request.form.get('nome'), cpf=request.form.get('cpf'), data_nascimento=data_nasc,
            email=request.form.get('email'), telefone=request.form.get('telefone'),
            profissao=request.form.get('profissao'), filiacao=request.form.get('filiacao'),
            cep=request.form.get('cep'), logradouro=request.form.get('logradouro'),
            numero=request.form.get('numero'), complemento=request.form.get('complemento'),
            bairro=request.form.get('bairro'), cidade=request.form.get('cidade'),
            estado=request.form.get('estado'), empresa_id=request.form.get('empresa_id'),
            status='Ativo'
        )
        db.session.add(novo_t)
        db.session.commit()
        return redirect(url_for('admin.listar_trabalhadores'))
    return render_template('admin/form_trabalhador.html', empresas=empresas, trabalhador=None, origem='admin')

@admin_bp.route('/trabalhadores/editar/<int:id>', methods=['GET', 'POST'])
@admin_required
def editar_trabalhador(id):
    trabalhador = Trabalhador.query.get_or_404(id)
    empresas = Empresa.query.all()
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
        trabalhador.empresa_id = request.form.get('empresa_id')
        db.session.commit()
        return redirect(url_for('admin.listar_trabalhadores'))
    return render_template('admin/form_trabalhador.html', trabalhador=trabalhador, empresas=empresas)

@admin_bp.route('/trabalhadores/inativar/<int:id>', methods=['POST'])
@admin_required
def inativar_trabalhador(id):
    if current_user.role != 'admin':
        return "Acesso Negado", 403
        
    t = Trabalhador.query.get_or_404(id)
    t.status = 'Inativo'
    db.session.commit()
    return redirect(url_for('admin.listar_trabalhadores'))

@admin_bp.route('/trabalhadores/reativar/<int:id>', methods=['POST'])
@admin_required
def reativar_trabalhador(id):
    if current_user.role != 'admin':
        return "Acesso Negado", 403
        
    t = Trabalhador.query.get_or_404(id)
    t.status = 'Ativo'
    db.session.commit()
    return redirect(url_for('admin.listar_trabalhadores'))

# --- MOTOR DE FATURAMENTO E ASAAS ---

@admin_bp.route('/faturamento')
@admin_required
def menu_faturamento():
    faturas = Fatura.query.order_by(Fatura.data_geracao.desc()).all()
    total_pendente = sum(f.valor_total for f in faturas if f.status == 'Pendente')
    total_pago = sum(f.valor_total for f in faturas if f.status == 'Pago')
    return render_template('admin/faturamento.html', faturas=faturas, total_pendente=total_pendente, total_pago=total_pago)

@admin_bp.route('/faturamento/gerar', methods=['POST'])
@admin_required
def gerar_faturamento():
    mes_ano = request.form.get('competencia')
    if not mes_ano: 
        return redirect(url_for('admin.menu_faturamento'))
        
    competencia = datetime.strptime(mes_ano, '%Y-%m').strftime('%m/%Y')
    empresas = Empresa.query.filter_by(status='Ativa').all()
    
    faturas_geradas = [] 

    for empresa in empresas:
        if Fatura.query.filter_by(empresa_id=empresa.id, competencia=competencia).first(): 
            continue
            
        qtd_vidas = Trabalhador.query.filter_by(empresa_id=empresa.id, status='Ativo').count()
        if qtd_vidas > 0:
            valor_total = qtd_vidas * empresa.valor_por_vida
            hoje = datetime.now()
            try: 
                vencimento = hoje.replace(day=empresa.dia_vencimento)
            except ValueError: 
                vencimento = hoje.replace(day=28)
                
            f = Fatura(competencia=competencia, quantidade_vidas=qtd_vidas, valor_unitario=empresa.valor_por_vida,
                       valor_total=valor_total, data_vencimento=vencimento, status='Pendente', empresa_id=empresa.id)
            
            # Chama a API do Asaas para gerar a cobrança
            gateway_id, boleto_url = criar_cobranca(empresa, f)
            if gateway_id:
                f.gateway_id = gateway_id
                f.boleto_url = boleto_url

            db.session.add(f)
            faturas_geradas.append((empresa, f))

    db.session.commit()

    # Disparo de e-mail em lote
    enviados = 0
    for empresa, fatura in faturas_geradas:
        if empresa.email:
            sucesso = enviar_email(
                assunto=f"Nova Fatura Disponível - {fatura.competencia}",
                destinatario=empresa.email,
                template="emails/fatura_pronta.html",
                empresa=empresa,
                fatura=fatura
            )
            if sucesso:
                enviados += 1

    flash(f'Processamento concluído! {len(faturas_geradas)} faturas geradas e {enviados} e-mails enviados.', 'success')
    return redirect(url_for('admin.menu_faturamento'))

@admin_bp.route('/faturamento/pagar/<int:id>', methods=['POST'])
@admin_required
def baixar_fatura(id):
    fatura = Fatura.query.get_or_404(id)
    fatura.status = 'Pago'
    db.session.commit()
    return redirect(url_for('admin.menu_faturamento'))

# ROTA PARA IMPRESSÃO DO RECIBO
@admin_bp.route('/faturamento/imprimir/<int:id>')
@login_required 
def imprimir_fatura(id):
    fatura = Fatura.query.get_or_404(id)
    
    if current_user.role != 'admin' and current_user.empresa_id != fatura.empresa_id:
        abort(403)
        
    return render_template('admin/recibo_fatura.html', fatura=fatura)

# --- GESTÃO DE USUÁRIOS (ADMIN) ---

@admin_bp.route('/usuarios')
@admin_required
def listar_usuarios():
    if current_user.role != 'admin':
        return "Acesso Negado", 403
    usuarios = Usuario.query.all()
    return render_template('admin/usuarios.html', usuarios=usuarios)

@admin_bp.route('/usuarios/novo', methods=['GET', 'POST'])
@admin_required
def cadastrar_usuario():
    if current_user.role != 'admin':
        return "Acesso Negado", 403
    
    empresas = Empresa.query.all()
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        role = request.form.get('role')
        empresa_id = request.form.get('empresa_id')

        if role == 'admin':
            empresa_id = None
        
        novo_usuario = Usuario(email=email, role=role, empresa_id=empresa_id)
        novo_usuario.set_senha(senha)
        
        db.session.add(novo_usuario)
        db.session.commit()
        return redirect(url_for('admin.listar_usuarios'))
        
    return render_template('admin/form_usuario.html', empresas=empresas, usuario=None)

@admin_bp.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@admin_required
def editar_usuario(id):
    if current_user.role != 'admin':
        return "Acesso Negado", 403
    
    usuario = Usuario.query.get_or_404(id)
    empresas = Empresa.query.all()
    
    if request.method == 'POST':
        usuario.email = request.form.get('email')
        usuario.role = request.form.get('role')
        
        if usuario.role == 'admin':
            usuario.empresa_id = None
        else:
            usuario.empresa_id = request.form.get('empresa_id')
            
        nova_senha = request.form.get('senha')
        if nova_senha:
            usuario.set_senha(nova_senha)
            
        db.session.commit()
        return redirect(url_for('admin.listar_usuarios'))
        
    return render_template('admin/form_usuario.html', empresas=empresas, usuario=usuario)

@admin_bp.route('/usuarios/excluir/<int:id>', methods=['POST'])
@admin_required
def excluir_usuario(id):
    if current_user.role != 'admin':
        return "Acesso Negado", 403
    
    if id == current_user.id:
        return "Erro: Você não pode excluir sua própria conta.", 400
        
    usuario = Usuario.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()
    return redirect(url_for('admin.listar_usuarios'))

# --- WEBHOOKS (AUTOMAÇÃO FINANCEIRA) ---

from flask import jsonify

@admin_bp.route('/webhook/asaas', methods=['POST'])
def webhook_asaas():
    """Esta rota recebe os avisos automáticos do Asaas (ex: Boleto Pago)"""
    
    # Pega os dados que o Asaas enviou
    dados = request.json
    if not dados:
        return jsonify({"erro": "Nenhum dado recebido"}), 400

    # O Asaas manda vários eventos, nós só queremos saber se foi PAGO
    eventos_pagos = ['PAYMENT_RECEIVED', 'PAYMENT_CONFIRMED']
    
    if dados.get('event') in eventos_pagos:
        pagamento = dados.get('payment', {})
        gateway_id = pagamento.get('id')
        
        if gateway_id:
            # Procura no nosso banco qual fatura tem esse ID do Asaas
            fatura = Fatura.query.filter_by(gateway_id=gateway_id).first()
            
            if fatura and fatura.status != 'Pago':
                fatura.status = 'Pago'
                fatura.data_pagamento = datetime.now()
                db.session.commit()
                print(f"✅ SUCESSO: Fatura {fatura.id} baixada automaticamente via Webhook!")
                
    # Sempre devemos responder 200 OK para o Asaas saber que recebemos a mensagem
    return jsonify({"status": "recebido"}), 200
