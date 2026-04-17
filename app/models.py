from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import unicodedata
import re

db = SQLAlchemy()

# Função para transformar "Pizza Leste S/A" em "pizza-leste-sa"
def gerar_slug(texto):
    if not texto:
        return "empresa-sem-nome"
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    texto = re.sub(r'[^\w\s-]', '', texto.lower())
    return re.sub(r'[-\s]+', '-', texto).strip('-_')

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
    
    trabalhadores = db.relationship('Trabalhador', backref='empresa', lazy=True, cascade="all, delete-orphan")
    faturas = db.relationship('Fatura', backref='empresa', lazy=True, cascade="all, delete-orphan")

# ==========================================
# ENTIDADE: TRABALHADOR (VIDAS)
# ==========================================
class Trabalhador(db.Model):
    __tablename__ = 'trabalhadores'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
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
    
    status = db.Column(db.String(20), default='Ativo')
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)

# ==========================================
# ENTIDADE: FATURA (PREPARADA PARA BANCO)
# ==========================================
class Fatura(db.Model):
    __tablename__ = 'faturas'
    id = db.Column(db.Integer, primary_key=True)
    competencia = db.Column(db.String(7), nullable=False) # Formato: MM/AAAA
    quantidade_vidas = db.Column(db.Integer, nullable=False)
    valor_unitario = db.Column(db.Float, nullable=False)
    valor_total = db.Column(db.Float, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    
    data_geracao = db.Column(db.DateTime, default=datetime.utcnow)
    data_pagamento = db.Column(db.DateTime, nullable=True) # Preenchido quando o banco avisar
    status = db.Column(db.String(20), default='Pendente') # Pendente, Pago, Vencido
    
    # --- CAMPOS DE INTEGRAÇÃO BANCÁRIA ---
    gateway_id = db.Column(db.String(100), unique=True, nullable=True) # ID da cobrança no Banco
    boleto_url = db.Column(db.String(500), nullable=True)             # Link do PDF do Banco
    linha_digitavel = db.Column(db.String(150), nullable=True)        # Código de barras para copiar
    pix_copia_e_cola = db.Column(db.Text, nullable=True)              # String do PIX
    # -------------------------------------
    
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)

# ==========================================
# USUÁRIOS
# ==========================================
class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(512), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='cliente')
    
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=True)
    empresa = db.relationship('Empresa', backref=db.backref('usuario', uselist=False))

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)
