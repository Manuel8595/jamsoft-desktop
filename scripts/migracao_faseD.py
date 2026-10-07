from database import conectar
c = conectar()
cur = c.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('fila_sincronizacao','log_sincronizacao')")
print('Tabelas FASE D:', [x[0] for x in cur.fetchall()])

cur.execute("PRAGMA table_info(fila_sincronizacao)")
print('Colunas fila:', [x[1] for x in cur.fetchall()])

cur.execute("PRAGMA table_info(log_sincronizacao)")
print('Colunas log:', [x[1] for x in cur.fetchall()])
c.close()