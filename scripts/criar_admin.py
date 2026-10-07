from database import criar_tabelas, criar_utilizador, listar_utilizadores

criar_tabelas()

print("\n" + "="*50)
print("🔐 JAM Soft — Criar Utilizador Administrador")
print("="*50 + "\n")

existentes = listar_utilizadores()

if existentes:
    print("⚠️ Já existem utilizadores no sistema:\n")
    for u in existentes:
        print(f"  ID: {u[0]} | Nome: {u[1]} | Username: {u[2]} | Perfil: {u[3]}")
    print("\nSe quiser criar outro administrador, execute novamente e escolha um username diferente.")
else:
    print("Nenhum utilizador encontrado. Vamos criar o primeiro administrador.\n")

nome = input("Nome completo do administrador: ").strip()
username = input("Nome de utilizador (ex: admin): ").strip()
senha = input("Palavra-passe (mínimo 6 caracteres): ").strip()

if len(senha) < 6:
    print("\n❌ Erro: a palavra-passe deve ter pelo menos 6 caracteres.")
elif not nome or not username:
    print("\n❌ Erro: nome e utilizador são obrigatórios.")
else:
    if criar_utilizador(nome, username, senha, perfil="admin"):
        print(f"\n✅ Utilizador '{username}' criado com sucesso!")
        print("   Perfil: Administrador")
        print("\n👉 Agora pode executar: python main.py")
    else:
        print(f"\n❌ Erro: o utilizador '{username}' já existe.")