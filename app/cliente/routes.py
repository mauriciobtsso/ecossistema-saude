from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from ..models import db, Empresa, Trabalhador, Fatura
from datetime import datetime
from flask_login import login_required, current_user

cliente_bp = Blueprint('cliente', __name__)

# Dashboard: Visão Geral da Empresa
@cliente_bp.route('/<string:slug>')
@login_required
def dashboard(slug):
    empresa = Empresa.query.filter_by(slug=slug).first_or_404()
    
    if current_user.role != 'admin' and current_user.empresa_id != empresa.id:
        abort(403) # Bloqueia acesso indevido
        
    trabalhadores = Trabalhador.query.filter_by(empresa_id=empresa.id).all()
    # Pega apenas as últimas 5 faturas para o resumo
    faturas = Fatura.query.filter_by(empresa_id=empresa.id).order_by(Fatura.data_geracao.desc()).limit(5).all()
    
    return render_template('cliente/dashboard.html', empresa=empresa, trabalhadores=trabalhadores, faturas=faturas)

# Listagem completa de funcionários do cliente
@cliente_bp.route('/<string:slug>/funcionarios')
@login_required
def listar_trabalhadores(slug):
    empresa = Empresa.query.filter_by(slug=slug).first_or_404()
    
    if current_user.role != 'admin' and current_user.empresa_id != empresa.id:
        abort(403) # Bloqueia acesso indevido
        
    trabalhadores = Trabalhador.query.filter_by(empresa_id=empresa.id).all()
    
    return render_template('cliente/trabalhadores.html', empresa=empresa, trabalhadores=trabalhadores)

# Novo Funcionário pelo Portal (Usa SLUG)
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

# Editar Funcionário (O ID é o do trabalhador, então não muda)
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

# Visualizar Faturas do Cliente
@cliente_bp.route('/<string:slug>/faturas')
@login_required
def listar_faturas(slug):
    empresa = Empresa.query.filter_by(slug=slug).first_or_404()
    
    if current_user.role != 'admin' and current_user.empresa_id != empresa.id:
        abort(403) 
        
    faturas = Fatura.query.filter_by(empresa_id=empresa.id).order_by(Fatura.competencia.desc()).all()
    
    # Descobre a competência atual (Mês/Ano) para saber se a empresa já gerou
    hoje = datetime.now()
    competencia_atual = hoje.strftime('%m/%Y')
    
    # Verifica se a fatura deste mês já existe
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
    
    if current_user.role != 'admin' and current_user.empresa_id != empresa.id:
        abort(403)
        
    hoje = datetime.now()
    competencia_atual = hoje.strftime('%m/%Y')
    
    # Trava de segurança: impede gerar duas faturas para o mesmo mês
    fatura_existente = Fatura.query.filter_by(empresa_id=empresa.id, competencia=competencia_atual).first()
    if fatura_existente:
        flash('A fatura deste mês já foi gerada.', 'warning')
        return redirect(url_for('cliente.listar_faturas', slug=empresa.slug))
        
    # Calcula as vidas ativas
    qtd_vidas = Trabalhador.query.filter_by(empresa_id=empresa.id, status='Ativo').count()
    
    if qtd_vidas == 0:
        flash('Você não possui vidas ativas para faturar.', 'danger')
        return redirect(url_for('cliente.listar_faturas', slug=empresa.slug))
        
    valor_total = qtd_vidas * empresa.valor_por_vida
    
    # Define a data de vencimento baseada no dia configurado na empresa
    try:
        vencimento = hoje.replace(day=empresa.dia_vencimento)
        # Se a empresa gerar DEPOIS do vencimento no mesmo mês, joga para o mês que vem
        if hoje > vencimento:
            if hoje.month == 12:
                vencimento = vencimento.replace(year=hoje.year + 1, month=1)
            else:
                vencimento = vencimento.replace(month=hoje.month + 1)
    except ValueError:
        vencimento = hoje.replace(day=28) # Prevenção para meses curtos se o vencimento for dia 30/31
        
    nova_fatura = Fatura(
        competencia=competencia_atual,
        quantidade_vidas=qtd_vidas,
        valor_unitario=empresa.valor_por_vida,
        valor_total=valor_total,
        data_vencimento=vencimento.date(), # Garantindo formato Date
        status='Pendente',
        empresa_id=empresa.id
    )
    
    db.session.add(nova_fatura)
    db.session.commit()
    
    flash('Fatura gerada com sucesso!', 'success')
    return redirect(url_for('cliente.listar_faturas', slug=empresa.slug))

