from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Empresa, Trabalhador, Fatura
from app.auth import contador_required

contador_portal_bp = Blueprint('contador_portal', __name__)

@contador_portal_bp.route('/')
@login_required
@contador_required
def dashboard():
    escritorio = current_user.escritorio
    
    # Puxa todas as empresas vinculadas a este escritório
    empresas = Empresa.query.filter_by(escritorio_id=escritorio.id).order_by(Empresa.razao_social).all()
    
    # Métricas Globais do Escritório
    total_empresas = len(empresas)
    total_vidas = 0
    faturas_pendentes = 0
    
    # Coleta as métricas de cada empresa para exibir no card
    empresas_data = []
    for emp in empresas:
        vidas = Trabalhador.query.filter_by(empresa_id=emp.id, status='Ativo').count()
        faturas = Fatura.query.filter_by(empresa_id=emp.id, status='Pendente').count()
        
        total_vidas += vidas
        faturas_pendentes += faturas
        
        empresas_data.append({
            'obj': emp,
            'vidas': vidas,
            'faturas': faturas
        })
        
    return render_template('contador_portal/dashboard.html', 
                           escritorio=escritorio,
                           total_empresas=total_empresas,
                           total_vidas=total_vidas,
                           faturas_pendentes=faturas_pendentes,
                           empresas_data=empresas_data)