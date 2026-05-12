import os
from flask import Blueprint, render_template, request, redirect, url_for, abort, flash, jsonify
from ..models import db, Empresa, Trabalhador, Fatura, Usuario, gerar_slug, Escritorio
from datetime import datetime
from sqlalchemy import func
from ..auth import admin_required
from flask_login import login_required, current_user
from app.utils import enviar_email
from app.asaas import criar_cobranca

# Importação do módulo de Clínicas para os Relatórios
from app.clinicas.models import Clinica, Consulta, Especialidade

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

# --- GESTÃO DE ESCRITÓRIOS (CONTABILIDADE) ---
@admin_bp.route('/escritorios')
@admin_required
def listar_escritorios():
    escritorios = Escritorio.query.order_by(Escritorio.nome).all()
    return render_template('admin/escritorios.html', escritorios=escritorios)

@admin_bp.route('/escritorios/novo', methods=['POST'])
@admin_required
def cadastrar_escritorio():
    novo = Escritorio(
        nome=request.form.get('nome'),
        cnpj=request.form.get('cnpj'),
        email=request.form.get('email'),
        telefone=request.form.get('telefone')
    )
    db.session.add(novo)
    db.session.commit()
    flash('Escritório cadastrado com sucesso!', 'success')
    return redirect(url_for('admin.listar_escritorios'))

@admin_bp.route('/escritorios/editar/<int:id>', methods=['POST'])
@admin_required
def editar_escritorio(id):
    escritorio = Escritorio.query.get_or_404(id)
    escritorio.nome = request.form.get('nome')
    escritorio.cnpj = request.form.get('cnpj')
    escritorio.email = request.form.get('email')
    escritorio.telefone = request.form.get('telefone')
    db.session.commit()
    flash('Escritório atualizado com sucesso!', 'success')
    return redirect(url_for('admin.listar_escritorios'))

@admin_bp.route('/escritorios/excluir/<int:id>', methods=['POST'])
@admin_required
def excluir_escritorio(id):
    escritorio = Escritorio.query.get_or_404(id)
    try:
        db.session.delete(escritorio)
        db.session.commit()
        flash('Escritório excluído com sucesso!', 'success')
    except:
        db.session.rollback()
        flash('Não é possível excluir. Existem empresas vinculadas a este escritório.', 'danger')
    return redirect(url_for('admin.listar_escritorios'))

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
    escritorios = Escritorio.query.order_by(Escritorio.nome).all()
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
            dia_vencimento=int(request.form.get('dia_vencimento', 10)),
            escritorio_id=request.form.get('escritorio_id') or None
        )
        nova.slug = gerar_slug(nova.nome_fantasia or nova.razao_social)
        db.session.add(nova)
        db.session.commit()
        return redirect(url_for('admin.listar_empresas'))
    return render_template('admin/form_empresa.html', empresa=None, escritorios=escritorios)

@admin_bp.route('/empresas/editar/<int:id>', methods=['GET', 'POST'])
@admin_required
def editar_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    escritorios = Escritorio.query.order_by(Escritorio.nome).all()
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
        empresa.escritorio_id = request.form.get('escritorio_id') or None
        empresa.slug = gerar_slug(empresa.nome_fantasia or empresa.razao_social)
        
        db.session.commit()
        return redirect(url_for('admin.listar_empresas'))
    return render_template('admin/form_empresa.html', empresa=empresa, escritorios=escritorios)

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

# --- GESTÃO DE TRABALHADORES ---
@admin_bp.route('/api/buscar_cpf_trabalhador/<cpf>')
@admin_required
def buscar_cpf_trabalhador(cpf):
    t = Trabalhador.query.filter_by(cpf=cpf).first()
    if t:
        return jsonify({
            'encontrado': True,
            'nome': t.nome, 'rg': t.rg, 'orgao_expedidor': t.orgao_expedidor,
            'pis': t.pis, 'ctps': t.ctps, 'estado_civil': t.estado_civil,
            'data_nascimento': t.data_nascimento.strftime('%Y-%m-%d') if t.data_nascimento else '',
            'email': t.email, 'telefone': t.telefone, 'profissao': t.profissao, 'filiacao': t.filiacao,
            'cep': t.cep, 'logradouro': t.logradouro, 'numero': t.numero, 'complemento': t.complemento,
            'bairro': t.bairro, 'cidade': t.cidade, 'estado': t.estado,
            'status_atual': t.status
        })
    return jsonify({'encontrado': False})

@admin_bp.route('/trabalhadores')
@admin_required
def listar_trabalhadores():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    query = Trabalhador.query
    if search:
        query = query.filter(Trabalhador.nome.like(f'%{search}%') | Trabalhador.cpf.like(f'%{search}%'))
    pagination = query.order_by(Trabalhador.status.asc(), Trabalhador.nome).paginate(page=page, per_page=15)
    return render_template('admin/trabalhadores.html', pagination=pagination, search=search)

@admin_bp.route('/trabalhadores/novo', methods=['GET', 'POST'])
@admin_required
def cadastrar_trabalhador():
    empresas = Empresa.query.all()
    if request.method == 'POST':
        cpf = request.form.get('cpf')
        t = Trabalhador.query.filter_by(cpf=cpf).first()
        if not t:
            t = Trabalhador(cpf=cpf)
            db.session.add(t)
            flash('Novo colaborador cadastrado com sucesso!', 'success')
        else:
            flash('Colaborador já existia na base global. Dados atualizados e vínculo recriado!', 'info')

        data_nasc_str = request.form.get('data_nascimento')
        data_adm_str = request.form.get('data_admissao')
        
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
        
        t.empresa_id = request.form.get('empresa_id')
        t.status = 'Ativo'
        t.data_desligamento = None
        t.motivo_desligamento = None
        
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
        trabalhador.empresa_id = request.form.get('empresa_id')
        
        db.session.commit()
        flash('Cadastro atualizado com sucesso!', 'success')
        return redirect(url_for('admin.listar_trabalhadores'))
    return render_template('admin/form_trabalhador.html', trabalhador=trabalhador, empresas=empresas)

@admin_bp.route('/trabalhadores/inativar/<int:id>', methods=['POST'])
@admin_required
def inativar_trabalhador(id):
    if current_user.role != 'admin':
        return "Acesso Negado", 403
        
    t = Trabalhador.query.get_or_404(id)
    t.status = 'Inativo'
    
    data_desl_str = request.form.get('data_desligamento')
    motivo = request.form.get('motivo_desligamento')
    
    t.data_desligamento = datetime.strptime(data_desl_str, '%Y-%m-%d').date() if data_desl_str else datetime.now().date()
    t.motivo_desligamento = motivo
    
    db.session.commit()
    flash(f'Trabalhador {t.nome} foi inativado. Motivo: {t.motivo_desligamento}', 'warning')
    return redirect(url_for('admin.listar_trabalhadores'))

@admin_bp.route('/trabalhadores/reativar/<int:id>', methods=['POST'])
@admin_required
def reativar_trabalhador(id):
    if current_user.role != 'admin':
        return "Acesso Negado", 403
        
    t = Trabalhador.query.get_or_404(id)
    t.status = 'Ativo'
    t.data_desligamento = None
    t.motivo_desligamento = None
    db.session.commit()
    flash(f'Trabalhador {t.nome} reativado com sucesso!', 'success')
    return redirect(url_for('admin.listar_trabalhadores'))

# --- MOTOR DE FATURAMENTO ---
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
            
            gateway_id, boleto_url = criar_cobranca(empresa, f)
            if gateway_id:
                f.gateway_id = gateway_id
                f.boleto_url = boleto_url

            db.session.add(f)
            faturas_geradas.append((empresa, f))

    db.session.commit()
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

@admin_bp.route('/faturamento/imprimir/<int:id>')
@login_required 
def imprimir_fatura(id):
    fatura = Fatura.query.get_or_404(id)
    if current_user.role != 'admin' and current_user.empresa_id != fatura.empresa_id:
        abort(403)
    return render_template('admin/recibo_fatura.html', fatura=fatura)

# --- NOVA ROTA: GERADOR DE NOTIFICAÇÃO EXTRAJUDICIAL ---
@admin_bp.route('/faturamento/notificacao/<int:id>')
@admin_required
def gerar_notificacao(id):
    fatura = Fatura.query.get_or_404(id)
    if fatura.status == 'Pago':
        flash('Esta fatura já se encontra paga. Notificação bloqueada.', 'warning')
        return redirect(url_for('admin.menu_faturamento'))
    
    return render_template('admin/notificacao_carta.html', fatura=fatura, data_atual=datetime.now())

# --- NOVA ROTA: CENTRAL DE RELATÓRIOS INTELIGENTES ---
@admin_bp.route('/relatorios')
@admin_required
def central_relatorios():
    tipo = request.args.get('tipo', 'financeiro')
    competencia = request.args.get('competencia', datetime.now().strftime('%m/%Y'))
    
    dados = {}
    
    if tipo == 'financeiro':
        faturas = Fatura.query.filter_by(competencia=competencia).all()
        dados['pagas'] = sum(f.valor_total for f in faturas if f.status == 'Pago')
        dados['pendentes'] = sum(f.valor_total for f in faturas if f.status != 'Pago')
        dados['faturas'] = faturas
        
    elif tipo == 'cadastral':
        # Novas empresas este mês
        dados['novas_empresas'] = Empresa.query.order_by(Empresa.id.desc()).limit(20).all()
        # Demissões recentes (Turnover)
        dados['demissoes'] = Trabalhador.query.filter(Trabalhador.status == 'Inativo').order_by(Trabalhador.data_desligamento.desc()).limit(50).all()
        
    elif tipo == 'clinico':
        if len(competencia.split('/')) == 2:
            m, y = competencia.split('/')
            consultas = Consulta.query.filter(
                db.extract('month', Consulta.data_agendada) == int(m),
                db.extract('year', Consulta.data_agendada) == int(y)
            ).order_by(Consulta.data_agendada.desc()).all()
            
            dados['consultas'] = consultas
            dados['realizadas'] = len([c for c in consultas if c.status == 'Realizada'])
            dados['agendadas'] = len(consultas) - dados['realizadas']

    return render_template('admin/relatorios.html', tipo=tipo, competencia=competencia, dados=dados)

# --- GESTÃO DE USUÁRIOS E WEBHOOK (MANTIDOS INTACTOS) ---
@admin_bp.route('/usuarios')
@admin_required
def listar_usuarios():
    if current_user.role != 'admin': return "Acesso Negado", 403
    usuarios = Usuario.query.all()
    return render_template('admin/usuarios.html', usuarios=usuarios)

@admin_bp.route('/usuarios/novo', methods=['GET', 'POST'])
@admin_required
def cadastrar_usuario():
    if current_user.role != 'admin': return "Acesso Negado", 403
    empresas = Empresa.query.all()
    clinicas = Clinica.query.all() 
    escritorios = Escritorio.query.all() 
    
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        role = request.form.get('role')
        empresa_id = request.form.get('empresa_id') or None
        clinica_id = request.form.get('clinica_id') or None
        escritorio_id = request.form.get('escritorio_id') or None
        if role == 'admin': empresa_id = clinica_id = escritorio_id = None
        elif role == 'cliente': clinica_id = escritorio_id = None
        elif role == 'clinica': empresa_id = escritorio_id = None
        elif role == 'contador': empresa_id = clinica_id = None
        
        novo_usuario = Usuario(email=email, role=role, empresa_id=empresa_id, clinica_id=clinica_id, escritorio_id=escritorio_id)
        novo_usuario.set_senha(senha)
        db.session.add(novo_usuario)
        db.session.commit()
        return redirect(url_for('admin.listar_usuarios'))
    return render_template('admin/form_usuario.html', empresas=empresas, clinicas=clinicas, escritorios=escritorios, usuario=None)

@admin_bp.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@admin_required
def editar_usuario(id):
    if current_user.role != 'admin': return "Acesso Negado", 403
    usuario = Usuario.query.get_or_404(id)
    empresas = Empresa.query.all()
    clinicas = Clinica.query.all()
    escritorios = Escritorio.query.all()
    if request.method == 'POST':
        usuario.email = request.form.get('email')
        usuario.role = request.form.get('role')
        empresa_id = request.form.get('empresa_id') or None
        clinica_id = request.form.get('clinica_id') or None
        escritorio_id = request.form.get('escritorio_id') or None
        if usuario.role == 'admin': usuario.empresa_id = usuario.clinica_id = usuario.escritorio_id = None
        elif usuario.role == 'cliente': usuario.empresa_id = empresa_id; usuario.clinica_id = usuario.escritorio_id = None
        elif usuario.role == 'clinica': usuario.clinica_id = clinica_id; usuario.empresa_id = usuario.escritorio_id = None
        elif usuario.role == 'contador': usuario.escritorio_id = escritorio_id; usuario.empresa_id = usuario.clinica_id = None
            
        nova_senha = request.form.get('senha')
        if nova_senha: usuario.set_senha(nova_senha)
        db.session.commit()
        return redirect(url_for('admin.listar_usuarios'))
    return render_template('admin/form_usuario.html', empresas=empresas, clinicas=clinicas, escritorios=escritorios, usuario=usuario)

@admin_bp.route('/usuarios/excluir/<int:id>', methods=['POST'])
@admin_required
def excluir_usuario(id):
    if current_user.role != 'admin': return "Acesso Negado", 403
    if id == current_user.id: return "Erro: Você não pode excluir sua própria conta.", 400
    usuario = Usuario.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()
    return redirect(url_for('admin.listar_usuarios'))

@admin_bp.route('/webhook/asaas', methods=['POST'])
def webhook_asaas():
    dados = request.json
    if not dados: return jsonify({"erro": "Nenhum dado recebido"}), 400
    eventos_pagos = ['PAYMENT_RECEIVED', 'PAYMENT_CONFIRMED']
    if dados.get('event') in eventos_pagos:
        pagamento = dados.get('payment', {})
        gateway_id = pagamento.get('id')
        if gateway_id:
            fatura = Fatura.query.filter_by(gateway_id=gateway_id).first()
            if fatura and fatura.status != 'Pago':
                fatura.status = 'Pago'
                fatura.data_pagamento = datetime.now()
                db.session.commit()
    return jsonify({"status": "recebido"}), 200

@admin_bp.route('/executar-tarefa-faturamento-secreta', methods=['POST'])
def gatilho_faturamento_externo():
    chave = request.headers.get('X-Task-Key')
    if chave != os.getenv('SECRET_KEY'): return "Não autorizado", 403
    from app.tasks import processar_faturamento_automatico
    processar_faturamento_automatico()
    return "Faturamento concluído com sucesso!", 200