from app import create_app, db
from app.models import Empresa, Trabalhador, Usuario, gerar_slug
from datetime import date

app = create_app()

def popular_banco():
    with app.app_context():
        print("Limpando banco de dados...")
        db.drop_all()
        db.create_all()

        print("Criando Administrador Geral...")
        admin = Usuario(email="admin@saude.com", role="admin")
        admin.set_senha("admin")
        db.session.add(admin)

        # --- EMPRESA 1: PIZZA LESTE ---
        print("Semeando Empresa: Pizza Leste...")
        e1 = Empresa(
            razao_social="Pizza Leste Alimentos LTDA",
            nome_fantasia="Pizza Leste",
            cnpj="11.222.333/0001-44",
            email="financeiro@pizzaleste.com",
            telefone="(11) 98888-7777",
            logradouro="Avenida dos Sabores",
            numero="100",
            bairro="Mooca",
            cidade="São Paulo",
            estado="SP",
            cep="03102-000",
            valor_por_vida=45.00,
            dia_vencimento=10,
            status="Ativa"
        )
        e1.slug = gerar_slug(e1.nome_fantasia)
        db.session.add(e1)
        db.session.flush() # Para gerar o ID e vincular usuários/trabalhadores

        u1 = Usuario(email="pizza@pizzaleste.com", role="cliente", empresa_id=e1.id)
        u1.set_senha("pizzaleste")
        db.session.add(u1)

        t1 = Trabalhador(nome="Carlos Pizzaiolo", cpf="111.111.111-11", profissao="Mestre", empresa_id=e1.id, status="Ativo")
        t2 = Trabalhador(nome="Maria Massa", cpf="222.222.222-22", profissao="Auxiliar", empresa_id=e1.id, status="Ativo")
        db.session.add_all([t1, t2])

        # --- EMPRESA 2: JÓQUEI BEBIDAS ---
        print("Semeando Empresa: Jóquei Bebidas...")
        e2 = Empresa(
            razao_social="Joquei Comercio de Bebidas S/A",
            nome_fantasia="Jóquei Bebidas",
            cnpj="55.666.777/0001-88",
            email="jb@jb.com",
            valor_por_vida=50.00,
            dia_vencimento=15,
            status="Ativa"
        )
        e2.slug = gerar_slug(e2.nome_fantasia)
        db.session.add(e2)
        db.session.flush()

        u2 = Usuario(email="jb@jb.com", role="cliente", empresa_id=e2.id)
        u2.set_senha("joquei")
        db.session.add(u2)

        for i in range(1, 6):
            t = Trabalhador(
                nome=f"Funcionario Joquei {i}", 
                cpf=f"{i}{i}{i}.000.000-00", 
                empresa_id=e2.id, 
                status="Ativo"
            )
            db.session.add(t)

        db.session.commit()
        print("\n✅ Banco de dados semeado com sucesso!")
        print("Admin: admin@saude.com / admin")
        print("Cliente 1: pizza@pizzaleste.com / pizzaleste")
        print("Cliente 2: jb@jb.com / joquei")

if __name__ == "__main__":
    popular_banco()