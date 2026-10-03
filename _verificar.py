import uuid as uuid_lib
from database import conectar
import os


tabelas = [
    'categorias', 'fornecedores', 'utilizadores', 'itens_factura',
    'inventarios', 'itens_inventario', 'depositos', 'saldo_farmacia',
    'nao_conformidades', 'auditorias_realizadas', 'auditoria', 'itens_compra'
]

terminal = os.environ.get("COMPUTERNAME", "TERM-01")

conn = conectar()
cur = conn.cursor()

print("=" * 50)
print("GERAR UUIDS PARA REGISTOS ANTIGOS")
print("=" * 50)

total_geral = 0

for t in tabelas:
    try:
        # Buscar registos sem uuid
        cur.execute(f"SELECT id FROM {t} WHERE uuid IS NULL")
        ids = [row[0] for row in cur.fetchall()]
        
        if not ids:
            print(f"{t:25} — 0 registos (nada a fazer)")
            continue
        
        # Gerar uuid para cada
        for reg_id in ids:
            novo_uuid = str(uuid_lib.uuid4())
            cur.execute(f"""
                UPDATE {t}
                SET uuid = ?, terminal_id = ?, sincronizado = 0
                WHERE id = ?
            """, (novo_uuid, terminal, reg_id))
        
        total_geral += len(ids)
        print(f"{t:25} — {len(ids)} registos actualizados ✅")
    
    except Exception as e:
        print(f"{t:25} — ERRO: {e}")

conn.commit()
conn.close()

print("=" * 50)
print(f"TOTAL: {total_geral} registos com uuid gerado")
print("=" * 50)