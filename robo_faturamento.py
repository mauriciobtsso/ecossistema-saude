# robo_faturamento.py
from app import create_app
from app.models import db, Empresa, Trabalhador, Fatura
from datetime import datetime

# Inicia a aplicação para acessar o banco de dados
app = create_app()

def rodar_robo_faturamento():
    with app.app_context():
        hoje = datetime.now()
        dia_atual = hoje.day
        competencia_atual = hoje.strftime('%m/%Y')
        
        print(f"[{hoje.strftime('%Y-%m-%d %H:%M:%S')}] Iniciando varredura do Robô de Faturamento...")
        
        # 1. Busca todas as empresas ativas cujo vencimento é HOJE
        empresas = Empresa.query.filter_by(status='Ativa', dia_vencimento=dia_atual).all()
        
        if not empresas:
            print("Nenhuma empresa com vencimento para hoje.")
            return

        for empresa in empresas:
            # 2. Verifica se a empresa já gerou a fatura manualmente
            fatura_existe = Fatura.query.filter_by(empresa_id=empresa.id, competencia=competencia_atual).first()
            
            if not fatura_existe:
                # 3. Se não gerou, o Robô assume e gera!
                qtd_vidas = Trabalhador.query.filter_by(empresa_id=empresa.id, status='Ativo').count()
                
                if qtd_vidas > 0:
                    valor_total = qtd_vidas * empresa.valor_por_vida
                    
                    try:
                        vencimento = hoje.replace(day=empresa.dia_vencimento)
                    except ValueError:
                        vencimento = hoje.replace(day=28)
                        
                    nova_fatura = Fatura(
                        competencia=competencia_atual,
                        quantidade_vidas=qtd_vidas,
                        valor_unitario=empresa.valor_por_vida,
                        valor_total=valor_total,
                        data_vencimento=vencimento.date(),
                        status='Pendente',
                        empresa_id=empresa.id
                    )
                    
                    db.session.add(nova_fatura)
                    print(f" -> FATURA GERADA AUTOMATICAMENTE: {empresa.nome_fantasia} | Vidas: {qtd_vidas} | Total: R${valor_total}")
                else:
                    print(f" -> Empresa {empresa.nome_fantasia} ignorada (0 vidas ativas).")
            else:
                print(f" -> Empresa {empresa.nome_fantasia} já havia gerado a fatura no portal.")
                
        # Salva tudo no banco
        db.session.commit()
        print("Varredura concluída com sucesso!")

if __name__ == '__main__':
    rodar_robo_faturamento()