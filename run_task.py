# run_task.py
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente (.env local ou Environment do Render)
load_dotenv()

from app import create_app, db
from app.tasks import processar_faturamento_automatico

app = create_app()
with app.app_context():
    print("Iniciando agendamento diário...")
    processar_faturamento_automatico()