from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from app.models import Usuario

app = create_app()

with app.app_context():
    # Cria as tabelas no Neon se elas não existirem
    db.create_all()
    
    # Verifica se já existe um admin, se não, cria um para você conseguir logar
    admin_existente = Usuario.query.filter_by(role='admin').first()
    if not admin_existente:
        # Dica: Você pode mudar este e-mail para admin@sindimedic.com no futuro!
        admin = Usuario(email="admin@ecossistema.com", role="admin")
        admin.set_senha("admin123")
        db.session.add(admin)
        db.session.commit()
        print("Usuário Admin inicial criado no banco de Produção!")

if __name__ == "__main__":
    # Coloquei debug=True para facilitar a visualização de erros no seu terminal local
    app.run(debug=True)