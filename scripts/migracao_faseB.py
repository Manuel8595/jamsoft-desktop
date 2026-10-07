from database import conectar

c = conectar()
cur = c.cursor()

def coluna_existe(tabela, coluna):
    cur.execute(f"PRAGMA table_info({tabela})")
    return coluna in [x[1] for x in cur.fetchall()]

tabelas = ["vendas", "compras", "perdas", "movimentos_caixa", "facturas"]

for tabela in tabelas:
    print(f"\n[{tabela}]")
    
    if not coluna_existe(tabela, "uuid"):
        cur.execute(f"ALTER TABLE {tabela} ADD COLUMN uuid TEXT")
        print(f"  + uuid adicionado")
    else:
        print(f"  - uuid ja existe")
    
    if not coluna_existe(tabela, "terminal_id"):
        cur.execute(f"ALTER TABLE {tabela} ADD COLUMN terminal_id TEXT")
        print(f"  + terminal_id adicionado")
    else:
        print(f"  - terminal_id ja existe")
    
    if not coluna_existe(tabela, "farmacia_id"):
        cur.execute(f"ALTER TABLE {tabela} ADD COLUMN farmacia_id INTEGER")
        print(f"  + farmacia_id adicionado")
    else:
        print(f"  - farmacia_id ja existe")
    
    if not coluna_existe(tabela, "sincronizado"):
        cur.execute(f"ALTER TABLE {tabela} ADD COLUMN sincronizado INTEGER DEFAULT 0")
        print(f"  + sincronizado adicionado")
    else:
        print(f"  - sincronizado ja existe")

c.commit()
c.close()

print("\n" + "="*60)
print("OK - Colunas da Fase B adicionadas!")
print("="*60)