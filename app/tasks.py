# app/tasks.py
from datetime import datetime
from .models import db, Empresa, Trabalhador, Fatura
from .asaas import criar_cobranca
from .utils import enviar_email
import time

def processar_faturamento_automatico():
    """
    Robô de faturamento automático otimizado para escala.
    Pode ser chamado por um script de agendamento.
    """
    hoje = datetime.now()
    competencia = hoje.strftime('%m/%Y')
    
    # 1. Filtra apenas empresas ativas que ainda não possuem fatura no mês
    # Usamos um subquery para otimizar a busca no banco
    faturas_existentes = db.session.query(Fatura.empresa_id).filter(Fatura.competencia == competencia)
    empresas_para_faturar = Empresa.query.filter(
        Empresa.status == 'Ativa',
        ~Empresa.id.in_(faturas_existentes)
    ).all()

    total_processado = 0
    erros = 0

    print(f"--- Iniciando Robô de Faturamento: {len(empresas_para_faturar)} empresas pendentes ---")

    for empresa in empresas_para_faturar:
        try:
            # Busca vidas ativas
            qtd_vidas = Trabalhador.query.filter_by(empresa_id=empresa.id, status='Ativo').count()
            
            if qtd_vidas > 0:
                valor_total = qtd_vidas * empresa.valor_por_vida
                
                # Define vencimento
                try:
                    vencimento = hoje.replace(day=empresa.dia_vencimento)
                except ValueError:
                    vencimento = hoje.replace(day=28)

                # Cria objeto da fatura
                f = Fatura(
                    competencia=competencia,
                    quantidade_vidas=qtd_vidas,
                    valor_unitario=empresa.valor_por_vida,
                    valor_total=valor_total,
                    data_vencimento=vencimento,
                    status='Pendente',
                    empresa_id=empresa.id
                )

                # Comunicação com Asaas (I/O Bound - Ponto de lentidão)
                gateway_id, boleto_url = criar_cobranca(empresa, f)
                if gateway_id:
                    f.gateway_id = gateway_id
                    f.boleto_url = boleto_url

                db.session.add(f)
                
                # Commit individual ou por pequeno lote para não perder progresso em caso de queda
                db.session.commit() 
                
                # Envio de e-mail (Opcional: Pode ser movido para uma fila separada se ficar lento)
                if empresa.email:
                    enviar_email(
                        assunto=f"Fatura Automática Disponível - {competencia}",
                        destinatario=empresa.email,
                        template="emails/fatura_pronta.html",
                        empresa=empresa,
                        fatura=f
                    )
                
                total_processado += 1
                print(f"✓ Faturado: {empresa.razao_social}")
                
                # Pequena pausa para não estourar o limite de requisições (rate limit) da API do Asaas
                time.sleep(0.5) 

        except Exception as e:
            db.session.rollback()
            erros += 1
            print(f"✗ Erro ao faturar {empresa.razao_social}: {e}")

    print(f"--- Robô finalizado: {total_processado} sucessos, {erros} erros ---")
    return total_processado