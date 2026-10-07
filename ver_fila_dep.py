import sqlite3

conn = sqlite3.connect("farmacia.db")
cur = conn.cursor()

# Ver o que está na fila relacionado com depósitos
cur.execute("SELECT id, tipo, estado, tentativas FROM fila_sincronizacao WHERE tipo LIKE '%DEP%' LIMIT 20")
resultados = cur.fetchall()

print(f"Total de operacoes DEPOSITO na fila: {len(resultados)}")
print()

for r in resultados:
    print(r)

print()
print("--- Ultimos 5 itens na fila (qualquer tipo) ---")
cur.execute("SELECT id, tipo, estado FROM fila_sincronizacao ORDER BY id DESC LIMIT 5")
for r in cur.fetchall():
    print(r)

conn.close()