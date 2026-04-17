# criar_admin.py
from app import create_app, db
from app.models import Usuario

app = create_app()

with app.app_context():
    # Verifica se já existe um admin
    admin_existente = Usuario.query.filter_by(role='admin').first()
    
    if not admin_existente:
        admin = Usuario(
            email='admin@saude.com',
            role='admin'
        )
        admin.set_senha('admin') # Mude para uma senha forte depois!
        db.session.add(admin)
        db.session.commit()
        print("Usuário Administrador criado com sucesso!")
        print("E-mail: admin@saude.com | Senha: admin")
    else:
        print("Já existe um administrador cadastrado.")