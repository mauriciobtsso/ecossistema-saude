from flask import render_template, request, redirect, url_for
from .models import db, Empresa, Trabalhador, Fatura
from flask import current_app as app
from datetime import datetime
from sqlalchemy import func

# ==========================================
# 1. DIRECIONAMENTO E DASHBOARD
# ==========================================

@app.route('/')
def index():
    # Garante que o usuário caia no Dashboard ao acessar a raiz
    return redirect(url_for('dashboard'))

@app.route('/admin')
def dashboard():
    total_empresas = Empresa.query.count()
    total_vidas = Trabalhador.query.filter_by(status='Ativo').count()
    
    # Receita Prevista baseada em vidas ativas vinculadas às empresas
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

# ==========================================
# 2. GESTÃO DE EMPRESAS (CRUD)
# ==========================================

@app.route('/admin/empresas')
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

@app.route('/admin/empresas/novo', methods=['GET', 'POST'])
def cadastrar_empresa():
    if request.method == 'POST':
        valor_limpo = request.form.get('valor_por_vida', '50,00').replace('.', '').replace(',', '.')
        nova_empresa = Empresa(
            razao_social=request.form.get('razao_social'),
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
        db.session.add(nova_empresa)
        db.session.commit()
        return redirect(url_for('listar_empresas'))
    return render_template('admin/form_empresa.html', empresa=None)

@app.route('/admin/empresas/editar/<int:id>', methods=['GET', 'POST'])
def editar_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    if request.method == 'POST':
        valor_limpo = request.form.get('valor_por_vida', '50,00').replace('.', '').replace(',', '.')
        empresa.razao_social = request.form.get('razao_social')
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
        db.session.commit()
        return redirect(url_for('listar_empresas'))
    return render_template('admin/form_empresa.html', empresa=empresa)

@app.route('/admin/empresas/excluir/<int:id>', methods=['POST'])
def excluir_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    db.session.delete(empresa)
    db.session.commit()
    return redirect(url_for('listar_empresas'))

@app.route('/admin/empresas/visualizar/<int:id>')
def visualizar_empresa(id):
    empresa = Empresa.query.get_or_404(id)
    trabalhadores = Trabalhador.query.filter_by(empresa_id=id).all()
    vidas_ativas = len([t for t in trabalhadores if t.status == 'Ativo'])
    faturamento_previsto = vidas_ativas * empresa.valor_por_vida
    return render_template('admin/detalhe_empresa.html', 
                           empresa=empresa, trabalhadores=trabalhadores,
                           vidas_ativas=vidas_ativas, faturamento_previsto=faturamento_previsto)

# ==========================================
# 3. GESTÃO DE TRABALHADORES (CRUD)
# ==========================================

@app.route('/admin/trabalhadores')
def listar_trabalhadores():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    query = Trabalhador.query
    if search:
        query = query.filter(Trabalhador.nome.like(f'%{search}%') | Trabalhador.cpf.like(f'%{search}%'))
    pagination = query.order_by(Trabalhador.nome).paginate(page=page, per_page=15)
    return render_template('admin/trabalhadores.html', pagination=pagination, search=search)

@app.route('/admin/trabalhadores/novo', methods=['GET', 'POST'])
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
        return redirect(url_for('listar_trabalhadores'))
    return render_template('admin/form_trabalhador.html', empresas=empresas, trabalhador=None)

@app.route('/admin/trabalhadores/editar/<int:id>', methods=['GET', 'POST'])
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
        return redirect(url_for('listar_trabalhadores'))
    return render_template('admin/form_trabalhador.html', trabalhador=trabalhador, empresas=empresas)

@app.route('/admin/trabalhadores/excluir/<int:id>', methods=['POST'])
def excluir_trabalhador(id):
    t = Trabalhador.query.get_or_404(id)
    db.session.delete(t)
    db.session.commit()
    return redirect(url_for('listar_trabalhadores'))

# ==========================================
# 4. MOTOR DE FATURAMENTO
# ==========================================

@app.route('/admin/faturamento')
def menu_faturamento():
    faturas = Fatura.query.order_by(Fatura.data_geracao.desc()).all()
    total_pendente = sum(f.valor_total for f in faturas if f.status == 'Pendente')
    total_pago = sum(f.valor_total for f in faturas if f.status == 'Pago')
    return render_template('admin/faturamento.html', 
                           faturas=faturas, total_pendente=total_pendente, total_pago=total_pago)

@app.route('/admin/faturamento/gerar', methods=['POST'])
def gerar_faturamento():
    mes_ano = request.form.get('competencia')
    if not mes_ano: return redirect(url_for('menu_faturamento'))
    competencia = datetime.strptime(mes_ano, '%Y-%m').strftime('%m/%Y')
    empresas = Empresa.query.filter_by(status='Ativa').all()
    for empresa in empresas:
        if Fatura.query.filter_by(empresa_id=empresa.id, competencia=competencia).first(): continue
        qtd_vidas = Trabalhador.query.filter_by(empresa_id=empresa.id, status='Ativo').count()
        if qtd_vidas > 0:
            valor_total = qtd_vidas * empresa.valor_por_vida
            hoje = datetime.now()
            try: vencimento = hoje.replace(day=empresa.dia_vencimento)
            except ValueError: vencimento = hoje.replace(day=28)
            nova_fatura = Fatura(
                competencia=competencia, quantidade_vidas=qtd_vidas, valor_unitario=empresa.valor_por_vida,
                valor_total=valor_total, data_vencimento=vencimento, status='Pendente', empresa_id=empresa.id
            )
            db.session.add(nova_fatura)
    db.session.commit()
    return redirect(url_for('menu_faturamento'))

@app.route('/admin/faturamento/pagar/<int:id>', methods=['POST'])
def baixar_fatura(id):
    fatura = Fatura.query.get_or_404(id)
    if fatura.status == 'Pendente':
        fatura.status = 'Pago'
        db.session.commit()
    return redirect(url_for('menu_faturamento'))

@app.route('/admin/faturamento/imprimir/<int:id>')
def imprimir_fatura(id):
    fatura = Fatura.query.get_or_404(id)
    return render_template('admin/recibo_fatura.html', fatura=fatura)