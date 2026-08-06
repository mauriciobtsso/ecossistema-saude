from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from app.models import db, Empresa, Usuario, gerar_slug, ConfiguracaoSite, ServicoPortifolio
import re

# Blueprint do Site Público (sem restrição de login)
site_bp = Blueprint('site', __name__, template_folder='templates')

def obter_configuracoes():
    """Garante que sempre exista uma configuração base caso o banco esteja vazio"""
    config = ConfiguracaoSite.query.first()
    if not config:
        config = ConfiguracaoSite()
        db.session.add(config)
        db.session.commit()
    return config

@site_bp.route('/')
def index():
    # Consulta ao BD para tornar o site dinâmico
    config = obter_configuracoes()
    servicos = ServicoPortifolio.query.filter_by(ativo=True).order_by(ServicoPortifolio.ordem).all()
    
    return render_template('site/index.html', config=config, servicos=servicos)

@site_bp.route('/termos-de-uso')
def termos():
    config = obter_configuracoes()
    return render_template('site/termos.html', config=config)

@site_bp.route('/politica-de-privacidade')
def privacidade():
    config = obter_configuracoes()
    return render_template('site/privacidade.html', config=config)

@site_bp.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        cnpj_raw = request.form.get('cnpj', '')
        cnpj_clean = re.sub(r'\D', '', cnpj_raw)
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        # Formata CNPJ de volta para manter o padrão do banco (00.000.000/0001-00)
        if len(cnpj_clean) == 14:
            cnpj = f"{cnpj_clean[:2]}.{cnpj_clean[2:5]}.{cnpj_clean[5:8]}/{cnpj_clean[8:12]}-{cnpj_clean[12:]}"
        else:
            cnpj = cnpj_raw

        # Verifica se a empresa já existe
        empresa_existente = Empresa.query.filter_by(cnpj=cnpj).first()
        if empresa_existente:
            flash('Este CNPJ já possui cadastro. Faça o login ou recupere a sua senha.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Verifica se o e-mail do usuário já existe
        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            flash('Este e-mail já está em uso.', 'danger')
            return redirect(url_for('site.cadastro'))

        # 1. Cria a Empresa
        nova_empresa = Empresa(
            cnpj=cnpj,
            razao_social=request.form.get('razao_social'),
            nome_fantasia=request.form.get('nome_fantasia'),
            cep=request.form.get('cep'),
            logradouro=request.form.get('logradouro'),
            numero=request.form.get('numero'),
            bairro=request.form.get('bairro'),
            cidade=request.form.get('cidade'),
            estado=request.form.get('estado'),
            telefone=request.form.get('telefone'),
            email=email,
            status='Ativa',
            valor_por_vida=50.0, # Valor contratual padrão
            dia_vencimento=10
        )
        nova_empresa.slug = gerar_slug(nova_empresa.nome_fantasia or nova_empresa.razao_social)
        
        db.session.add(nova_empresa)
        db.session.flush()

        # 2. Cria o Usuário Administrador (Cliente) atrelado a esta nova empresa
        novo_usuario = Usuario(
            email=email,
            role='cliente',
            empresa_id=nova_empresa.id
        )
        novo_usuario.set_senha(senha)
        db.session.add(novo_usuario)
        
        db.session.commit()
        flash('Cadastro concluído com sucesso! Faça login para acessar o seu painel de RH.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('site/cadastro.html')

# ==========================================
# ROTAS DE SEO E INTELIGÊNCIA ARTIFICIAL
# ==========================================

@site_bp.route('/robots.txt')
def robots_txt():
    """Diz aos motores de busca o que podem e não podem indexar"""
    url_base = request.url_root # Pega o domínio automaticamente (ex: https://medicsind.com.br/)
    
    conteudo = f"""User-agent: *
Disallow: /admin/
Disallow: /cliente/
Disallow: /paciente/
Disallow: /clinica/
Allow: /

Sitemap: {url_base}sitemap.xml
"""
    # Usamos o Response do Flask para devolver texto puro em vez de HTML
    return Response(conteudo, mimetype="text/plain")


@site_bp.route('/sitemap.xml')
def sitemap_xml():
    """Mapa do site para o Google indexar as páginas públicas"""
    url_base = request.url_root.rstrip('/') # Remove a última barra
    
    conteudo = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{url_base}/</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{url_base}/cadastro</loc>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>{url_base}/termos-de-uso</loc>
    <changefreq>yearly</changefreq>
    <priority>0.5</priority>
  </url>
  <url>
    <loc>{url_base}/politica-de-privacidade</loc>
    <changefreq>yearly</changefreq>
    <priority>0.5</priority>
  </url>
</urlset>"""
    
    # mimetype="application/xml" garante que o navegador e os bots leiam como XML estruturado
    return Response(conteudo, mimetype="application/xml")


@site_bp.route('/llms.txt')
def llms_txt():
    """Cartão de visita otimizado para Inteligências Artificiais (LLMs)"""
    config = obter_configuracoes()
    url_base = request.url_root
    
    # Aqui utilizamos os dados do banco para alimentar a IA!
    conteudo = f"""# {config.nome_empresa}

> {config.seo_description}

## Sobre o Projeto
A {config.nome_empresa} é um ecossistema completo de gestão de saúde projetado para conectar Sindicatos, Clínicas, Contabilidades e Trabalhadores. Nossa plataforma automatiza faturamentos, gerencia elegibilidade em tempo real e entrega relatórios inteligentes.

## Principais Soluções
- Gestão de Vidas e Elegibilidade
- Hub de Contabilidades (Multi-Empresas)
- Agendamento e Repasses para Rede Credenciada
- Faturamento e Cobrança Automatizada

## Links Importantes
- [Página Inicial]({url_base})
- [Criar Conta como Empresa]({url_base}cadastro)
- [Acesso ao Portal Corporativo]({url_base}login)

## Contato
Para suporte e atendimento comercial, acesse nosso site oficial.
"""
    return Response(conteudo, mimetype="text/plain")