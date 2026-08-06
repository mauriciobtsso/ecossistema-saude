from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import unicodedata
import re

db = SQLAlchemy()

def gerar_slug(texto):
    if not texto:
        return "empresa-sem-nome"
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    texto = re.sub(r'[^\w\s-]', '', texto.lower())
    return re.sub(r'[-\s]+', '-', texto).strip('-_')

# ==========================================
# ENTIDADE: ESCRITÓRIO DE CONTABILIDADE
# ==========================================
class Escritorio(db.Model):
    __tablename__ = 'escritorios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cnpj = db.Column(db.String(18), unique=True, nullable=False)
    email = db.Column(db.String(100))
    telefone = db.Column(db.String(20))
    status = db.Column(db.String(20), default='Ativo')
    
    # Um escritório gere várias empresas
    empresas = db.relationship('Empresa', backref='escritorio_vinculado', lazy=True)

# ==========================================
# ENTIDADE: EMPRESA
# ==========================================
class Empresa(db.Model):
    __tablename__ = 'empresas'
    id = db.Column(db.Integer, primary_key=True)
    razao_social = db.Column(db.String(150), nullable=False)
    nome_fantasia = db.Column(db.String(150))
    cnpj = db.Column(db.String(18), unique=True, nullable=False)
    
    slug = db.Column(db.String(150), unique=True, nullable=True)
    
    logradouro = db.Column(db.String(200))
    numero = db.Column(db.String(20))
    complemento = db.Column(db.String(100))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    cep = db.Column(db.String(10))
    email = db.Column(db.String(100))
    telefone = db.Column(db.String(20))
    responsavel = db.Column(db.String(100))
    
    valor_por_vida = db.Column(db.Float, default=50.0)
    dia_vencimento = db.Column(db.Integer, default=10)
    status = db.Column(db.String(20), default='Ativa') # Ativa, Suspensa, Cancelada
    
    # Vínculo com a Contabilidade
    escritorio_id = db.Column(db.Integer, db.ForeignKey('escritorios.id'), nullable=True)
    
    trabalhadores = db.relationship('Trabalhador', backref='empresa', lazy=True, cascade="all, delete-orphan")
    faturas = db.relationship('Fatura', backref='empresa', lazy=True, cascade="all, delete-orphan")

# ==========================================
# ENTIDADE: TRABALHADOR (VIDAS) - GLOBALIZADO
# ==========================================
class Trabalhador(db.Model):
    __tablename__ = 'trabalhadores'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False, index=True)
    
    rg = db.Column(db.String(20))
    orgao_expedidor = db.Column(db.String(20))
    pis = db.Column(db.String(20))
    ctps = db.Column(db.String(50))
    estado_civil = db.Column(db.String(50))
    
    data_nascimento = db.Column(db.Date)
    email = db.Column(db.String(100))
    telefone = db.Column(db.String(20))
    profissao = db.Column(db.String(100))
    filiacao = db.Column(db.String(200))
    
    cep = db.Column(db.String(10))
    logradouro = db.Column(db.String(200))
    numero = db.Column(db.String(20))
    complemento = db.Column(db.String(100))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    
    data_admissao = db.Column(db.Date)
    data_desligamento = db.Column(db.Date)
    motivo_desligamento = db.Column(db.String(255))
    
    status = db.Column(db.String(20), default='Ativo')
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=True)

# ==========================================
# ENTIDADE: FATURA (PREPARADA PARA BANCO)
# ==========================================
class Fatura(db.Model):
    __tablename__ = 'faturas'
    id = db.Column(db.Integer, primary_key=True)
    competencia = db.Column(db.String(7), nullable=False)
    quantidade_vidas = db.Column(db.Integer, nullable=False)
    valor_unitario = db.Column(db.Float, nullable=False)
    valor_total = db.Column(db.Float, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    
    data_geracao = db.Column(db.DateTime, default=datetime.utcnow)
    data_pagamento = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='Pendente')
    
    gateway_id = db.Column(db.String(100), unique=True, nullable=True)
    boleto_url = db.Column(db.String(500), nullable=True)
    linha_digitavel = db.Column(db.String(150), nullable=True)
    pix_copia_e_cola = db.Column(db.Text, nullable=True)
    
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)

# ==========================================
# USUÁRIOS
# ==========================================
class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(512), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='cliente') # admin, cliente, clinica, contador
    
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=True)
    empresa = db.relationship('Empresa', backref=db.backref('usuario', uselist=False))

    clinica_id = db.Column(db.Integer, db.ForeignKey('clinicas.id'), nullable=True)
    clinica = db.relationship('Clinica', backref=db.backref('usuario', uselist=False))

    escritorio_id = db.Column(db.Integer, db.ForeignKey('escritorios.id'), nullable=True)
    escritorio = db.relationship('Escritorio', backref=db.backref('usuarios', lazy=True))

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)


# ==========================================
# GESTÃO DINÂMICA DO SITE (CMS)
# ==========================================
class ConfiguracaoSite(db.Model):
    __tablename__ = 'configuracoes_site'
    id = db.Column(db.Integer, primary_key=True)
    
    # Dados da Empresa (MedicSind)
    nome_empresa = db.Column(db.String(100), default="MedicSind")
    cnpj = db.Column(db.String(20), nullable=True)
    endereco = db.Column(db.String(255), nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    email_contato = db.Column(db.String(100), nullable=True)
    logo_url = db.Column(db.String(255), nullable=True)
    
    # SEO Semântico
    seo_title = db.Column(db.String(150), default="MedicSind - Gestão de Vidas com Inteligência")
    seo_description = db.Column(db.String(255), default="A plataforma completa para RHs que buscam eficiência operacional e saúde acessível.")
    
    # Textos de Vendas (Copywriting)
    hero_titulo = db.Column(db.String(200), default="Gestão de Vidas com <span class='text-primary'>Inteligência.</span>")
    hero_subtitulo = db.Column(db.Text, default="A plataforma completa para RHs que buscam eficiência operacional e saúde acessível para todos os seus colaboradores.")

class ServicoPortifolio(db.Model):
    __tablename__ = 'servicos_portifolio'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    icone = db.Column(db.String(50), default="fas fa-star") # Para podermos usar os ícones do FontAwesome
    ordem = db.Column(db.Integer, default=0)
    ativo = db.Column(db.Boolean, default=True)