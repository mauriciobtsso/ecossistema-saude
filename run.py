from app import create_app, db
from app.models import Usuario

app = create_app()

# Este bloco roda assim que o servidor liga
with app.app_context():
    # Cria as tabelas se elas não existirem
    db.create_all()
    
    # Verifica se já existe um admin, se não, cria um para você conseguir logar
    admin_existente = Usuario.query.filter_by(role='admin').first()
    if not admin_existente:
        admin = Usuario(email="admin@ecossistema.com", role="admin")
        admin.set_senha("admin123")
        db.session.add(admin)
        db.session.commit()
        print("Usuário Admin inicial criado: admin@ecossistema.com / admin123")

if __name__ == "__main__":
    app.run()
