# app/utils.py
from flask_mail import Message
from flask import render_template, current_app
from . import mail # Importa a instância do mail que criamos no __init__.py

def enviar_email(assunto, destinatario, template, **kwargs):
    """
    Função genérica para enviar e-mails em HTML.
    - assunto: Título do e-mail
    - destinatario: E-mail de quem vai receber
    - template: Nome do arquivo HTML (ex: 'emails/fatura_pronta.html')
    - kwargs: Variáveis para passar para o template (ex: empresa=empresa, fatura=fatura)
    """
    try:
        msg = Message(
            subject=f"SindiMedic Saúde - {assunto}",
            recipients=[destinatario]
        )
        
        # O corpo do e-mail será um HTML renderizado bonitão
        msg.html = render_template(template, **kwargs)
        
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail para {destinatario}: {e}")
        return False