# app/clinicas/models.py

from app.models import db # Importamos o banco de dados principal
from datetime import datetime

# Tabela de Associação (Muitos-para-Muitos) entre Clínicas e Especialidades
clinica_especialidade = db.Table('clinica_especialidade',
    db.Column('clinica_id', db.Integer, db.ForeignKey('clinicas.id'), primary_key=True),
    db.Column('especialidade_id', db.Integer, db.ForeignKey('especialidades.id'), primary_key=True)
)

class Especialidade(db.Model):
    __tablename__ = 'especialidades'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True) # Ex: Cardiologia, Odontologia
    descricao = db.Column(db.String(255))
    
    # Relação com clínicas
    clinicas = db.relationship('Clinica', secondary=clinica_especialidade, backref=db.backref('especialidades_oferecidas', lazy='dynamic'))

class Clinica(db.Model):
    __tablename__ = 'clinicas'
    id = db.Column(db.Integer, primary_key=True)
    razao_social = db.Column(db.String(150), nullable=False)
    nome_fantasia = db.Column(db.String(150))
    cnpj = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True)
    telefone = db.Column(db.String(20))
    
    # Endereço
    cep = db.Column(db.String(10))
    logradouro = db.Column(db.String(150))
    numero = db.Column(db.String(20))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    
    # Configurações de Repasse (Quanto o SindiMedic paga à Clínica)
    dia_fechamento = db.Column(db.Integer, default=5) # Dia do mês para a clínica enviar a fatura
    
    status = db.Column(db.String(20), default='Ativa') # Ativa, Inativa, Bloqueada
    data_cadastro = db.Column(db.DateTime, default=datetime.now)

class Consulta(db.Model):
    __tablename__ = 'consultas'
    id = db.Column(db.Integer, primary_key=True)
    
    # Chaves Estrangeiras conectando todo o ecossistema
    trabalhador_id = db.Column(db.Integer, db.ForeignKey('trabalhadores.id'), nullable=False)
    clinica_id = db.Column(db.Integer, db.ForeignKey('clinicas.id'), nullable=False)
    especialidade_id = db.Column(db.Integer, db.ForeignKey('especialidades.id'), nullable=False)
    
    # Dados do Agendamento
    data_solicitacao = db.Column(db.DateTime, default=datetime.now)
    data_agendada = db.Column(db.DateTime, nullable=True) # Preenchido quando a clínica confirma
    
    # Status do fluxo: Pendente (Paciente pediu) -> Confirmada (Clínica aceitou) -> Realizada (Paciente foi) -> Faturada (SindiMedic pagou clínica)
    status = db.Column(db.String(30), default='Pendente') 
    
    # Financeiro (Opcional, mas útil para o Cenário B)
    valor_repasse = db.Column(db.Float, nullable=True) # Valor acordado a pagar à clínica por esta consulta específica
    
    # Relações (para podermos fazer `consulta.paciente.nome` ou `consulta.clinica.nome_fantasia`)
    paciente = db.relationship('Trabalhador', backref='minhas_consultas')
    clinica = db.relationship('Clinica', backref='consultas_agendadas')
    especialidade = db.relationship('Especialidade')